"""
阿里云OCR图片文字识别服务
使用阿里云通用OCR API进行图片文字识别
"""

import base64
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import hashlib
import hmac
import time
import urllib.parse

import httpx
import cv2
import numpy as np
from PIL import Image

from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import AIServiceError

logger = get_logger(__name__)


class OCRType:
    """OCR识别类型常量"""
    GENERAL = "general"           # 通用文字识别
    HANDWRITTEN = "handwritten"  # 手写文字识别
    TABLE = "table"              # 表格识别
    FORMULA = "formula"          # 公式识别


class OCRResult:
    """OCR识别结果"""

    def __init__(
        self,
        text: str,
        confidence: float,
        word_info: List[Dict[str, Any]],
        raw_response: Dict[str, Any],
        processing_time: float
    ):
        self.text = text
        self.confidence = confidence
        self.word_info = word_info
        self.raw_response = raw_response
        self.processing_time = processing_time
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "word_count": len(self.word_info),
            "word_info": self.word_info,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "raw_response": self.raw_response
        }


class AliCloudOCRService:
    """
    阿里云OCR服务
    使用HTTP API调用阿里云通用OCR服务
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        region: str = "cn-hangzhou"
    ):
        """
        初始化阿里云OCR服务

        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            region: 地域
        """
        self.access_key_id = access_key_id or settings.ALICLOUD_ACCESS_KEY_ID
        self.access_key_secret = access_key_secret or settings.ALICLOUD_ACCESS_KEY_SECRET
        self.region = region
        self.endpoint = f"https://ocr.{region}.aliyuncs.com"

        if not self.access_key_id or not self.access_key_secret:
            logger.warning("阿里云OCR服务未配置完整的访问凭证，将无法使用OCR功能")

    def _generate_signature(self, params: Dict[str, str], method: str = "POST") -> str:
        """
        生成API签名

        Args:
            params: 请求参数
            method: HTTP方法

        Returns:
            签名字符串
        """
        # 对参数进行排序
        sorted_params = sorted(params.items())

        # 构造签名字符串
        query_string = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params])
        string_to_sign = f"{method}&%2F&{urllib.parse.quote_plus(query_string)}"

        # 计算签名
        if not self.access_key_secret:
            raise AIServiceError("AccessKey Secret未配置")

        signature = base64.b64encode(
            hmac.new(
                (self.access_key_secret + "&").encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')

        return signature

    def _preprocess_image(
        self,
        image_path: str,
        enhance: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        图像预处理

        Args:
            image_path: 图片路径
            enhance: 是否进行图像增强

        Returns:
            base64编码的图片数据和图片信息
        """
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图片: {image_path}")

            # 获取原始图片信息
            height, width = image.shape[:2]
            original_size = Path(image_path).stat().st_size

            # 图像增强处理
            if enhance:
                # 转为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image

                # 降噪
                gray = cv2.medianBlur(gray, 3)

                # 自适应直方图均衡化
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

                # 锐化
                kernel = np.array([[-1, -1, -1],
                                 [-1, 9, -1],
                                 [-1, -1, -1]])
                gray = cv2.filter2D(gray, -1, kernel)

                # 转回BGR格式
                image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # 图片尺寸优化（如果太大就压缩）
            max_size = 2048
            if max(width, height) > max_size:
                scale = max_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.debug(f"图片已压缩: {width}x{height} -> {new_width}x{new_height}")

            # 转换为base64
            _, encoded_image = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            base64_image = base64.b64encode(encoded_image).decode('utf-8')

            # 图片信息
            image_info = {
                "original_width": width,
                "original_height": height,
                "processed_width": image.shape[1],
                "processed_height": image.shape[0],
                "original_size": original_size,
                "processed_size": len(base64_image),
                "enhanced": enhance
            }

            logger.debug(f"图片预处理完成: {image_info}")
            return base64_image, image_info

        except Exception as e:
            logger.error(f"图片预处理失败: {e}")
            raise AIServiceError(f"图片预处理失败: {e}")

    async def _call_ocr_api(
        self,
        action: str,
        image_data: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用OCR API

        Args:
            action: API动作
            image_data: base64编码的图片数据
            additional_params: 额外参数

        Returns:
            API响应
        """
        try:
            # 构造请求参数
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            nonce = str(int(time.time() * 1000))

            params = {
                'Action': action,
                'Version': '2019-12-30',
                'AccessKeyId': self.access_key_id,
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureVersion': '1.0',
                'SignatureNonce': nonce,
                'Timestamp': timestamp,
                'Format': 'JSON',
                'RegionId': self.region,
            }

            # 添加额外参数
            if additional_params:
                params.update(additional_params)

            # 生成签名
            signature = self._generate_signature(params)
            params['Signature'] = signature

            # 准备请求体
            request_body = {
                'ImageType': 1,  # base64格式
                'ImageData': image_data
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.endpoint,
                    params=params,
                    json=request_body,
                    headers={
                        'Content-Type': 'application/json; charset=utf-8',
                        'User-Agent': f'wuhao-tutor/{settings.VERSION}'
                    }
                )

                response.raise_for_status()
                result = response.json()

                if 'Code' in result and result['Code'] != 'Success':
                    error_msg = result.get('Message', '未知错误')
                    raise AIServiceError(f"OCR API调用失败: {error_msg}")

                return result

        except httpx.HTTPError as e:
            logger.error(f"OCR API HTTP请求失败: {e}")
            raise AIServiceError(f"OCR服务请求失败: {e}")
        except Exception as e:
            logger.error(f"OCR API调用失败: {e}")
            raise AIServiceError(f"OCR服务调用失败: {e}")

    async def recognize_general_text(
        self,
        image_path: str,
        enhance: bool = True
    ) -> OCRResult:
        """
        通用文字识别

        Args:
            image_path: 图片路径
            enhance: 是否进行图像增强

        Returns:
            OCR识别结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            if not self.access_key_id or not self.access_key_secret:
                raise AIServiceError("OCR服务未配置完整的访问凭证")

            # 图像预处理
            base64_image, image_info = self._preprocess_image(image_path, enhance)

            # 调用OCR API
            response = await self._call_ocr_api(
                action="RecognizeGeneral",
                image_data=base64_image
            )

            # 处理响应
            text_lines = []
            word_info = []
            total_confidence = 0.0
            word_count = 0

            # 解析识别结果
            if 'Data' in response and 'Content' in response['Data']:
                for item in response['Data']['Content']:
                    text = item.get('Text', '')
                    confidence = float(item.get('Confidence', 0)) / 100.0  # 转换为0-1范围

                    if text.strip():
                        text_lines.append(text)
                        word_info.append({
                            "text": text,
                            "confidence": confidence,
                            "positions": {
                                "left": item.get('Left', 0),
                                "top": item.get('Top', 0),
                                "width": item.get('Width', 0),
                                "height": item.get('Height', 0)
                            }
                        })

                        total_confidence += confidence
                        word_count += 1

            # 合并文本
            full_text = "\n".join(text_lines)
            average_confidence = total_confidence / word_count if word_count > 0 else 0.0

            processing_time = asyncio.get_event_loop().time() - start_time

            logger.info(f"通用OCR识别完成: {word_count}个文本块, 平均置信度: {average_confidence:.2f}")

            return OCRResult(
                text=full_text,
                confidence=average_confidence,
                word_info=word_info,
                raw_response=response,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"通用OCR识别失败: {e}, 处理时间: {processing_time:.2f}s")
            raise

    async def recognize_handwritten_text(
        self,
        image_path: str,
        enhance: bool = True
    ) -> OCRResult:
        """
        手写文字识别

        Args:
            image_path: 图片路径
            enhance: 是否进行图像增强

        Returns:
            OCR识别结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            if not self.access_key_id or not self.access_key_secret:
                raise AIServiceError("OCR服务未配置完整的访问凭证")

            # 图像预处理
            base64_image, image_info = self._preprocess_image(image_path, enhance)

            # 调用OCR API
            response = await self._call_ocr_api(
                action="RecognizeHandwriting",
                image_data=base64_image
            )

            # 处理响应（与通用识别类似）
            text_lines = []
            word_info = []
            total_confidence = 0.0
            word_count = 0

            if 'Data' in response and 'Content' in response['Data']:
                for item in response['Data']['Content']:
                    text = item.get('Text', '')
                    confidence = float(item.get('Confidence', 0)) / 100.0

                    if text.strip():
                        text_lines.append(text)
                        word_info.append({
                            "text": text,
                            "confidence": confidence,
                            "positions": {
                                "left": item.get('Left', 0),
                                "top": item.get('Top', 0),
                                "width": item.get('Width', 0),
                                "height": item.get('Height', 0)
                            }
                        })

                        total_confidence += confidence
                        word_count += 1

            full_text = "\n".join(text_lines)
            average_confidence = total_confidence / word_count if word_count > 0 else 0.0

            processing_time = asyncio.get_event_loop().time() - start_time

            logger.info(f"手写OCR识别完成: {word_count}个文本块, 平均置信度: {average_confidence:.2f}")

            return OCRResult(
                text=full_text,
                confidence=average_confidence,
                word_info=word_info,
                raw_response=response,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"手写OCR识别失败: {e}, 处理时间: {processing_time:.2f}s")
            raise

    async def auto_recognize(
        self,
        image_path: str,
        ocr_type: str = OCRType.GENERAL,
        enhance: bool = True
    ) -> OCRResult:
        """
        自动识别（根据类型选择合适的OCR方法）

        Args:
            image_path: 图片路径
            ocr_type: OCR类型
            enhance: 是否进行图像增强

        Returns:
            OCR识别结果
        """
        try:
            if ocr_type == OCRType.HANDWRITTEN:
                return await self.recognize_handwritten_text(image_path, enhance)
            else:
                # 默认使用通用识别
                return await self.recognize_general_text(image_path, enhance)

        except Exception as e:
            logger.error(f"自动OCR识别失败: {e}")
            raise

    def validate_image(self, image_path: str) -> bool:
        """
        验证图片是否有效

        Args:
            image_path: 图片路径

        Returns:
            是否有效
        """
        try:
            # 检查文件是否存在
            if not Path(image_path).exists():
                return False

            # 检查文件大小
            file_size = Path(image_path).stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"图片文件过大: {file_size / 1024 / 1024:.1f}MB")
                return False

            # 尝试打开图片
            image = cv2.imread(image_path)
            if image is None:
                return False

            # 检查图片尺寸
            height, width = image.shape[:2]
            if width < 10 or height < 10:
                return False

            return True

        except Exception as e:
            logger.error(f"图片验证失败: {e}")
            return False

    def is_service_available(self) -> bool:
        """
        检查OCR服务是否可用

        Returns:
            是否可用
        """
        return bool(self.access_key_id and self.access_key_secret)


# 全局OCR服务实例
_ocr_service_instance: Optional[AliCloudOCRService] = None


def get_ocr_service() -> AliCloudOCRService:
    """
    获取OCR服务实例

    Returns:
        OCR服务实例
    """
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = AliCloudOCRService()
    return _ocr_service_instance


# 便捷导出
ocr_service = get_ocr_service()
