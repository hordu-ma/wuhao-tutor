"""
文件管理服务
提供文件上传、下载、管理等功能的简化实现
"""

import os
import uuid
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.schemas.file import (
    FileInfoResponse,
    FileListQuery,
    FileMetadata,
    FileUploadResponse,
)
from src.utils.file_utils import (
    calculate_file_hash,
    format_file_size,
    generate_safe_filename,
    validate_file_content,
)

settings = get_settings()


class FileService:
    """文件管理服务"""

    def __init__(self):
        self.upload_dir = Path(getattr(settings, "UPLOAD_DIR", "./uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self, db: AsyncSession, file: UploadFile, metadata: FileMetadata
    ) -> FileUploadResponse:
        """
        上传文件

        Args:
            db: 数据库会话
            file: 上传的文件
            metadata: 文件元数据

        Returns:
            FileUploadResponse: 上传结果
        """
        # 读取文件内容
        content = await file.read()

        # 验证文件
        is_valid, error_msg = validate_file_content(
            content, metadata.content_type, metadata.original_filename
        )

        if not is_valid:
            raise ValueError(f"文件验证失败: {error_msg}")

        # 生成文件ID和存储文件名
        file_id = str(uuid.uuid4())
        safe_filename = generate_safe_filename(metadata.original_filename, file_id)

        # 保存文件
        file_path = self.upload_dir / safe_filename
        with open(file_path, "wb") as f:
            f.write(content)

        # 计算文件哈希（用于未来的去重功能）
        _file_hash = calculate_file_hash(content)

        # 返回响应
        from uuid import UUID

        return FileUploadResponse(
            id=UUID(file_id),
            original_filename=metadata.original_filename,
            stored_filename=safe_filename,
            content_type=metadata.content_type,
            size=len(content),
            category=metadata.category or "general",
            description=metadata.description,
            download_url=f"/api/v1/files/{file_id}/download",
            preview_url=(
                f"/api/v1/files/{file_id}/preview"
                if metadata.content_type.startswith("image/")
                else None
            ),
            uploaded_at=datetime.utcnow(),
            success=True,
        )

    async def upload_learning_image(
        self, file: UploadFile, user_id: str
    ) -> Dict[str, Any]:
        """
        专门用于学习问答的图片上传

        Args:
            file: 上传的图片文件
            user_id: 用户ID

        Returns:
            Dict: 包含图片信息和访问URL的字典

        Raises:
            ValueError: 文件验证失败
            Exception: 文件保存失败
        """
        # 验证文件类型 - 只允许图片
        if not file.content_type or not file.content_type.startswith("image/"):
            raise ValueError(f"只支持图片文件，当前类型: {file.content_type}")

        # 允许的图片类型
        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed_types:
            raise ValueError(f"不支持的图片类型，支持: {', '.join(allowed_types)}")

        # 读取文件内容
        content = await file.read()

        # 检查文件大小 (10MB)
        max_size = 10 * 1024 * 1024
        if len(content) > max_size:
            raise ValueError(
                f"文件大小超过限制，最大支持: {format_file_size(max_size)}"
            )

        # 生成文件ID和存储文件名
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        stored_filename = f"learning_{user_id}_{file_id}{file_extension}"

        # 保存文件
        file_path = self.upload_dir / stored_filename
        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"文件保存失败: {str(e)}")

        # 构建完整的访问URL
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        image_url = f"{base_url}/api/v1/files/{file_id}/preview"

        # 返回图片信息
        return {
            "id": file_id,
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "content_type": file.content_type,
            "size": len(content),
            "size_formatted": format_file_size(len(content)),
            "category": "learning_image",
            "image_url": image_url,  # 供AI使用的完整URL
            "preview_url": f"/api/v1/files/{file_id}/preview",
            "uploaded_at": datetime.utcnow().isoformat(),
            "success": True,
        }

    async def get_files(
        self, db: AsyncSession, query: FileListQuery
    ) -> List[FileInfoResponse]:
        """
        获取文件列表

        Args:
            db: 数据库会话
            query: 查询参数

        Returns:
            List[FileInfoResponse]: 文件列表
        """
        # 简化实现：返回空列表
        # 实际实现中应该从数据库查询
        return []

    async def get_file_info(
        self, db: AsyncSession, file_id: str, user_id: str
    ) -> Optional[FileInfoResponse]:
        """
        获取文件信息

        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID

        Returns:
            Optional[FileInfoResponse]: 文件信息
        """
        # 简化实现：返回None
        # 实际实现中应该从数据库查询
        return None

    async def get_file_path(self, db: AsyncSession, file_id: str, user_id: str) -> str:
        """
        获取文件路径

        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID

        Returns:
            str: 文件路径
        """
        # 简化实现：根据文件ID查找
        for file_path in self.upload_dir.iterdir():
            if file_id in file_path.name:
                return str(file_path)

        raise FileNotFoundError(f"文件不存在: {file_id}")

    async def record_download(self, db: AsyncSession, file_id: str):
        """
        记录下载统计

        Args:
            db: 数据库会话
            file_id: 文件ID
        """
        # 简化实现：不做任何操作
        # 实际实现中应该更新数据库中的下载计数
        pass

    async def record_preview(self, db: AsyncSession, file_id: str):
        """
        记录预览统计

        Args:
            db: 数据库会话
            file_id: 文件ID
        """
        # 简化实现：不做任何操作
        # 实际实现中应该更新数据库中的预览计数
        pass

    async def update_file_info(
        self,
        db: AsyncSession,
        file_id: str,
        user_id: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> FileInfoResponse:
        """
        更新文件信息

        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID
            description: 新描述
            category: 新分类

        Returns:
            FileInfoResponse: 更新后的文件信息
        """
        # 简化实现：抛出未找到异常
        # 实际实现中应该更新数据库记录
        raise FileNotFoundError(f"文件不存在: {file_id}")

    async def delete_file(self, db: AsyncSession, file_id: str, user_id: str):
        """
        删除文件

        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID
        """
        # 简化实现：尝试删除物理文件
        try:
            file_path = await self.get_file_path(db, file_id, user_id)
            os.remove(file_path)
        except FileNotFoundError:
            pass

        # 实际实现中还应该删除数据库记录

    async def get_file_stats(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        获取文件统计

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 简化实现：返回基本统计
        total_files = len(list(self.upload_dir.iterdir()))
        total_size = sum(
            f.stat().st_size for f in self.upload_dir.iterdir() if f.is_file()
        )

        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "image_count": 0,
            "document_count": 0,
            "category_stats": {"general": total_files},
            "recent_uploads": 0,
        }

    async def save_file(
        self,
        file_buffer: BytesIO,
        file_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        保存文件（支持 OSS 或本地）

        Args:
            file_buffer: 文件内容
            file_key: 文件路径/Key (e.g. "plans/123.pdf")
            content_type: MIME类型

        Returns:
            文件访问URL
        """
        # 检查是否配置了 OSS
        if settings.OSS_ACCESS_KEY_ID and settings.OSS_ACCESS_KEY_SECRET:
            return await self._save_to_oss(file_buffer, file_key, content_type)
        else:
            return await self._save_to_local(file_buffer, file_key)

    async def _save_to_oss(
        self, file_buffer: BytesIO, file_key: str, content_type: str
    ) -> str:
        import oss2

        auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET
        )
        bucket = oss2.Bucket(
            auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME
        )

        # 确保指针在开始位置
        file_buffer.seek(0)

        # 上传
        bucket.put_object(
            file_key, file_buffer, headers={"Content-Type": content_type}
        )

        # 生成签名URL (有效期1小时)
        url = bucket.sign_url("GET", file_key, 3600)
        return url

    async def _save_to_local(self, file_buffer: BytesIO, file_key: str) -> str:
        # 确保目录存在
        full_path = self.upload_dir / file_key
        full_path.parent.mkdir(parents=True, exist_ok=True)

        file_buffer.seek(0)
        with open(full_path, "wb") as f:
            f.write(file_buffer.read())

        # 返回本地访问URL
        return f"{settings.BASE_URL}/uploads/{file_key}"


# 全局实例
_file_service = None


def get_file_service() -> FileService:
    """获取文件服务实例"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
