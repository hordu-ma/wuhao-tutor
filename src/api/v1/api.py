"""
API v1 路由集合
整合所有v1版本的API端点
"""

from fastapi import APIRouter

from src.api.v1.endpoints import auth, learning

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    learning.router,
    prefix="/learning",
    tags=["学习问答"]
)

# TODO: 添加其他模块路由
# api_router.include_router(
#     homework.router,
#     prefix="/homework",
#     tags=["作业批改"]
# )
#
# api_router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["用户管理"]
# )
#
# api_router.include_router(
#     analytics.router,
#     prefix="/analytics",
#     tags=["学情分析"]
# )
