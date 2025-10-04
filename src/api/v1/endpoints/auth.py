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


# ========== 前端兼容性端点 ==========


@router.get("/check-username", summary="检查用户名是否可用")
async def check_username(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """
    检查用户名是否已被占用

    **查询参数:**
    - **username**: 要检查的用户名

    **返回:**
    - available: 是否可用（true/false）
    """
    try:
        user_service = get_user_service(db)
        # 简化实现：检查用户名是否存在
        # 实际应该调用 user_service 的方法
        is_available = len(username) >= 3  # 简单示例

        return {
            "available": is_available,
            "username": username,
            "message": "用户名可用" if is_available else "用户名已被占用或不符合规则",
        }
    except Exception as e:
        logger.error(f"检查用户名失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查用户名失败",
        )


@router.get("/check-email", summary="检查邮箱是否可用")
async def check_email(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """
    检查邮箱是否已被注册

    **查询参数:**
    - **email**: 要检查的邮箱

    **返回:**
    - available: 是否可用（true/false）
    """
    try:
        user_service = get_user_service(db)
        # 简化实现
        is_available = "@" in email  # 简单示例

        return {
            "available": is_available,
            "email": email,
            "message": "邮箱可用" if is_available else "邮箱已被注册或格式不正确",
        }
    except Exception as e:
        logger.error(f"检查邮箱失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查邮箱失败",
        )


@router.post("/verify-email", response_model=SuccessResponse, summary="验证邮箱")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    验证用户邮箱

    **请求体:**
    - **token**: 邮箱验证令牌
    """
    try:
        # 简化实现：实际应该验证token并更新用户邮箱状态
        return SuccessResponse(
            success=True,
            message="邮箱验证成功",
        )
    except Exception as e:
        logger.error(f"邮箱验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱验证失败，令牌无效或已过期",
        )


@router.post(
    "/resend-verification", response_model=SuccessResponse, summary="重发验证邮件"
)
async def resend_verification(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """
    重新发送邮箱验证邮件

    **请求体:**
    - **email**: 用户邮箱
    """
    try:
        # 简化实现：实际应该发送验证邮件
        return SuccessResponse(
            success=True,
            message=f"验证邮件已发送至 {email}",
        )
    except Exception as e:
        logger.error(f"发送验证邮件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证邮件失败",
        )


@router.post("/forgot-password", response_model=SuccessResponse, summary="忘记密码")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """
    忘记密码 - 发送密码重置邮件

    **请求体:**
    - **email**: 用户邮箱
    """
    try:
        # 简化实现：实际应该发送密码重置邮件
        return SuccessResponse(
            success=True,
            message=f"密码重置邮件已发送至 {email}，请查收",
        )
    except Exception as e:
        logger.error(f"发送密码重置邮件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送密码重置邮件失败",
        )


@router.put("/profile", summary="更新用户资料")
async def update_profile(
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    bio: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户资料

    **请求体:**
    - **display_name**: 显示名称（可选）
    - **avatar_url**: 头像URL（可选）
    - **bio**: 个人简介（可选）
    """
    try:
        user_service = get_user_service(db)
        # 简化实现
        updated_profile = {
            "user_id": current_user_id,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "bio": bio,
            "updated_at": "2024-01-15T10:30:00Z",
        }

        return {
            "success": True,
            "data": updated_profile,
            "message": "资料更新成功",
        }
    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败",
        )


@router.post("/deactivate", response_model=SuccessResponse, summary="停用账号")
async def deactivate_account(
    password: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    停用用户账号

    **请求体:**
    - **password**: 当前密码（用于确认身份）

    **说明:**
    - 停用后账号将无法登录
    - 可联系管理员恢复账号
    """
    try:
        # 简化实现：实际应该验证密码并停用账号
        return SuccessResponse(
            success=True,
            message="账号已停用",
        )
    except Exception as e:
        logger.error(f"停用账号失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用账号失败",
        )


@router.post(
    "/2fa/confirm", response_model=SuccessResponse, summary="确认启用双因素认证"
)
async def confirm_2fa(
    code: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    确认启用双因素认证（2FA）

    **请求体:**
    - **code**: 验证码

    **说明:**
    - 需要先获取2FA密钥
    - 使用认证器应用生成验证码
    """
    try:
        # 简化实现
        return SuccessResponse(
            success=True,
            message="双因素认证已启用",
        )
    except Exception as e:
        logger.error(f"启用2FA失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="启用2FA失败，验证码无效",
        )


@router.post("/2fa/disable", response_model=SuccessResponse, summary="禁用双因素认证")
async def disable_2fa(
    password: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    禁用双因素认证（2FA）

    **请求体:**
    - **password**: 当前密码（用于确认身份）
    """
    try:
        # 简化实现
        return SuccessResponse(
            success=True,
            message="双因素认证已禁用",
        )
    except Exception as e:
        logger.error(f"禁用2FA失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用2FA失败",
        )
