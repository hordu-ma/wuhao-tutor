"""
API v1 端点模块
包含所有API端点路由
"""

from . import analytics, auth, file, goals, health, learning, mistakes, user

# 导出所有端点路由
__all__ = [
    "auth",
    "learning",
    "file",
    "health",
    "analytics",
    "mistakes",
    "user",
    "goals",
]
