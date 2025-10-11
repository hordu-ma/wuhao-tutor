"""
API v1 路由集合
整合所有v1版本的API端点
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    analytics,
    auth,
    error_book,
    file,
    health,
    homework,
    homework_compatibility,
    learning,
    user,
)

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

api_router.include_router(user.router, prefix="/user", tags=["用户管理"])

api_router.include_router(learning.router, prefix="/learning", tags=["学习问答"])

# 错题本路由
api_router.include_router(error_book.router, tags=["错题本"])

# 作业相关路由
api_router.include_router(homework.router, tags=["作业批改"])

# 作业兼容性路由（前端兼容性）
api_router.include_router(homework_compatibility.router, tags=["作业批改-兼容性"])

api_router.include_router(analytics.router, tags=["学情分析"])

api_router.include_router(file.router, tags=["文件管理"])

api_router.include_router(health.router, tags=["健康检查"])
#     tags=["学情分析"]
# )
