"""
API依赖模块
提供FastAPI的依赖注入函数
"""

from .auth import get_current_active_user, get_current_user

__all__ = [
    "get_current_user",
    "get_current_active_user",
]
