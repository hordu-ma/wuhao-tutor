"""
AI图片访问服务 - 专门为AI服务提供可访问的图片URL
解决阿里云百炼AI要求公网可访问图片URL的问题
"""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import oss2
from fastapi import UploadFile

from src.core.config import get_settings
from src.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class AIImageAccessService:
    """AI图片访问服务"""

    def __init__(self):
        """初始化AI图片访问服务"""
        self.bucket_name = settings.OSS_BUCKET_NAME
        self.endpoint = settings.OSS_ENDPOINT

        # 初始化OSS客户端
        if all(
            [
                settings.OSS_ACCESS_KEY_ID,
                settings.OSS_ACCESS_KEY_SECRET,
                self.bucket_name,
            ]
        ):
            try:
                auth = oss2.Auth(
                    settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET
                )
                self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
                self.is_oss_available = True
                logger.info(f"AI图片访问服务初始化成功: {self.bucket_name}")
            except Exception as e:
                logger.error(f"OSS初始化失败: {e}")
                self.bucket = None
                self.is_oss_available = False
        else:
            logger.warning("OSS配置不完整，AI图片访问服务将使用降级方案")
            self.bucket = None
            self.is_oss_available = False

    def _generate_ai_object_name(self, user_id: str, original_filename: str) -> str:
        """
        生成AI分析专用的OSS对象名

        Args:
            user_id: 用户ID
            original_filename: 原始文件名

        Returns:
            str: OSS对象名
        """
        # 获取文件扩展名
        file_ext = Path(original_filename).suffix if original_filename else ".jpg"

        # 生成时间戳和随机ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:12]  # 12位随机字符
        user_hash = user_id[:8] if len(user_id) >= 8 else user_id  # 用户ID前8位

        # 构建对象名：ai_analysis/{user_hash}/{timestamp}_{random_id}.{ext}
        object_name = f"ai_analysis/{user_hash}/{timestamp}_{random_id}{file_ext}"

        return object_name

    async def upload_for_ai_analysis(
        self, user_id: str, file: UploadFile
    ) -> Dict[str, Any]:
        """
        上传图片供AI分析，生成公开可访问的URL

        Args:
            user_id: 用户ID
            file: 上传的文件

        Returns:
            Dict: 包含AI可访问URL的信息
        """
        try:
            # 读取文件内容
            content = await file.read()

            # 验证图片文件
            self._validate_image_file(file, content)

            # 生成OSS对象名
            object_name = self._generate_ai_object_name(
                user_id, file.filename or "image.jpg"
            )

            if self.is_oss_available and self.bucket:
                # 上传到OSS并设置公开读取权限
                result = self.bucket.put_object(
                    object_name,
                    content,
                    headers={
                        "x-oss-object-acl": "public-read",  # 设置公开读取
                        "Content-Type": file.content_type or "image/jpeg",
                        "Cache-Control": "max-age=86400",  # 缓存24小时
                    },
                )

                if result.status == 200:
                    # 生成公开访问URL
                    public_url = (
                        f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
                    )

                    logger.info(
                        f"AI图片上传成功: user={user_id}, object={object_name}, size={len(content)}"
                    )

                    return {
                        "ai_accessible_url": public_url,  # AI服务使用这个URL
                        "object_name": object_name,
                        "file_size": len(content),
                        "content_type": file.content_type,
                        "upload_time": datetime.now().isoformat(),
                        "storage_type": "oss_public",
                    }
                else:
                    raise AIServiceError(f"OSS上传失败: status={result.status}")
            else:
                # 降级方案：使用本地存储（开发环境）
                return await self._upload_to_local_for_ai(user_id, file, content)

        except Exception as e:
            logger.error(f"AI图片上传失败: user={user_id}, error={e}")
            raise AIServiceError(f"图片上传失败: {str(e)}")

    def _validate_image_file(self, file: UploadFile, content: bytes) -> None:
        """
        验证图片文件

        Args:
            file: 上传文件
            content: 文件内容
        """
        # 检查文件大小（最大10MB）
        max_size = 10 * 1024 * 1024
        if len(content) > max_size:
            raise AIServiceError(f"图片文件过大，最大支持10MB")

        # 检查文件类型
        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed_types:
            raise AIServiceError(f"不支持的图片格式，支持: {', '.join(allowed_types)}")

        # 检查文件内容（简单验证）
        if len(content) < 100:  # 至少100字节
            raise AIServiceError("图片文件内容异常")

    async def _upload_to_local_for_ai(
        self, user_id: str, file: UploadFile, content: bytes
    ) -> Dict[str, Any]:
        """
        降级方案：本地存储（开发环境使用）

        Args:
            user_id: 用户ID
            file: 上传文件
            content: 文件内容

        Returns:
            Dict: 文件信息（注意：本地存储的URL AI无法直接访问）
        """
        # 生成本地文件名
        object_name = self._generate_ai_object_name(
            user_id, file.filename or "image.jpg"
        )
        local_dir = Path("uploads/ai_analysis")
        local_dir.mkdir(parents=True, exist_ok=True)

        # 保存到本地
        local_file_path = local_dir / object_name.replace("/", "_")
        with open(local_file_path, "wb") as f:
            f.write(content)

        # 构建本地URL（注意：这个URL需要额外处理才能被AI访问）
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        local_url = f"{base_url}/api/v1/files/ai/{object_name.replace('/', '_')}"

        logger.warning(f"使用本地存储，AI可能无法直接访问: {local_url}")

        return {
            "ai_accessible_url": local_url,  # 需要额外处理
            "object_name": object_name,
            "file_size": len(content),
            "content_type": file.content_type,
            "upload_time": datetime.now().isoformat(),
            "storage_type": "local",
            "warning": "本地存储，需要配置公网访问",
        }

    def generate_signed_url(
        self, object_name: str, expires_in: int = 14400
    ) -> Optional[str]:
        """
        生成预签名URL（备用方案）

        Args:
            object_name: OSS对象名
            expires_in: 过期时间（秒），默认4小时

        Returns:
            Optional[str]: 预签名URL
        """
        if not self.is_oss_available or not self.bucket:
            return None

        try:
            signed_url = self.bucket.sign_url("GET", object_name, expires_in)
            logger.info(f"生成预签名URL: {object_name}, expires_in={expires_in}")
            return signed_url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {e}")
            return None

    async def cleanup_expired_images(self, hours_old: int = 24) -> int:
        """
        清理过期的AI分析图片

        Args:
            hours_old: 超过多少小时的图片被认为过期

        Returns:
            int: 清理的文件数量
        """
        if not self.is_oss_available or not self.bucket:
            logger.warning("OSS不可用，无法清理过期图片")
            return 0

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            deleted_count = 0

            # 列出ai_analysis目录下的所有对象
            for obj in oss2.ObjectIterator(self.bucket, prefix="ai_analysis/"):
                if obj.last_modified.replace(tzinfo=None) < cutoff_time:
                    try:
                        self.bucket.delete_object(obj.key)
                        deleted_count += 1
                        logger.debug(f"删除过期AI图片: {obj.key}")
                    except Exception as e:
                        logger.error(f"删除文件失败: {obj.key}, error={e}")

            logger.info(f"清理过期AI图片完成: 删除了{deleted_count}个文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理过期图片失败: {e}")
            return 0


# 全局实例
ai_image_service = AIImageAccessService()


async def get_ai_image_service() -> AIImageAccessService:
    """获取AI图片访问服务实例"""
    return ai_image_service
