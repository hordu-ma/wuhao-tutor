"""
管理员专用 Schema 定义
用于用户管理功能
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.user import UserResponse

# ========== 请求 Schema ==========


class AdminCreateUserRequest(BaseModel):
    """管理员创建用户请求"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    school: Optional[str] = Field(None, max_length=100, description="学校")
    grade_level: Optional[str] = Field(None, description="学段")
    class_name: Optional[str] = Field(None, max_length=50, description="班级")
    # 允许管理员指定角色（可选）
    role: Optional[str] = Field(
        None,
        description="用户角色: 'student'、'teacher' 或 'admin'",
        pattern=r"^(student|teacher|admin)$",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "13800138000",
                "name": "张三",
                "school": "示范小学",
                "grade_level": "primary_3",
                "class_name": "三年级1班",
                "role": "admin",
            }
        }
    }


class AdminUpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""

    is_active: bool = Field(..., description="是否激活")


# ========== 响应 Schema ==========


class AdminCreateUserResponse(BaseModel):
    """管理员创建用户响应"""

    user: UserResponse
    password: str = Field(..., description="明文密码（仅显示一次）")


class AdminResetPasswordResponse(BaseModel):
    """重置密码响应"""

    user_id: str
    phone: str
    name: str
    password: str = Field(..., description="新密码（明文）")


class AdminUserListItem(BaseModel):
    """用户列表项"""

    id: str
    phone: str
    name: str
    nickname: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = None
    class_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    login_count: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminUserListResponse(BaseModel):
    """用户列表响应"""

    total: int
    page: int
    size: int
    items: List[AdminUserListItem]
