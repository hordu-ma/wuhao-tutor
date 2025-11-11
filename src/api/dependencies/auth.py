"""
认证依赖函数
为FastAPI提供用户认证和授权的依赖注入
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AuthenticationError, AuthorizationError
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService, get_user_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    获取当前认证用户

    Args:
        credentials: HTTP Bearer token
        db: 数据库会话
        user_service: 用户服务

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    try:
        # 创建认证服务并验证token
        auth_service = AuthService(user_service)
        payload = auth_service.verify_token(credentials.credentials)

        # 从payload中获取用户ID并查询用户
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await user_service.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        当前活跃用户对象

    Raises:
        HTTPException: 用户未激活时抛出403错误
    """
    if not getattr(current_user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> Optional[User]:
    """
    获取可选的当前用户（允许匿名访问）

    Args:
        credentials: HTTP Bearer token（可选）
        db: 数据库会话
        user_service: 用户服务

    Returns:
        当前用户对象或None
    """
    if not credentials:
        return None

    try:
        auth_service = AuthService(user_service)
        payload = auth_service.verify_token(credentials.credentials)

        # 从payload中获取用户ID并查询用户
        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await user_service.user_repo.get_by_id(user_id)
        return user
    except Exception:
        return None


async def get_current_user_id(current_user: User = Depends(get_current_user)) -> str:
    """
    获取当前用户ID

    Args:
        current_user: 当前用户

    Returns:
        用户ID字符串
    """
    return str(current_user.id)


def require_role(*allowed_roles: str):
    """
    角色权限装饰器 - 简化版，所有认证用户都是学生角色

    Args:
        allowed_roles: 允许的角色列表（保留接口兼容性，但实际不再检查）

    Returns:
        依赖函数
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # 简化：所有认证用户都被视为学生角色，无需角色检查
        return current_user

    return role_checker


def require_permission(permission: str):
    """
    权限检查装饰器

    Args:
        permission: 需要的权限

    Returns:
        依赖函数
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        # 这里可以实现更复杂的权限检查逻辑
        # 例如检查用户的permissions字段
        user_permissions = getattr(current_user, "permissions", [])

        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}",
            )

        return current_user

    return permission_checker


# 预定义的角色依赖
require_admin = require_role("admin")
require_teacher = require_role("admin", "teacher")
require_student = require_role("admin", "teacher", "student")
