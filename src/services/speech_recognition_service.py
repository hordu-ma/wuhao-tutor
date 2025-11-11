"""
阿里云语音识别服务

该模块提供语音转文字功能，基于阿里云智能语音服务
支持：
- 文件语音识别
- 实时语音识别
- 多种音频格式
- 错误处理和重试机制
"""

import asyncio
import base64
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiofiles
import httpx
from fastapi import HTTPException, UploadFile

from src.core.config import get_settings
from src.core.exceptions import ServiceError

logger = logging.getLogger("speech_recognition_service")
settings = get_settings()


class SpeechRecognitionError(ServiceError):
    """语音识别服务异常"""

    pass


class SpeechRecognitionService:
    """阿里云语音识别服务类"""

    def __init__(self):
        self.app_key = settings.ASR_APP_KEY
        self.access_key_id = settings.ASR_ACCESS_KEY_ID
        self.access_key_secret = settings.ASR_ACCESS_KEY_SECRET
        self.endpoint = settings.ASR_ENDPOINT
        self.timeout = 30

        # Token 缓存
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0  # Token 过期时间戳

        if not self.app_key or not self.access_key_id or not self.access_key_secret:
            logger.warning(
                "语音识别服务配置不完整，请检查 ASR_APP_KEY、ASR_ACCESS_KEY_ID 和 ASR_ACCESS_KEY_SECRET"
            )

    async def _get_access_token(self) -> str:
        """
        使用 AccessKey 获取临时 Token

        Token 有效期为 24 小时,自动缓存和刷新

        Returns:
            str: 访问令牌

        Raises:
            SpeechRecognitionError: Token 获取失败
        """
        try:
            # 🔧 [修复] 检查缓存的 Token 是否有效（提前 1 小时刷新，确保不会过期）
            current_time = time.time()
            if self._access_token and current_time < self._token_expire_time:
                logger.debug(
                    f"使用缓存的 Token（剩余有效期: {(self._token_expire_time - current_time) / 3600:.1f} 小时）"
                )
                return self._access_token

            logger.info("Token 即将过期或不存在，正在获取新的阿里云 NLS Token...")

            # 使用阿里云POP API的CreateToken接口
            # 构造请求参数
            import hashlib
            import hmac
            import urllib.parse
            import uuid
            from datetime import datetime

            # 基本参数
            params = {
                "AccessKeyId": self.access_key_id,
                "Action": "CreateToken",
                "Format": "JSON",
                "RegionId": "cn-shanghai",
                "SignatureMethod": "HMAC-SHA1",
                "SignatureNonce": str(uuid.uuid4()),
                "SignatureVersion": "1.0",
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Version": "2019-02-28",
            }

            # 按字典序排序
            sorted_params = sorted(params.items())

            # 构造规范化的请求字符串
            canonicalized_query_string = "&".join(
                [
                    f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
                    for k, v in sorted_params
                ]
            )

            # 构造待签名的字符串
            string_to_sign = (
                f"GET&{urllib.parse.quote('/', safe='')}&"
                f"{urllib.parse.quote(canonicalized_query_string, safe='')}"
            )

            # 计算签名
            if not self.access_key_secret:
                raise SpeechRecognitionError("AccessKey Secret 未配置")

            h = hmac.new(
                (self.access_key_secret + "&").encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha1,
            )
            signature = base64.b64encode(h.digest()).decode("utf-8")

            # 添加签名到参数
            params["Signature"] = signature

            # 构造请求URL
            token_url = f"http://nls-meta.cn-shanghai.aliyuncs.com/?{urllib.parse.urlencode(params)}"

            logger.debug(f"Token请求URL: {token_url}")

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(token_url)

                logger.info(f"Token响应状态码: {response.status_code}")
                logger.debug(f"Token响应内容: {response.text}")

                if response.status_code != 200:
                    logger.error(
                        f"Token 获取失败: {response.status_code}, {response.text}"
                    )
                    raise SpeechRecognitionError(
                        f"Token 获取失败: HTTP {response.status_code}"
                    )

                result = response.json()

                if "Token" not in result or "Id" not in result.get("Token", {}):
                    logger.error(f"Token 响应格式错误: {result}")
                    raise SpeechRecognitionError("Token 响应格式错误")

                # 缓存 Token（有效期 24 小时）
                token_id = result["Token"]["Id"]
                if not token_id or not isinstance(token_id, str):
                    raise SpeechRecognitionError("Token 值无效")

                # Token提前1小时过期,确保有足够的缓冲时间
                self._access_token = token_id
                expire_seconds = result["Token"].get("ExpireTime", 86400)
                self._token_expire_time = (
                    current_time + expire_seconds - 3600
                )  # 提前1小时

                logger.info(
                    f"Token 获取成功，有效期至: "
                    f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._token_expire_time))}"
                )

                return self._access_token

        except httpx.TimeoutException:
            raise SpeechRecognitionError("Token 获取超时")
        except httpx.RequestError as e:
            raise SpeechRecognitionError(f"Token 获取网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"Token 获取异常: {str(e)}", exc_info=True)
            raise SpeechRecognitionError(f"Token 获取失败: {str(e)}")

    async def recognize_from_file(
        self, audio_file: UploadFile, language: str = "zh-CN"
    ) -> Dict[str, Any]:
        """
        从上传的音频文件识别语音转文字

        Args:
            audio_file: 上传的音频文件
            language: 识别语言，默认中文

        Returns:
            Dict: 识别结果
                {
                    "success": bool,
                    "text": str,
                    "confidence": float,
                    "duration": float,
                    "words": List[Dict]  # 可选，详细的词语识别结果
                }

        Raises:
            SpeechRecognitionError: 识别失败时抛出
        """
        try:
            # 验证文件格式
            if not audio_file.filename or not self._is_supported_format(
                audio_file.filename
            ):
                raise SpeechRecognitionError(f"不支持的音频格式: {audio_file.filename}")

            # 检查文件大小
            content = await audio_file.read()
            if (
                len(content) > settings.ASR_MAX_AUDIO_DURATION * 1024 * 1024
            ):  # 简化的大小检查
                raise SpeechRecognitionError("音频文件过大")

            # 重置文件指针
            await audio_file.seek(0)

            # 调用阿里云语音识别API
            result = await self._call_recognition_api(
                content, audio_file.filename or "audio.mp3", language
            )

            return result

        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}", exc_info=True)
            if isinstance(e, SpeechRecognitionError):
                raise
            raise SpeechRecognitionError(f"语音识别处理失败: {str(e)}")

    async def _call_recognition_api(
        self, audio_data: bytes, filename: str, language: str = "zh-CN"
    ) -> Dict[str, Any]:
        """
        调用阿里云语音识别API

        Args:
            audio_data: 音频数据
            filename: 文件名
            language: 识别语言

        Returns:
            Dict: API响应结果
        """
        try:
            # 获取 Access Token
            access_token = await self._get_access_token()

            # 获取音频格式
            audio_format = self._get_format_from_filename(filename)

            # 检查AppKey配置
            if not self.app_key or len(self.app_key) < 10:
                raise SpeechRecognitionError(
                    "AppKey配置错误或为空,请检查ASR_APP_KEY环境变量"
                )

            # 构造URL参数（按照阿里云RESTful API规范）
            params = {
                "appkey": self.app_key,
                "format": audio_format,
                "sample_rate": settings.ASR_SAMPLE_RATE,
                "enable_punctuation_prediction": str(
                    settings.ASR_ENABLE_PUNCTUATION_PREDICTION
                ).lower(),
                "enable_inverse_text_normalization": str(
                    settings.ASR_ENABLE_INVERSE_TEXT_NORMALIZATION
                ).lower(),
            }

            # 构造完整URL
            import urllib.parse

            one_sentence_url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"

            logger.info(f"ASR API请求URL: {one_sentence_url}")
            logger.info(f"音频格式: {audio_format}, 大小: {len(audio_data)} bytes")

            # 构建请求头（按照阿里云RESTful API规范）
            headers = {
                "X-NLS-Token": access_token,  # Token通过X-NLS-Token头传递
                "Content-type": "application/octet-stream",  # 二进制音频流
                "Content-Length": str(len(audio_data)),
            }

            # 发送HTTP请求（请求体为二进制音频数据）
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    one_sentence_url,
                    content=audio_data,
                    headers=headers,  # 使用content而不json
                )

                logger.info(f"ASR API响应状态码: {response.status_code}")
                logger.info(
                    f"ASR API完整响应: {response.text}"
                )  # 临时改为INFO级别以便调试

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(
                        f"ASR API调用失败: {response.status_code}, {error_detail}"
                    )

                    # 解析具体错误信息
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_detail)
                    except (ValueError, KeyError, AttributeError):
                        error_msg = error_detail

                    # 针对不同错误码提供具体提示
                    if response.status_code == 400:
                        raise SpeechRecognitionError(
                            f"语音识别参数错误: {error_msg}。请检查音频格式和采样率配置"
                        )
                    elif response.status_code == 401:
                        raise SpeechRecognitionError(
                            f"Token认证失败: {error_msg}。Token可能已过期,请重新获取"
                        )
                    elif response.status_code == 403:
                        raise SpeechRecognitionError(
                            f"无权访问: {error_msg}。请检查AppKey和AccessKey配置"
                        )
                    else:
                        raise SpeechRecognitionError(
                            f"语音识别API调用失败 ({response.status_code}): {error_msg}"
                        )

                result = response.json()

                # 解析响应
                return self._parse_recognition_response(result, len(audio_data))

        except httpx.TimeoutException:
            raise SpeechRecognitionError("语音识别请求超时")
        except httpx.RequestError as e:
            raise SpeechRecognitionError(f"语音识别网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"语音识别API调用异常: {str(e)}", exc_info=True)
            raise SpeechRecognitionError(f"语音识别处理异常: {str(e)}")

    def _parse_recognition_response(
        self, response: Dict, audio_size: int
    ) -> Dict[str, Any]:
        """
        解析语音识别API响应

        Args:
            response: API响应
            audio_size: 音频文件大小

        Returns:
            Dict: 标准化的识别结果
        """
        try:
            # 阿里云ASR响应格式解析
            if response.get("status") == 20000000:  # 成功状态码
                result_text = response.get("result", "")
                confidence = response.get("confidence", 0.0)

                return {
                    "success": True,
                    "text": result_text,
                    "confidence": confidence,
                    "duration": 0.0,  # 文件识别无法获取准确时长
                    "audio_size": audio_size,
                    "words": [],  # 一句话识别不提供详细词语信息
                    "raw_response": response,
                }
            else:
                error_message = response.get("message", "未知错误")
                logger.error(f"语音识别失败: {error_message}")
                raise SpeechRecognitionError(f"语音识别失败: {error_message}")

        except Exception as e:
            logger.error(f"解析语音识别响应失败: {str(e)}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "duration": 0.0,
                "audio_size": audio_size,
                "error": str(e),
                "raw_response": response,
            }

    def _is_supported_format(self, filename: Optional[str]) -> bool:
        """检查是否为支持的音频格式"""
        if not filename:
            return False

        supported_formats = [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"]
        return any(filename.lower().endswith(fmt) for fmt in supported_formats)

    def _get_format_from_filename(self, filename: str) -> str:
        """从文件名获取音频格式"""
        extension = Path(filename).suffix.lower()
        format_mapping = {
            ".mp3": "mp3",
            ".wav": "wav",
            ".m4a": "aac",
            ".aac": "aac",
            ".flac": "flac",
            ".ogg": "ogg",
        }
        return format_mapping.get(extension, "mp3")

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict: 服务状态信息
        """
        status = {
            "service": "speech_recognition",
            "status": "unknown",
            "config": {
                "app_key_configured": bool(self.app_key),
                "access_key_configured": bool(
                    self.access_key_id and self.access_key_secret
                ),
                "endpoint": self.endpoint,
                "max_audio_duration": settings.ASR_MAX_AUDIO_DURATION,
                "supported_formats": [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"],
            },
        }

        if not settings.ASR_ENABLED:
            status["status"] = "disabled"
            status["message"] = "语音识别服务已禁用"
            return status

        if not self.app_key or not self.access_key_id or not self.access_key_secret:
            status["status"] = "error"
            status["message"] = "语音识别服务配置不完整"
            return status

        try:
            # 简单的连通性检查
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://nls-gateway-cn-shanghai.aliyuncs.com/"
                )
                status["status"] = (
                    "healthy" if response.status_code < 500 else "unhealthy"
                )
                status["message"] = "语音识别服务可用"
        except Exception as e:
            status["status"] = "unhealthy"
            status["message"] = f"语音识别服务连接失败: {str(e)}"

        return status


# 全局服务实例
_speech_recognition_service: Optional[SpeechRecognitionService] = None


def get_speech_recognition_service() -> SpeechRecognitionService:
    """获取语音识别服务实例"""
    global _speech_recognition_service
    if _speech_recognition_service is None:
        _speech_recognition_service = SpeechRecognitionService()
    return _speech_recognition_service
