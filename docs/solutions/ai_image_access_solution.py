"""
方案A: 阿里云OSS公开访问图片URL生成
为AI服务提供无需认证的公开图片访问
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import oss2

from src.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class AIImageService:
    """专门为AI服务提供图片访问的服务"""

    def __init__(self):
        self.bucket_name = settings.OSS_BUCKET_NAME
        self.endpoint = settings.OSS_ENDPOINT
        self.auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET
        )
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

    async def upload_for_ai_analysis(
        self, file_content: bytes, original_filename: str, user_id: str
    ) -> dict:
        """
        上传图片并生成AI可访问的公开URL

        Args:
            file_content: 图片文件内容
            original_filename: 原始文件名
            user_id: 用户ID

        Returns:
            dict: 包含公开URL和文件信息
        """
        # 1. 生成唯一的OSS对象名
        file_ext = (
            original_filename.split(".")[-1] if "." in original_filename else "jpg"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = (
            f"ai_images/{user_id}/{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
        )

        # 2. 上传到OSS（设置为公开读取）
        result = self.bucket.put_object(
            object_name,
            file_content,
            headers={"x-oss-object-acl": "public-read"},  # 关键：设置公开读取
        )

        if result.status != 200:
            raise Exception(f"OSS上传失败: {result.status}")

        # 3. 生成公开访问URL
        public_url = f"https://{self.bucket_name}.{self.endpoint}/{object_name}"

        # 4. 生成带签名的临时URL（备用，有效期24小时）
        signed_url = self.bucket.sign_url("GET", object_name, 24 * 3600)

        return {
            "object_name": object_name,
            "public_url": public_url,  # AI服务使用这个URL
            "signed_url": signed_url,  # 备用URL
            "file_size": len(file_content),
            "upload_time": datetime.now().isoformat(),
        }

    def generate_presigned_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        生成预签名URL（临时访问）

        Args:
            object_name: OSS对象名
            expires_in: 过期时间（秒）

        Returns:
            str: 预签名URL
        """
        return self.bucket.sign_url("GET", object_name, expires_in)

    def set_object_public(self, object_name: str) -> bool:
        """
        将OSS对象设置为公开访问

        Args:
            object_name: OSS对象名

        Returns:
            bool: 是否设置成功
        """
        try:
            result = self.bucket.put_object_acl(
                object_name, oss2.OBJECT_ACL_PUBLIC_READ
            )
            return result.status == 200
        except Exception as e:
            logger.error(f"设置对象公开访问失败: {e}")
            return False


# 使用示例
async def process_user_photo_for_ai(file_content: bytes, filename: str, user_id: str):
    """处理用户拍照的试题图片"""
    ai_image_service = AIImageService()

    # 上传并获取公开URL
    result = await ai_image_service.upload_for_ai_analysis(
        file_content, filename, user_id
    )

    # 这个URL可以直接被阿里云百炼AI访问
    ai_accessible_url = result["public_url"]

    return {"ai_url": ai_accessible_url, "file_info": result}
