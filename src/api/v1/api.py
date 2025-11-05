"""
API v1 路由集合
整合所有v1版本的API端点
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    file,
    goals,
    health,
    knowledge_graph,
    learning,
    mistakes,
    user,
)

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

api_router.include_router(admin.router, tags=["管理员"])

api_router.include_router(user.router, prefix="/user", tags=["用户管理"])

api_router.include_router(learning.router, prefix="/learning", tags=["学习问答"])

api_router.include_router(analytics.router, tags=["学情分析"])

# 错题手册路由
api_router.include_router(mistakes.router, prefix="/mistakes", tags=["错题手册"])

# 知识图谱路由
api_router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["知识图谱"]
)

# 每日目标路由
api_router.include_router(goals.router, tags=["每日目标"])

api_router.include_router(file.router, tags=["文件管理"])

api_router.include_router(health.router, tags=["健康检查"])
