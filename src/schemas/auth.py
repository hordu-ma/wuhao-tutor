"""
用户认证相关的Pydantic Schema模型
包含登录、注册、token管理等数据结构
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator


class DeviceType(str, Enum):
    """设备类型枚举"""

    WEB = "web"
    MOBILE = "mobile"
    MINI_PROGRAM = "mini_program"
    APP = "app"


class UserRole(str, Enum):
    """用户角色枚举"""

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


class GradeLevel(str, Enum):
    """学段枚举 - 完整K12教育体系"""

    # 小学阶段
    PRIMARY_1 = "primary_1"
    PRIMARY_2 = "primary_2"
    PRIMARY_3 = "primary_3"
    PRIMARY_4 = "primary_4"
    PRIMARY_5 = "primary_5"
    PRIMARY_6 = "primary_6"
    # 初中阶段
    JUNIOR_1 = "junior_1"
    JUNIOR_2 = "junior_2"
    JUNIOR_3 = "junior_3"
    # 高中阶段
    SENIOR_1 = "senior_1"
    SENIOR_2 = "senior_2"
    SENIOR_3 = "senior_3"


# ========== 基础Schema模型 ==========


class UserBase(BaseModel):
    """用户基础模型"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    name: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    school: Optional[str] = Field(None, max_length=100, description="学校名称")
    grade_level: Optional[GradeLevel] = Field(None, description="学段")
    class_name: Optional[str] = Field(None, max_length=50, description="班级")
    institution: Optional[str] = Field(None, max_length=100, description="所属机构")
    parent_contact: Optional[str] = Field(
        None, pattern=r"^1[3-9]\d{9}$", description="家长联系电话"
    )
    parent_name: Optional[str] = Field(None, max_length=50, description="家长姓名")


class TokenBase(BaseModel):
    """令牌基础模型"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


# ========== 请求Schema模型 ==========


class RegisterRequest(UserBase):
    """用户注册请求"""

    password: str = Field(..., min_length=6, max_length=128, description="密码")
    password_confirm: str = Field(..., description="确认密码")
    verification_code: str = Field(
        ..., min_length=6, max_length=6, description="短信验证码"
    )
    role: UserRole = Field(default=UserRole.STUDENT, description="用户角色")

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "13800138000",
                "name": "张三",
                "nickname": "小张",
                "password": "123456",
                "password_confirm": "123456",
                "verification_code": "123456",
                "role": "student",
                "school": "北京中学",
                "grade_level": "junior_2",
                "class_name": "初二(1)班",
            }
        }
    )


class LoginRequest(BaseModel):
    """登录请求"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    password: str = Field(..., min_length=1, description="密码")
    device_type: Optional[DeviceType] = Field(
        default=DeviceType.WEB, description="设备类型"
    )
    device_id: Optional[str] = Field(None, max_length=128, description="设备ID")
    remember_me: bool = Field(default=False, description="记住登录状态")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "13800138000",
                "password": "123456",
                "device_type": "web",
                "remember_me": False,
            }
        }
    )


class WechatLoginRequest(BaseModel):
    """微信登录请求"""

    code: str = Field(..., description="微信授权码")
    device_type: Optional[DeviceType] = Field(
        default=DeviceType.MINI_PROGRAM, description="设备类型"
    )
    device_id: Optional[str] = Field(None, max_length=128, description="设备ID")
    # 如果是新用户，需要补充信息
    name: Optional[str] = Field(None, max_length=50, description="姓名")
    school: Optional[str] = Field(None, max_length=100, description="学校")
    grade_level: Optional[GradeLevel] = Field(None, description="学段")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., description="刷新令牌")
    device_type: Optional[DeviceType] = Field(
        default=DeviceType.WEB, description="设备类型"
    )


class LogoutRequest(BaseModel):
    """登出请求"""

    device_type: Optional[DeviceType] = Field(
        default=DeviceType.WEB, description="设备类型"
    )
    logout_all_devices: bool = Field(default=False, description="是否登出所有设备")


