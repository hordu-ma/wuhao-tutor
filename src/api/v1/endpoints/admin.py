"""
管理员 API 端点
提供用户管理功能
"""

import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import ConflictError, NotFoundError
from src.schemas.admin import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
    AdminResetPasswordResponse,
    AdminUpdateUserStatusRequest,
    AdminUserListItem,
    AdminUserListResponse,
)
from src.schemas.common import SuccessResponse
from src.schemas.user import UserResponse
from src.services.auth_service import AuthService
from src.services.user_service import get_user_service
from src.utils.cache import cache_manager

router = APIRouter(prefix="/admin", tags=["管理员"])


# Token 验证缓存：键为 hash(token)，值为 user_id，TTL=1小时
async def _verify_token_with_cache(token: str, db: AsyncSession) -> str:
    """
    带缓存的 Token 验证
    - 首次验证：查询数据库，缓存结果（1小时）
    - 后续请求：直接从缓存读取，减少 JWT 解析 + 数据库查询
    """
    # 生成缓存键
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    cache_key = f"admin_token:{token_hash}"

    # 尝试从缓存读取
    cached_user_id = await cache_manager.get(cache_key, namespace="security")
    if cached_user_id:
        return cached_user_id

    # 缓存未命中，执行完整验证
    user_service = get_user_service(db)
    auth_service = AuthService(user_service)
    payload = auth_service.verify_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 检查管理员权限
    user = await user_service.user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限才能访问此功能")

    # 缓存验证结果（TTL=1小时）
    await cache_manager.set(cache_key, user_id, ttl=3600, namespace="security")

    return user_id


async def verify_token(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db),
):
    """Token 验证并检查管理员权限（使用 Redis 缓存优化）"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        return await _verify_token_with_cache(token, db)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post(
    "/users",
    response_model=AdminCreateUserResponse,
    summary="创建用户",
)
async def create_user(
    request: AdminCreateUserRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_token),
):
    """
    管理员创建用户

    - 自动生成安全密码
    - 返回明文密码（仅此一次）
    - 需要管理员权限（暂时所有认证用户都有权限）
    """
    try:
        user_service = get_user_service(db)

        user, password = await user_service.admin_create_user(
            phone=request.phone,
            name=request.name,
            school=request.school,
            grade_level=request.grade_level,
            class_name=request.class_name,
        )

        # 转换为响应格式
        user_dict = {k: v for k, v in user.__dict__.items() if not k.startswith("_")}
        user_dict["id"] = str(user.id)
        user_response = UserResponse.model_validate(user_dict)

        return AdminCreateUserResponse(user=user_response, password=password)

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}",
        )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="查询用户列表",
)
async def list_users(
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_token),
):
    """
    管理员查询用户列表

    - 支持分页
    - 支持搜索（姓名、手机号、昵称）
    - 需要管理员权限（暂时所有认证用户都有权限）
    """
    try:
        user_service = get_user_service(db)
        users, total = await user_service.admin_list_users(
            page=page, size=size, search=search
        )

        items = [
            AdminUserListItem(
                id=str(user.id),
                phone=user.phone,
                name=user.name,
                nickname=user.nickname,
                school=user.school,
                grade_level=user.grade_level,
                class_name=user.class_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                login_count=user.login_count,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
            )
            for user in users
        ]

        return AdminUserListResponse(total=total, page=page, size=size, items=items)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询用户列表失败: {str(e)}",
        )


@router.post(
    "/users/{user_id}/reset-password",
    response_model=AdminResetPasswordResponse,
    summary="重置用户密码",
)
async def reset_user_password(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(verify_token),
):
    """
    管理员重置用户密码

    - 自动生成新密码
    - 返回明文密码（仅此一次）
    - 撤销该用户所有登录会话
    - 需要管理员权限（暂时所有认证用户都有权限）
    """
    try:
        user_service = get_user_service(db)
        user, new_password = await user_service.admin_reset_password(user_id)

        return AdminResetPasswordResponse(
            user_id=str(user.id),
            phone=user.phone,
            name=user.name,
            password=new_password,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置密码失败: {str(e)}",
        )


@router.put(
    "/users/{user_id}/status",
    response_model=SuccessResponse,
    summary="启用/禁用用户",
)
async def update_user_status(
    user_id: str,
    request: AdminUpdateUserStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(verify_token),
):
    """
    管理员启用/禁用用户

    - 禁用后用户无法登录
    - 需要管理员权限（暂时所有认证用户都有权限）
    """
    try:
        user_service = get_user_service(db)
        user = await user_service.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        await user_service.user_repo.update(user_id, {"is_active": request.is_active})

        action = "启用" if request.is_active else "禁用"
        return SuccessResponse(message=f"用户{action}成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}",
        )


@router.delete(
    "/users/{user_id}",
    response_model=SuccessResponse,
    summary="删除用户",
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(verify_token),
):
    """
    管理员删除用户

    - 将彻底删除用户及其所有数据
    - 需要管理员权限（暂时所有认证用户都有权限）
    - 谨慎操作，不可恢复
    """
    try:
        user_service = get_user_service(db)
        user = await user_service.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 删除用户
        await user_service.user_repo.delete(user_id)

        return SuccessResponse(message="用户删除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}",
        )
