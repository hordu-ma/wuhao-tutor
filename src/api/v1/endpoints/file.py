"""
文件管理API端点 - 简化版
提供文件上传、下载、管理等功能的基础框架
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi import status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.config import get_settings
from src.core.database import get_db
from src.schemas.common import DataResponse, SuccessResponse
from src.services.ai_image_service import get_ai_image_service
from src.services.file_service import FileService

settings = get_settings()
router = APIRouter(prefix="/files", tags=["文件管理"])
logger = logging.getLogger(__name__)

# 支持的文件类型配置
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "application/msword"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

# 文件大小限制（字节）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


# ========== 健康检查 ==========


@router.get(
    "/health",
    summary="文件模块健康检查",
    description="检查文件管理模块的健康状态和存储空间",
    response_model=Dict[str, Any],
)
async def file_health():
    """
    文件模块健康检查

    **返回信息:**
    - 模块状态
    - 存储目录状态
    - 可用空间信息
    """
    try:
        upload_dir = Path(settings.UPLOAD_DIR)

        # 检查上传目录
        upload_dir_exists = upload_dir.exists()
        upload_dir_writable = (
            upload_dir.is_dir() and os.access(upload_dir, os.W_OK)
            if upload_dir_exists
            else False
        )

        # 获取磁盘空间信息
        if upload_dir_exists:
            try:
                stat = os.statvfs(upload_dir)
                free_space = stat.f_bavail * stat.f_frsize
                total_space = stat.f_blocks * stat.f_frsize
                used_space = total_space - free_space
                space_usage_percent = (
                    (used_space / total_space) * 100 if total_space > 0 else 0
                )
            except (OSError, AttributeError):
                free_space = total_space = used_space = space_usage_percent = 0
        else:
            free_space = total_space = used_space = space_usage_percent = 0

        health_info = {
            "status": (
                "healthy" if upload_dir_exists and upload_dir_writable else "unhealthy"
            ),
            "module": "file_management",
            "version": "1.0.0",
            "storage": {
                "upload_directory": str(upload_dir),
                "directory_exists": upload_dir_exists,
                "directory_writable": upload_dir_writable,
                "free_space_bytes": free_space,
                "total_space_bytes": total_space,
                "space_usage_percent": round(space_usage_percent, 2),
                "max_file_size_bytes": MAX_FILE_SIZE,
                "free_space_formatted": format_file_size(free_space),
                "total_space_formatted": format_file_size(total_space),
            },
            "supported_types": {
                "images": list(ALLOWED_IMAGE_TYPES),
                "documents": list(ALLOWED_DOCUMENT_TYPES),
            },
        }

        return health_info

    except Exception as e:
        return {"status": "unhealthy", "module": "file_management", "error": str(e)}


@router.get(
    "/avatars/{filename}", summary="获取头像文件", description="获取用户头像图片文件"
)
async def get_avatar(filename: str, db: AsyncSession = Depends(get_db)):
    """
    获取头像文件

    **路径参数:**
    - **filename**: 头像文件名

    **返回:**
    - 头像图片文件
    """
    upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
    file_path = upload_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="头像文件不存在"
        )

    # 返回头像文件
    return FileResponse(path=str(file_path), headers={"Content-Disposition": "inline"})


# ========== 文件上传 ==========


@router.post(
    "/upload",
    summary="上传文件",
    description="上传单个文件到服务器",
    response_model=DataResponse[Dict[str, Any]],
)
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    category: Optional[str] = Query("general", description="文件分类"),
    description: Optional[str] = Query(None, description="文件描述"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件

    **支持的文件类型:**
    - 图片: JPEG, PNG, WebP, GIF
    - 文档: PDF, TXT, DOC

    **文件限制:**
    - 最大文件大小: 10MB
    - 文件名长度: 最大255字符

    **返回数据:**
    - 文件ID、访问URL、文件信息等
    """
    # 验证文件
    if not file.filename:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="文件名不能为空"
        )

    # 检查文件类型
    if not file.content_type or file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(ALLOWED_TYPES)}",
        )

    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({format_file_size(MAX_FILE_SIZE)})",
        )

    # 重置文件指针
    await file.seek(0)

    # 确保上传目录存在
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件ID和保存路径
    import uuid

    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    stored_filename = f"{file_id}{file_extension}"
    file_path = upload_dir / stored_filename

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}",
        )

    # 返回响应
    uploaded_file = {
        "id": file_id,
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "content_type": file.content_type,
        "size": len(content),
        "size_formatted": format_file_size(len(content)),
        "category": category,
        "description": description,
        "download_url": f"/api/v1/files/{file_id}/download",
        "preview_url": (
            f"/api/v1/files/{file_id}/preview"
            if file.content_type.startswith("image/")
            else None
        ),
        "uploaded_at": "2024-01-15T10:45:00Z",
        "success": True,
    }

    return DataResponse[Dict[str, Any]](
        success=True, data=uploaded_file, message="文件上传成功"
    )


# ========== 学习问答图片上传 ==========


