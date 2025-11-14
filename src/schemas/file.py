"""
文件管理相关的Schema定义
"""

from typing import Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4


class FileMetadata(BaseModel):
    """文件元数据"""

    original_filename: str = Field(..., description="原始文件名")
    content_type: str = Field(..., description="文件MIME类型")
    size: int = Field(..., ge=0, description="文件大小（字节）")
    category: Optional[str] = Field("general", description="文件分类")
    description: Optional[str] = Field(None, description="文件描述")
    user_id: str = Field(..., description="用户ID")


class FileUploadResponse(BaseModel):
    """文件上传响应"""

    id: UUID4 = Field(..., description="文件ID")
    original_filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储文件名")
    content_type: str = Field(..., description="文件MIME类型")
    size: int = Field(..., description="文件大小")
    category: str = Field(..., description="文件分类")
    description: Optional[str] = Field(None, description="文件描述")
    download_url: str = Field(..., description="下载链接")
    preview_url: Optional[str] = Field(None, description="预览链接")
    uploaded_at: datetime = Field(..., description="上传时间")
    success: bool = Field(True, description="是否成功")


class FileInfoResponse(BaseModel):
    """文件信息响应"""

    id: UUID4 = Field(..., description="文件ID")
    original_filename: str = Field(..., description="原始文件名")
    stored_filename: str = Field(..., description="存储文件名")
    content_type: str = Field(..., description="文件MIME类型")
    size: int = Field(..., description="文件大小")
    category: str = Field(..., description="文件分类")
    description: Optional[str] = Field(None, description="文件描述")
    download_url: str = Field(..., description="下载链接")
    preview_url: Optional[str] = Field(None, description="预览链接")
    uploaded_at: datetime = Field(..., description="上传时间")
    download_count: int = Field(0, ge=0, description="下载次数")
    preview_count: int = Field(0, ge=0, description="预览次数")


class FileListQuery(BaseModel):
    """文件列表查询参数"""

    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    category: Optional[str] = Field(None, description="分类筛选")
    file_type: Optional[str] = Field(None, description="文件类型筛选")
    search: Optional[str] = Field(None, description="搜索关键词")
    user_id: str = Field(..., description="用户ID")

    @validator("file_type")
    def validate_file_type(cls, v):
        if v and v not in ["image", "document"]:
            raise ValueError('file_type must be "image" or "document"')
        return v


class FileListResponse(BaseModel):
    """文件列表响应"""

    success: bool = Field(True, description="是否成功")
    data: List[FileInfoResponse] = Field(..., description="文件列表")
    message: str = Field(..., description="响应消息")
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页数量")


class FileStatsResponse(BaseModel):
    """文件统计响应"""

    total_files: int = Field(..., ge=0, description="总文件数")
    total_size: int = Field(..., ge=0, description="总大小（字节）")
    image_count: int = Field(..., ge=0, description="图片数量")
    document_count: int = Field(..., ge=0, description="文档数量")
    category_stats: Dict[str, int] = Field(..., description="分类统计")
    recent_uploads: int = Field(..., ge=0, description="最近7天上传数")
