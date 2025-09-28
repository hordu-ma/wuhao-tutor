"""
文件上传处理和阿里云OSS集成服务
支持本地存储和阿里云OSS云存储
"""

import os
import hashlib
import mimetypes
from typing import List, Optional, Tuple, Dict, Any, BinaryIO
from datetime import datetime
from pathlib import Path
import aiofiles
import uuid

import oss2
from PIL import Image
from fastapi import UploadFile

from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import AIServiceError

logger = get_logger(__name__)


class FileType:
    """文件类型常量"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class UploadConfig:
    """上传配置"""

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {
        FileType.IMAGE: {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'},
        FileType.DOCUMENT: {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
        FileType.VIDEO: {'.mp4', '.avi', '.mov', '.wmv', '.flv'},
        FileType.AUDIO: {'.mp3', '.wav', '.ogg', '.m4a'},
    }

    # 文件大小限制 (bytes)
    MAX_FILE_SIZES = {
        FileType.IMAGE: 10 * 1024 * 1024,      # 10MB
        FileType.DOCUMENT: 50 * 1024 * 1024,   # 50MB
        FileType.VIDEO: 100 * 1024 * 1024,     # 100MB
        FileType.AUDIO: 20 * 1024 * 1024,      # 20MB
        FileType.OTHER: 10 * 1024 * 1024,      # 10MB
    }

    # MIME类型映射
    MIME_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
    }


class FileInfo:
    """文件信息"""

    def __init__(
        self,
        filename: str,
        file_path: str,
        file_url: Optional[str] = None,
        file_size: int = 0,
        mime_type: str = "",
        file_hash: str = "",
        storage_type: str = "local",
        width: Optional[int] = None,
        height: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.filename = filename
        self.file_path = file_path
        self.file_url = file_url
        self.file_size = file_size
        self.mime_type = mime_type
        self.file_hash = file_hash
        self.storage_type = storage_type
        self.width = width
        self.height = height
        self.metadata = metadata or {}
        self.upload_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "filename": self.filename,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_hash": self.file_hash,
            "storage_type": self.storage_type,
            "width": self.width,
            "height": self.height,
            "metadata": self.metadata,
            "upload_time": self.upload_time.isoformat()
        }


class AliCloudOSSStorage:
    """阿里云OSS存储服务"""

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """
        初始化OSS存储服务

        Args:
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
            bucket_name: 存储桶名称
            endpoint: OSS端点
        """
        self.access_key_id = access_key_id or settings.OSS_ACCESS_KEY_ID
        self.access_key_secret = access_key_secret or settings.OSS_ACCESS_KEY_SECRET
        self.bucket_name = bucket_name or settings.OSS_BUCKET_NAME
        self.endpoint = endpoint or settings.OSS_ENDPOINT

        self.auth = None
        self.bucket = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化OSS客户端"""
        try:
            if not all([self.access_key_id, self.access_key_secret, self.bucket_name]):
                logger.warning("OSS配置不完整，将使用本地存储")
                return

            # 创建认证对象
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)

            # 创建Bucket对象
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

            logger.info(f"阿里云OSS客户端初始化成功: {self.bucket_name}")

        except Exception as e:
            logger.error(f"阿里云OSS客户端初始化失败: {e}")
            self.bucket = None

    def is_available(self) -> bool:
        """检查OSS服务是否可用"""
        return self.bucket is not None

    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        上传文件到OSS

        Args:
            file_data: 文件数据
            object_name: 对象名称
            content_type: 内容类型

        Returns:
            文件URL
        """
        try:
            if not self.is_available():
                raise AIServiceError("OSS服务不可用")

            # 设置元数据
            headers = {}
            if content_type:
                headers['Content-Type'] = content_type

            # 上传文件
            if self.bucket is not None:
                result = self.bucket.put_object(
                    object_name,
                    file_data,
                    headers=headers
                )
            else:
                raise AIServiceError("OSS客户端未初始化")

            if result.status == 200:
                # 生成文件URL
                file_url = f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
                logger.info(f"文件上传到OSS成功: {object_name}")
                return file_url
            else:
                raise AIServiceError(f"OSS上传失败: {result.status}")

        except Exception as e:
            logger.error(f"OSS文件上传失败: {e}")
            raise AIServiceError(f"文件上传失败: {e}")

    async def delete_file(self, object_name: str) -> bool:
        """
        从OSS删除文件

        Args:
            object_name: 对象名称

        Returns:
            是否删除成功
        """
        try:
            if not self.is_available():
                return False

            if self.bucket is not None:
                result = self.bucket.delete_object(object_name)
                logger.info(f"从OSS删除文件: {object_name}")
                return result.status == 204
            else:
                return False

        except Exception as e:
            logger.error(f"OSS文件删除失败: {e}")
            return False


class FileUploadService:
    """文件上传服务"""

    def __init__(
        self,
        base_upload_dir: str = "uploads",
        use_oss: bool = True
    ):
        """
        初始化文件上传服务

        Args:
            base_upload_dir: 基础上传目录
            use_oss: 是否使用OSS
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

        self.use_oss = use_oss
        self.oss_storage = AliCloudOSSStorage() if use_oss else None

        if use_oss and self.oss_storage and not self.oss_storage.is_available():
            logger.warning("OSS不可用，将使用本地存储")
            self.use_oss = False

    def _get_file_type(self, filename: str) -> str:
        """
        获取文件类型

        Args:
            filename: 文件名

        Returns:
            文件类型
        """
        ext = Path(filename).suffix.lower()

        for file_type, extensions in UploadConfig.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type

        return FileType.OTHER

    def _validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        验证文件

        Args:
            filename: 文件名
            file_size: 文件大小

        Returns:
            (是否有效, 错误消息)
        """
        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if not ext:
            return False, "文件没有扩展名"

        # 检查是否为允许的类型
        file_type = self._get_file_type(filename)
        if file_type == FileType.OTHER:
            all_allowed = set()
            for extensions in UploadConfig.ALLOWED_EXTENSIONS.values():
                all_allowed.update(extensions)
            if ext not in all_allowed:
                return False, f"不支持的文件类型: {ext}"

        # 检查文件大小
        max_size = UploadConfig.MAX_FILE_SIZES.get(file_type, UploadConfig.MAX_FILE_SIZES[FileType.OTHER])
        if file_size > max_size:
            max_size_mb = max_size / 1024 / 1024
            return False, f"文件大小超出限制: {max_size_mb}MB"

        return True, ""

    def _calculate_file_hash(self, file_data: bytes) -> str:
        """
        计算文件哈希

        Args:
            file_data: 文件数据

        Returns:
            文件哈希值
        """
        return hashlib.md5(file_data).hexdigest()

    def _get_image_info(self, file_data: bytes) -> Tuple[Optional[int], Optional[int]]:
        """
        获取图片信息

        Args:
            file_data: 图片数据

        Returns:
            (宽度, 高度)
        """
        try:
            from io import BytesIO
            image = Image.open(BytesIO(file_data))
            return image.size
        except Exception as e:
            logger.debug(f"获取图片信息失败: {e}")
            return None, None

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        生成唯一文件名

        Args:
            original_filename: 原始文件名

        Returns:
            唯一文件名
        """
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        return f"{timestamp}_{unique_id}{ext}"

    def _get_storage_path(self, filename: str, file_type: str) -> str:
        """
        获取存储路径

        Args:
            filename: 文件名
            file_type: 文件类型

        Returns:
            存储路径
        """
        today = datetime.now().strftime("%Y/%m/%d")
        return f"{file_type}/{today}/{filename}"

    async def save_upload_file(
        self,
        upload_file: UploadFile,
        subfolder: str = "general"
    ) -> FileInfo:
        """
        保存上传文件

        Args:
            upload_file: FastAPI上传文件对象
            subfolder: 子文件夹

        Returns:
            文件信息
        """
        try:
            # 读取文件数据
            file_data = await upload_file.read()

            # 检查文件名
            if not upload_file.filename:
                raise AIServiceError("文件名不能为空")

            # 验证文件
            is_valid, error_msg = self._validate_file(upload_file.filename, len(file_data))
            if not is_valid:
                raise AIServiceError(error_msg)

            # 生成唯一文件名
            unique_filename = self._generate_unique_filename(upload_file.filename)
            file_type = self._get_file_type(upload_file.filename)

            # 生成存储路径
            storage_path = f"{subfolder}/{self._get_storage_path(unique_filename, file_type)}"

            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_data)

            # 获取MIME类型
            file_suffix = Path(upload_file.filename).suffix.lower() if upload_file.filename else ""
            mime_type = upload_file.content_type or UploadConfig.MIME_TYPES.get(
                file_suffix,
                'application/octet-stream'
            )

            # 获取图片尺寸（如果是图片）
            width, height = None, None
            if file_type == FileType.IMAGE:
                width, height = self._get_image_info(file_data)

            # 选择存储方式
            if self.use_oss and self.oss_storage and self.oss_storage.is_available():
                # 上传到OSS
                file_url = await self.oss_storage.upload_file(
                    file_data,
                    storage_path,
                    mime_type
                )

                file_info = FileInfo(
                    filename=upload_file.filename,
                    file_path=storage_path,
                    file_url=file_url,
                    file_size=len(file_data),
                    mime_type=mime_type,
                    file_hash=file_hash,
                    storage_type="oss",
                    width=width,
                    height=height,
                    metadata={
                        "original_filename": upload_file.filename,
                        "unique_filename": unique_filename,
                        "file_type": file_type
                    }
                )

            else:
                # 保存到本地
                local_file_path = self.base_upload_dir / storage_path
                local_file_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(local_file_path, 'wb') as f:
                    await f.write(file_data)

                file_info = FileInfo(
                    filename=upload_file.filename or "unknown",
                    file_path=str(local_file_path),
                    file_url=f"/uploads/{storage_path}",  # 相对URL
                    file_size=len(file_data),
                    mime_type=mime_type,
                    file_hash=file_hash,
                    storage_type="local",
                    width=width,
                    height=height,
                    metadata={
                        "original_filename": upload_file.filename,
                        "unique_filename": unique_filename,
                        "file_type": file_type
                    }
                )

            logger.info(f"文件上传成功: {upload_file.filename} -> {storage_path}")
            return file_info

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise AIServiceError(f"文件上传失败: {e}")
        finally:
            # 确保文件句柄被关闭
            await upload_file.seek(0)

    async def save_multiple_files(
        self,
        upload_files: List[UploadFile],
        subfolder: str = "general"
    ) -> List[FileInfo]:
        """
        批量保存上传文件

        Args:
            upload_files: 上传文件列表
            subfolder: 子文件夹

        Returns:
            文件信息列表
        """
        file_infos = []

        for upload_file in upload_files:
            try:
                file_info = await self.save_upload_file(upload_file, subfolder)
                file_infos.append(file_info)
            except Exception as e:
                logger.error(f"批量上传中文件失败: {upload_file.filename}, 错误: {e}")
                # 继续处理其他文件，但记录错误
                continue

        return file_infos

    async def delete_file(self, file_info: FileInfo) -> bool:
        """
        删除文件

        Args:
            file_info: 文件信息

        Returns:
            是否删除成功
        """
        try:
            if file_info.storage_type == "oss":
                # 从OSS删除
                if self.oss_storage:
                    return await self.oss_storage.delete_file(file_info.file_path)
            else:
                # 从本地删除
                local_path = Path(file_info.file_path)
                if local_path.exists():
                    local_path.unlink()
                    logger.info(f"本地文件删除成功: {file_info.file_path}")
                    return True

            return False

        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False


# 全局文件上传服务实例
_file_upload_service_instance: Optional[FileUploadService] = None


def get_file_upload_service() -> FileUploadService:
    """
    获取文件上传服务实例

    Returns:
        文件上传服务实例
    """
    global _file_upload_service_instance
    if _file_upload_service_instance is None:
        _file_upload_service_instance = FileUploadService()
    return _file_upload_service_instance


# 便捷导出
file_upload_service = get_file_upload_service()
