"""
API v1 端点模块
包含所有API端点路由
"""

from . import auth
from . import learning
from . import homework
from . import file
from . import health

# 导出所有端点路由
__all__ = [
    "auth",
    "learning",
    "homework",
    "file",
    "health",
]
