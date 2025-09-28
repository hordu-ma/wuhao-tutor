"""
用户相关数据模型
包含用户基础信息、认证信息等
"""

from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class GradeLevel(enum.Enum):
    """学段枚举"""
    JUNIOR_1 = "junior_1"  # 初一
    JUNIOR_2 = "junior_2"  # 初二
    JUNIOR_3 = "junior_3"  # 初三
    SENIOR_1 = "senior_1"  # 高一
    SENIOR_2 = "senior_2"  # 高二
    SENIOR_3 = "senior_3"  # 高三


class UserRole(enum.Enum):
    """用户角色枚举"""
    STUDENT = "student"      # 学生
    TEACHER = "teacher"      # 教师
    PARENT = "parent"        # 家长
    ADMIN = "admin"          # 管理员


class User(BaseModel):
    """
    用户模型
    存储用户基础信息
    """
    __tablename__ = "users"

    # 基础认证信息
    phone = Column(
        String(11),
        unique=True,
        index=True,
        nullable=False,
        comment="手机号（主要登录凭证）"
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )

    # 第三方账号绑定
    wechat_openid = Column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
        comment="微信OpenID"
    )

    wechat_unionid = Column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
        comment="微信UnionID"
    )

    # 基础个人信息
    name = Column(
        String(50),
        nullable=False,
        comment="真实姓名"
    )

    nickname = Column(
        String(50),
        nullable=True,
        comment="昵称"
    )

    avatar_url = Column(
        String(500),
        nullable=True,
        comment="头像URL"
    )

    # 学习相关信息
    school = Column(
        String(100),
        nullable=True,
        comment="学校名称"
    )

    grade_level = Column(
        String(20),
        nullable=True,
        comment="学段"
    )

    class_name = Column(
        String(50),
        nullable=True,
        comment="班级"
    )

    institution = Column(
        String(100),
        nullable=True,
        comment="所属机构"
    )

    # 联系信息
    parent_contact = Column(
        String(11),
        nullable=True,
        comment="家长联系电话"
    )

    parent_name = Column(
        String(50),
        nullable=True,
        comment="家长姓名"
    )

    # 系统信息
    role = Column(
        String(20),
        default="student",
        nullable=False,
        comment="用户角色"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已验证手机号"
    )

    # 学习偏好设置
    study_subjects = Column(
        Text,
        nullable=True,
        comment="关注学科（JSON格式）"
    )

    study_goals = Column(
        Text,
        nullable=True,
        comment="学习目标（JSON格式）"
    )

    # 系统设置
    notification_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用通知"
    )

    last_login_at = Column(
        String(50),
        nullable=True,
        comment="最后登录时间"
    )

    login_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="登录次数"
    )

    # 表约束
    __table_args__ = (
        UniqueConstraint('phone', name='uq_user_phone'),
        UniqueConstraint('wechat_openid', name='uq_user_wechat_openid'),
    )

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', phone='{self.phone}', name='{self.name}')>"

    @property
    def is_student(self) -> bool:
        """是否为学生"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, 'role', '') == UserRole.STUDENT.value)

    @property
    def is_teacher(self) -> bool:
        """是否为教师"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, 'role', '') == UserRole.TEACHER.value)

    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, 'role', '') == UserRole.ADMIN.value)

    @property
    def display_name(self) -> str:
        """显示名称"""
        # 类型检查器修复：强制类型转换
        nickname = str(getattr(self, 'nickname', '') or '')
        name = str(getattr(self, 'name', ''))
        return nickname or name


class UserSession(BaseModel):
    """
    用户会话模型
    用于管理用户登录状态和JWT令牌
    """
    __tablename__ = "user_sessions"

    user_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    device_id = Column(
        String(128),
        nullable=True,
        comment="设备ID"
    )

    device_type = Column(
        String(20),
        nullable=True,
        comment="设备类型 (web/mobile/mini_program)"
    )

    access_token_jti = Column(
        String(36),
        nullable=False,
        unique=True,
        comment="访问令牌JTI"
    )

    refresh_token_jti = Column(
        String(36),
        nullable=False,
        unique=True,
        comment="刷新令牌JTI"
    )

    expires_at = Column(
        String(50),
        nullable=False,
        comment="过期时间"
    )

    is_revoked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已撤销"
    )

    ip_address = Column(
        String(45),
        nullable=True,
        comment="IP地址"
    )

    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理"
    )

    def __repr__(self) -> str:
        return f"<UserSession(user_id='{self.user_id}', device_type='{self.device_type}')>"
