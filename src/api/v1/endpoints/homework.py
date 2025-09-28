"""
作业批改API端点 - 测试版本
"""

from fastapi import APIRouter

router = APIRouter(prefix="/homework", tags=["作业批改"])


@router.get("/health")
async def homework_health():
    """作业模块健康检查"""
    return {"status": "ok", "module": "homework"}


@router.get("/templates")
async def get_templates():
    """获取作业模板列表"""
    return {"success": True, "data": [], "message": "获取成功"}


@router.post("/templates")
async def create_template():
    """创建作业模板"""
    return {"success": True, "data": {"id": "test"}, "message": "创建成功"}
