"""
认证API端点
提供用户注册、登录、登出、token刷新等认证相关接口
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ServiceError,
    ValidationError,
)
from src.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SendVerificationCodeRequest,
    VerifyCodeResponse,
    WechatLoginRequest,
)
from src.schemas.common import ErrorResponse, SuccessResponse
from src.services.auth_service import get_auth_service
from src.services.user_service import get_user_service

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger("auth.endpoints")


# ========== 依赖注入 ==========


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> str:
    """获取当前用户ID"""
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)

        token = credentials.credentials
        payload = auth_service.verify_token(token)

        if payload.get("type") != "access":
            raise AuthenticationError("令牌类型错误")

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise AuthenticationError("令牌格式错误")

        # 验证会话
        session = await auth_service.verify_user_session(jti)
        if not session:
            raise AuthenticationError("会话已失效")

        return user_id

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_client_info(request: Request) -> dict:
    """获取客户端信息"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "device_id": request.headers.get("x-device-id"),
    }


# ========== 认证端点 ==========


@router.post("/register", response_model=LoginResponse, summary="用户注册")
async def register(
    request: RegisterRequest,
    client_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册

    - **phone**: 手机号
    - **password**: 密码
    - **password_confirm**: 确认密码
    - **verification_code**: 短信验证码
    - **name**: 真实姓名
    - **role**: 用户角色 (student/teacher/parent)
    """
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)
        client_info = get_client_info(client_request)

        # 创建用户
        user_response = await user_service.create_user(request)

        # 自动登录
        login_response = await auth_service.authenticate_with_password(
            phone=request.phone,
            password=request.password,
            device_type=client_request.headers.get("x-device-type", "web"),
            device_id=client_info.get("device_id"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )

        return login_response

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试",
        )


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    request: LoginRequest, client_request: Request, db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    - **phone**: 手机号
    - **password**: 密码
    - **device_type**: 设备类型 (web/mobile/mini_program/app)
    - **remember_me**: 是否记住登录状态
    """
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)
        client_info = get_client_info(client_request)

        login_response = await auth_service.authenticate_with_password(
            phone=request.phone,
            password=request.password,
            device_type=request.device_type.value if request.device_type else "web",
            device_id=request.device_id or client_info.get("device_id"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            remember_me=request.remember_me,
        )

        return login_response

    except AuthenticationError as e:
        logger.warning(f"登录认证失败: {str(e)}", extra={"phone": request.phone})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(
            f"登录过程中发生异常: {str(e)}",
            extra={"phone": request.phone},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}",
        )


@router.post("/wechat-login", response_model=LoginResponse, summary="微信小程序登录")
async def wechat_login(
    request: WechatLoginRequest,
    client_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    微信小程序登录

    - **code**: 微信授权码 (通过wx.login获取)
    - **device_type**: 设备类型 (默认为mini_program)
    - **device_id**: 设备ID (可选)
    - **name**: 用户姓名 (新用户注册时可选)
    - **school**: 学校 (新用户注册时可选)
    - **grade_level**: 学段 (新用户注册时可选)

    流程:
    1. 使用code换取openid和session_key
    2. 查找或创建用户
    3. 生成JWT token
    4. 返回登录信息
    """
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)
        client_info = get_client_info(client_request)

        # 准备用户信息（用于新用户注册）
        user_info = {}
        if request.name:
            user_info["name"] = request.name
        if request.school:
            user_info["school"] = request.school
        if request.grade_level:
            user_info["grade_level"] = request.grade_level.value

        login_response = await auth_service.authenticate_with_wechat(
            code=request.code,
            device_type=(
                request.device_type.value if request.device_type else "mini_program"
            ),
            device_id=request.device_id or client_info.get("device_id"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            user_info=user_info if user_info else None,
        )

        logger.info(f"微信登录成功: user_id={login_response.user.id}")
        return login_response

    except AuthenticationError as e:
        logger.warning(f"微信登录认证失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ServiceError as e:
        logger.error(f"微信登录服务失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"微信登录失败: {str(e)}",
        )
    except Exception as e:
        logger.error(f"微信登录异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}",
        )


@router.post("/refresh", response_model=RefreshTokenResponse, summary="刷新访问令牌")
async def refresh_token(
    request: RefreshTokenRequest,
    client_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌
    - **device_type**: 设备类型
    """
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)

        refresh_response = await auth_service.refresh_access_token(
            refresh_token=request.refresh_token,
            device_type=request.device_type.value if request.device_type else "web",
        )

        return refresh_response

    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败，请稍后重试",
        )


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout(
    request: LogoutRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出

    - **logout_all_devices**: 是否登出所有设备
    """
    try:
        user_service = get_user_service(db)
        auth_service = get_auth_service(user_service)

        # 从令牌中获取会话ID（简化处理）
        success = await auth_service.logout_user(
            user_id=current_user_id, logout_all_devices=request.logout_all_devices
        )

        return SuccessResponse(message="登出成功" if success else "登出失败")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败，请稍后重试",
        )


# ========== 密码管理端点 ==========


@router.post(
    "/send-verification-code", response_model=VerifyCodeResponse, summary="发送验证码"
)
async def send_verification_code(
    request: SendVerificationCodeRequest, db: AsyncSession = Depends(get_db)
):
    """
    发送短信验证码

    - **phone**: 手机号
    - **purpose**: 用途 (register/reset_password/bind_phone)
    """
    try:
        # TODO: 集成短信服务
        # sms_service = get_sms_service()
        # await sms_service.send_verification_code(request.phone, request.purpose)

        return VerifyCodeResponse(
            message="验证码发送成功", expires_in=300, can_resend_in=60
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试",
        )


@router.post("/reset-password", response_model=SuccessResponse, summary="重置密码")
async def reset_password(
    request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """
    通过验证码重置密码

    - **phone**: 手机号
    - **verification_code**: 短信验证码
    - **new_password**: 新密码
    - **password_confirm**: 确认密码
    """
    try:
        user_service = get_user_service(db)

        success = await user_service.reset_password(
            phone=request.phone,
            new_password=request.new_password,
            verification_code=request.verification_code,
        )

        return SuccessResponse(message="密码重置成功" if success else "密码重置失败")

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败，请稍后重试",
        )


@router.post("/change-password", response_model=SuccessResponse, summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    修改密码（需要认证）

    - **old_password**: 旧密码
    - **new_password**: 新密码
    - **password_confirm**: 确认密码
    """
    try:
        user_service = get_user_service(db)

        success = await user_service.change_password(
            user_id=current_user_id,
            old_password=request.old_password,
            new_password=request.new_password,
        )

        return SuccessResponse(
            message="密码修改成功，请重新登录" if success else "密码修改失败"
        )

    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败，请稍后重试",
        )


# ========== 用户信息端点 ==========


@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的详细信息"""
    try:
        user_service = get_user_service(db)

        user_detail = await user_service.get_user_detail(current_user_id)
        if not user_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        return user_detail

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户信息失败"
        )


@router.get("/verify-token", summary="验证令牌有效性")
async def verify_token(current_user_id: str = Depends(get_current_user_id)):
    """
    验证访问令牌是否有效

    如果令牌有效，返回用户ID；否则返回401错误
    """
    return {"valid": True, "user_id": current_user_id, "message": "令牌有效"}