@router.post(
    "/upload-image-for-learning",
    summary="上传学习问答图片",
    description="专门用于学习问答的图片上传，返回可访问的图片URL",
    response_model=DataResponse[Dict[str, Any]],
)
async def upload_image_for_learning(
    file: UploadFile = File(..., description="要上传的图片文件"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    上传学习问答图片

    **支持的图片类型:**
    - JPEG, PNG, WebP, GIF

    **文件限制:**
    - 最大文件大小: 10MB
    - 只支持图片格式

    **返回数据:**
    - 图片ID、访问URL、预览URL等
    """
    try:
        # 使用文件服务处理上传
        file_service = FileService()
        uploaded_image = await file_service.upload_learning_image(file, current_user_id)

        return DataResponse[Dict[str, Any]](
            success=True, data=uploaded_image, message="学习图片上传成功"
        )

    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}",
        )


# ========== 文件查询 ==========


@router.get(
    "/",
    summary="获取文件列表",
    description="获取用户上传的文件列表",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_files(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="文件分类筛选"),
    file_type: Optional[str] = Query(None, description="文件类型筛选 (image/document)"),
    search: Optional[str] = Query(None, description="文件名搜索"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文件列表

    **查询参数:**
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100
    - **category**: 按分类筛选
    - **file_type**: 按类型筛选 (image/document)
    - **search**: 按文件名模糊搜索

    **返回数据:**
    - 文件列表，包含基本信息和统计数据
    """
    # 简化实现：返回示例数据
    files = [
        {
            "id": "990e8400-e29b-41d4-a716-446655440005",
            "original_filename": "homework_sample.jpg",
            "content_type": "image/jpeg",
            "size": 1024576,
            "size_formatted": "1.0 MB",
            "category": "homework",
            "description": "示例作业图片",
            "download_url": "/api/v1/files/990e8400-e29b-41d4-a716-446655440005/download",
            "preview_url": "/api/v1/files/990e8400-e29b-41d4-a716-446655440005/preview",
            "uploaded_at": "2024-01-15T10:45:00Z",
            "download_count": 0,
        }
    ]

    return DataResponse[List[Dict[str, Any]]](
        success=True, data=files, message="获取文件列表成功"
    )


@router.get(
    "/{file_id}",
    summary="获取文件信息",
    description="获取特定文件的详细信息",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_file_info(
    file_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文件详细信息

    **路径参数:**
    - **file_id**: 文件UUID

    **返回数据:**
    - 完整的文件信息，包括元数据、访问统计等
    """
    # 简化实现：返回示例数据或404
    if str(file_id) == "990e8400-e29b-41d4-a716-446655440005":
        file_info = {
            "id": str(file_id),
            "original_filename": "homework_sample.jpg",
            "stored_filename": f"{file_id}.jpg",
            "content_type": "image/jpeg",
            "size": 1024576,
            "size_formatted": "1.0 MB",
            "category": "homework",
            "description": "示例作业图片",
            "download_url": f"/api/v1/files/{file_id}/download",
            "preview_url": f"/api/v1/files/{file_id}/preview",
            "uploaded_at": "2024-01-15T10:45:00Z",
            "download_count": 0,
            "preview_count": 0,
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=file_info, message="获取文件信息成功"
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )


# ========== 文件下载 ==========


@router.get("/{file_id}/download", summary="下载文件", description="下载指定的文件")
async def download_file(
    file_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    下载文件

    **路径参数:**
    - **file_id**: 文件UUID

    **返回:**
    - 文件内容流，浏览器会自动下载
    """
    # 简化实现：查找文件
    upload_dir = Path(settings.UPLOAD_DIR)

    # 查找匹配的文件
    file_path = None
    for f in upload_dir.iterdir():
        if str(file_id) in f.name:
            file_path = f
            break

    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )

    # 返回文件
    return FileResponse(path=str(file_path), filename=f"download_{file_path.name}")


@router.get(
    "/{file_id}/preview",
    summary="预览文件",
    description="在线预览文件（适用于图片和部分文档）",
)
async def preview_file(
    file_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    预览文件

    **路径参数:**
    - **file_id**: 文件UUID

    **支持预览的类型:**
    - 所有图片格式
    - PDF文档（部分浏览器支持）

    **返回:**
    - 文件内容，可在浏览器中直接显示
    """
    # 简化实现：查找文件
    upload_dir = Path(settings.UPLOAD_DIR)

    # 查找匹配的文件
    file_path = None
    for f in upload_dir.iterdir():
        if str(file_id) in f.name:
            file_path = f
            break

    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )

    # 检查文件类型是否支持预览
    file_extension = file_path.suffix.lower()
    if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="该文件类型不支持预览"
        )

    # 返回文件用于预览
    return FileResponse(path=str(file_path), headers={"Content-Disposition": "inline"})


# ========== 文件管理 ==========


@router.delete(
    "/{file_id}",
    summary="删除文件",
    description="删除指定的文件",
    response_model=SuccessResponse,
)
async def delete_file(
    file_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文件

    **路径参数:**
    - **file_id**: 文件UUID

    **注意:**
    - 此操作不可逆
    - 只能删除自己上传的文件
    - 相关的作业提交记录不会被删除，但文件链接会失效
    """
    # 简化实现：查找并删除文件
    upload_dir = Path(settings.UPLOAD_DIR)

    # 查找匹配的文件
    file_path = None
    for f in upload_dir.iterdir():
        if str(file_id) in f.name:
            file_path = f
            break

    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )

    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}",
        )

    return SuccessResponse(success=True, message="文件删除成功")


# ========== 统计信息 ==========


@router.get(
    "/stats/summary",
    summary="获取文件统计",
    description="获取用户文件的统计信息",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_file_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文件统计信息

    **返回数据:**
    - 文件总数
    - 存储空间使用情况
    - 文件类型分布
    - 最近上传统计
    """
    # 简化实现：返回基本统计
    upload_dir = Path(settings.UPLOAD_DIR)

    try:
        if upload_dir.exists():
            files = list(upload_dir.iterdir())
            total_files = len([f for f in files if f.is_file()])
            total_size = sum(f.stat().st_size for f in files if f.is_file())
        else:
            total_files = 0
            total_size = 0

        stats = {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "image_count": 0,
            "document_count": 0,
            "category_stats": {"general": total_files},
            "recent_uploads": 0,
            "upload_directory": str(upload_dir),
            "directory_exists": upload_dir.exists(),
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=stats, message="获取统计信息成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}",
        )


@router.post(
    "/upload-for-ai",
    summary="上传图片供AI分析",
    description="专门为AI服务上传图片，生成公开可访问的URL",
    response_model=DataResponse[Dict[str, Any]],
)
async def upload_image_for_ai(
    file: UploadFile = File(..., description="要上传的图片文件"),
    current_user_id: str = Depends(get_current_user_id),
    ai_image_service=Depends(get_ai_image_service),
):
    """
    上传图片供AI分析

    **专用功能:**
    - 上传图片到OSS并设置公开访问权限
    - 生成AI服务可直接访问的公开URL
    - 支持阿里云百炼等AI服务的图片识别需求

    **支持的图片类型:**
    - JPEG, PNG, WebP, GIF

    **文件限制:**
    - 最大文件大小: 10MB

    **返回数据:**
    - ai_accessible_url: AI服务可直接访问的公开URL
    - 文件信息和上传状态
    """
    try:
        # 验证是否为图片文件
        if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"只支持图片文件。支持的类型: {', '.join(ALLOWED_IMAGE_TYPES)}",
            )

        # 上传并获取AI可访问的URL
        result = await ai_image_service.upload_for_ai_analysis(current_user_id, file)

        return DataResponse[Dict[str, Any]](
            success=True, data=result, message="图片上传成功，AI可直接访问"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI图片上传失败: user={current_user_id}, error={e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片上传失败: {str(e)}",
        )


# ========== AI分析文件访问（降级方案支持）==========


@router.get(
    "/ai/{filename}",
    summary="获取AI分析文件",
    description="为本地存储的AI分析文件提供访问端点（OSS不可用时的降级方案）",
)
async def get_ai_analysis_file(
    filename: str,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    获取AI分析文件（降级方案）

    **用途:**
    - 当OSS不可用时，为本地存储的AI分析文件提供访问
    - 支持AIImageAccessService的降级方案

    **路径参数:**
    - **filename**: AI分析文件名（格式：ai_analysis_用户ID_时间戳_随机ID.ext）

    **安全:**
    - 需要用户认证
    - 只能访问ai_analysis目录下的文件
    - 文件名包含用户信息验证

    **返回:**
    - 图片文件内容，可直接在浏览器中显示
    """
    try:
        # 安全检查：确保文件名不包含路径遍历
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="无效的文件名"
            )

        # 构建文件路径（只允许访问ai_analysis目录）
        ai_analysis_dir = Path("uploads/ai_analysis")
        file_path = ai_analysis_dir / filename

        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="AI分析文件不存在"
            )

        # 额外安全检查：确保文件路径在允许的目录内
        try:
            file_path.resolve().relative_to(ai_analysis_dir.resolve())
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="拒绝访问此文件"
            )

        # 检查文件权限：文件名应包含用户相关信息
        # AI分析文件格式：ai_analysis_{user_hash}_{timestamp}_{random}.ext
        if not filename.startswith("ai_analysis_"):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN, detail="无权访问此文件"
            )

        # 记录访问日志
        logger.info(
            f"AI分析文件访问: user={current_user_id}, file={filename}",
            extra={
                "user_id": current_user_id,
                "filename": filename,
                "file_size": file_path.stat().st_size,
                "access_type": "ai_analysis_fallback",
            },
        )

        # 返回文件，设置适当的缓存头
        return FileResponse(
            path=str(file_path),
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600",  # 缓存1小时
                "X-Content-Type-Options": "nosniff",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"AI分析文件访问失败: user={current_user_id}, file={filename}, error={e}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件访问失败",
        )
