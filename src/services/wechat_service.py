"""
微信服务
处理微信登录、用户信息获取等相关功能
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx

from src.core.config import get_settings
from src.core.exceptions import ServiceError, ValidationError

logger = logging.getLogger("wechat_service")
settings = get_settings()


class WeChatService:
    """微信服务类"""

    def __init__(self):
        self.app_id = settings.WECHAT_MINI_PROGRAM_APP_ID
        self.app_secret = settings.WECHAT_MINI_PROGRAM_APP_SECRET
        self.session_key_cache: Dict[str, Dict] = {}  # 临时缓存，生产环境应使用Redis

    async def code2session(self, code: str) -> Dict:
        """
        通过code获取session_key和openid

        Args:
            code: 微信登录临时code

        Returns:
            Dict: 包含session_key, openid, unionid(可选)的字典

        Raises:
            ServiceError: 微信API调用失败
        """
        if not self.app_id or not self.app_secret:
            raise ServiceError("微信小程序配置缺失")

        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()

                if "errcode" in result and result["errcode"] != 0:
                    error_msg = result.get("errmsg", "未知错误")
                    logger.error(
                        f"微信code2session失败: {error_msg} (errcode: {result['errcode']})"
                    )
                    raise ServiceError(f"微信登录失败: {error_msg}")

                # 缓存session_key（生产环境应存储到Redis并设置过期时间）
                openid = result.get("openid")
                if openid and "session_key" in result:
                    self.session_key_cache[openid] = {
                        "session_key": result["session_key"],
                        "expires_at": datetime.now() + timedelta(hours=24),
                    }

                logger.info(f"微信登录成功: openid={openid}")
                return {
                    "openid": result.get("openid"),
                    "session_key": result.get("session_key"),
                    "unionid": result.get("unionid"),  # 只有绑定了开放平台才有
                }

        except httpx.HTTPError as e:
            logger.error(f"调用微信API失败: {str(e)}", exc_info=True)
            raise ServiceError(f"微信服务不可用: {str(e)}")
        except Exception as e:
            logger.error(f"微信登录异常: {str(e)}", exc_info=True)
            raise ServiceError(f"微信登录失败: {str(e)}")

    def get_cached_session_key(self, openid: str) -> Optional[str]:
        """
        获取缓存的session_key

        Args:
            openid: 微信openid

        Returns:
            Optional[str]: session_key或None
        """
        if openid in self.session_key_cache:
            cache_data = self.session_key_cache[openid]
            if cache_data["expires_at"] > datetime.now():
                return cache_data["session_key"]
            else:
                # 过期则删除
                del self.session_key_cache[openid]
        return None

    async def decrypt_user_info(
        self, encrypted_data: str, iv: str, session_key: str
    ) -> Dict:
        """
        解密微信用户敏感数据

        Args:
            encrypted_data: 加密数据
            iv: 加密算法的初始向量
            session_key: 会话密钥

        Returns:
            Dict: 解密后的用户数据

        Note:
            需要安装 pycryptodome: pip install pycryptodome
        """
        try:
            import base64

            from Crypto.Cipher import AES

            session_key_bytes = base64.b64decode(session_key)
            encrypted_data_bytes = base64.b64decode(encrypted_data)
            iv_bytes = base64.b64decode(iv)

            cipher = AES.new(session_key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted = cipher.decrypt(encrypted_data_bytes)

            # 去除padding
            pad = decrypted[-1]
            if isinstance(pad, str):
                pad = ord(pad)
            decrypted = decrypted[:-pad]

            # 解析JSON
            import json

            user_info = json.loads(decrypted.decode("utf-8"))

            return user_info

        except ImportError:
            logger.error("pycryptodome未安装，无法解密微信用户数据")
            raise ServiceError("服务配置错误：缺少加密库")
        except Exception as e:
            logger.error(f"解密微信用户数据失败: {str(e)}", exc_info=True)
            raise ValidationError(f"数据解密失败: {str(e)}")

    async def get_access_token(self) -> str:
        """
        获取小程序全局唯一后台接口调用凭据

        Returns:
            str: access_token

        Note:
            access_token有效期为2小时，应当缓存
        """
        if not self.app_id or not self.app_secret:
            raise ServiceError("微信小程序配置缺失")

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()

                if "errcode" in result and result["errcode"] != 0:
                    error_msg = result.get("errmsg", "未知错误")
                    logger.error(f"获取access_token失败: {error_msg}")
                    raise ServiceError(f"获取微信凭据失败: {error_msg}")

                return result.get("access_token")

        except httpx.HTTPError as e:
            logger.error(f"调用微信API失败: {str(e)}", exc_info=True)
            raise ServiceError(f"微信服务不可用: {str(e)}")


# 全局单例
_wechat_service: Optional[WeChatService] = None


def get_wechat_service() -> WeChatService:
    """获取微信服务实例"""
    global _wechat_service
    if _wechat_service is None:
        _wechat_service = WeChatService()
    return _wechat_service
