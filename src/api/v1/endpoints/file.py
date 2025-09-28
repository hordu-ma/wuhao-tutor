"""
文件上传API端点 - 简化版本
"""

from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.get("/health")
async def file_health():
    """文件模块健康检查"""
    return {"status": "ok", "module": "file"}


@router.get("/")
async def list_files():
    """获取文件列表"""
    return {"success": True, "data": [], "message": "获取文件列表成功"}


@router.post("/upload")
async def upload_file():
    """上传文件"""
    return {"success": True, "data": {"id": "file_123"}, "message": "文件上传成功"}
