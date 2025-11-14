"""
用户相关数据工厂
"""

import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

from factory.base import Factory
from factory.declarations import LazyAttribute, LazyFunction, Sequence
from factory.faker import Faker

from src.models.user import GradeLevel, User, UserRole


class UserModelFactory(Factory):
    """
    User 模型工厂（使用 factory-boy）
    用于生成标准的 User 对象但不持久化到数据库
    """

    class Meta:
        model = User

    id = LazyFunction(lambda: str(uuid.uuid4()))
    phone = Sequence(lambda n: f"138{n:08d}")
    password_hash = "pbkdf2:sha256:260000$hashed_password"
    name = Faker("name", locale="zh_CN")
    nickname = LazyAttribute(lambda obj: f"{obj.name}的昵称")
    avatar_url = Faker("image_url")

    wechat_openid = None
    wechat_unionid = None

    school = Faker("company", locale="zh_CN")
    grade_level = GradeLevel.SENIOR_1.value
    class_name = Sequence(lambda n: f"高一{n}班")
    institution = None

    parent_contact = None
    parent_name = None

    role = UserRole.STUDENT.value
    is_active = True
    is_verified = True

    created_at = LazyFunction(datetime.utcnow)
    updated_at = LazyFunction(datetime.utcnow)
    deleted_at = None


class UserFactory:
    """用户数据工厂（传统方法）"""

    @staticmethod
    def create_user(
        user_id: Optional[str] = None,
        phone: str = "13800138000",
        name: str = "测试用户",
        password_hash: str = "hashed_password",
        role: UserRole = UserRole.STUDENT,
        grade_level: Optional[GradeLevel] = GradeLevel.SENIOR_1,
        **kwargs,
    ) -> User:
        """创建测试用户"""
        user = User(
            id=user_id or str(uuid.uuid4()),
            phone=phone,
            name=name,
            password_hash=password_hash,
            role=role.value if isinstance(role, UserRole) else role,
            grade_level=(
                grade_level.value
                if isinstance(grade_level, GradeLevel)
                else grade_level
            ),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs,
        )
        return user

    @staticmethod
    def create_student(
        user_id: Optional[str] = None,
        phone: str = "13800138001",
        name: str = "学生用户",
        grade_level: GradeLevel = GradeLevel.SENIOR_1,
        **kwargs,
    ) -> User:
        """创建学生用户"""
        return UserFactory.create_user(
            user_id=user_id,
            phone=phone,
            name=name,
            role=UserRole.STUDENT,
            grade_level=grade_level,
            **kwargs,
        )

    @staticmethod
    def create_teacher(
        user_id: Optional[str] = None,
        phone: str = "13800138002",
        name: str = "教师用户",
        **kwargs,
    ) -> User:
        """创建教师用户"""
        return UserFactory.create_user(
            user_id=user_id,
            phone=phone,
            name=name,
            role=UserRole.TEACHER,
            grade_level=None,
            **kwargs,
        )

    @staticmethod
    def create_admin(
        user_id: Optional[str] = None,
        phone: str = "13800138003",
        name: str = "管理员",
        **kwargs,
    ) -> User:
        """创建管理员用户"""
        return UserFactory.create_user(
            user_id=user_id,
            phone=phone,
            name=name,
            role=UserRole.ADMIN,
            grade_level=None,
            **kwargs,
        )

    @staticmethod
    def create_mock_user(
        user_id: str = "test_user_123", username: str = "testuser", **kwargs
    ) -> MagicMock:
        """创建Mock用户对象"""
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = username
        mock_user.phone = kwargs.get("phone", "13800138000")
        mock_user.name = kwargs.get("name", "测试用户")
        mock_user.role = kwargs.get("role", UserRole.STUDENT.value)
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()
        return mock_user

    @staticmethod
    def create_batch_students(count: int = 5, **kwargs) -> list[User]:
        """批量创建学生用户"""
        return [
            UserFactory.create_student(
                phone=f"138{i:08d}",
                name=f"学生{i}",
                **kwargs,
            )
            for i in range(count)
        ]