class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    purpose: str = Field(..., description="用途: register/reset_password/bind_phone")

    model_config = ConfigDict(
        json_schema_extra={"example": {"phone": "13800138000", "purpose": "register"}}
    )


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    verification_code: str = Field(
        ..., min_length=6, max_length=6, description="短信验证码"
    )
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    password_confirm: str = Field(..., description="确认密码")

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    password_confirm: str = Field(..., description="确认密码")

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    school: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[GradeLevel] = None
    class_name: Optional[str] = Field(None, max_length=50)
    institution: Optional[str] = Field(None, max_length=100)
    parent_contact: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    parent_name: Optional[str] = Field(None, max_length=50)
    notification_enabled: Optional[bool] = None


# ========== 响应Schema模型 ==========


class UserResponse(UserBase):
    """用户信息响应"""

    id: str
    role: UserRole
    is_active: bool
    is_verified: bool
    notification_enabled: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(TokenBase):
    """登录响应"""

    user: UserResponse
    session_id: str = Field(..., description="会话ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "phone": "13800138000",
                    "name": "张三",
                    "role": "student",
                },
                "session_id": "sess_123456789",
            }
        }
    )


class RefreshTokenResponse(TokenBase):
    """刷新令牌响应"""

    session_id: str = Field(..., description="会话ID")
    user: "UserResponse" = Field(..., description="用户信息")


class UserSessionResponse(BaseModel):
    """用户会话响应"""

    id: str
    user_id: str
    device_type: Optional[DeviceType] = None
    device_id: Optional[str] = None
    expires_at: datetime
    is_revoked: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WechatUserInfo(BaseModel):
    """微信用户信息"""

    openid: str
    unionid: Optional[str] = None
    nickname: str
    avatar_url: str
    gender: Optional[int] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None


class WechatLoginResponse(LoginResponse):
    """微信登录响应"""

    is_new_user: bool = Field(..., description="是否为新用户")
    wechat_info: WechatUserInfo


# ========== 管理和统计Schema模型 ==========


class UserListQuery(BaseModel):
    """用户列表查询"""

    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    school: Optional[str] = None
    grade_level: Optional[GradeLevel] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")


class PaginatedResponse(BaseModel):
    """分页响应基础模型"""

    total: int
    page: int
    size: int
    pages: int


class UserListResponse(PaginatedResponse):
    """用户列表响应"""

    items: List[UserResponse]


class SessionListResponse(PaginatedResponse):
    """会话列表响应"""

    items: List[UserSessionResponse]


class UserStatsResponse(BaseModel):
    """用户统计响应"""

    total_users: int
    active_users: int
    new_users_today: int
    new_users_week: int
    verified_users: int
    role_distribution: dict = Field(..., description="角色分布")
    grade_distribution: dict = Field(..., description="年级分布")


# ========== 权限和角色Schema模型 ==========


class PermissionResponse(BaseModel):
    """权限响应"""

    code: str
    name: str
    description: str
    resource: str
    action: str


class RoleResponse(BaseModel):
    """角色响应"""

    code: str
    name: str
    description: str
    permissions: List[PermissionResponse]


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""

    user_id: str
    role: UserRole
    permissions: List[str] = Field(..., description="权限代码列表")
    resources: dict = Field(..., description="资源权限映射")


# ========== 验证和安全Schema模型 ==========


class VerifyCodeResponse(BaseModel):
    """验证码响应"""

    message: str = Field(default="验证码发送成功")
    expires_in: int = Field(default=300, description="验证码有效期(秒)")
    can_resend_in: int = Field(default=60, description="重发间隔(秒)")


class SecurityLogResponse(BaseModel):
    """安全日志响应"""

    id: str
    user_id: str
    action: str = Field(..., description="操作类型")
    resource: str = Field(..., description="资源")
    ip_address: str
    user_agent: str
    status: str = Field(..., description="状态: success/failed")
    details: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyResponse(BaseModel):
    """API密钥响应"""

    id: str
    name: str
    key: str = Field(..., description="API密钥")
    permissions: List[str]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateApiKeyRequest(BaseModel):
    """创建API密钥请求"""

    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    permissions: List[str] = Field(..., description="权限列表")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="有效期(天)")
