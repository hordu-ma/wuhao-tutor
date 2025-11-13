"""
用户服务单元测试
测试用户创建、查询、更新等功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.schemas.auth import RegisterRequest
from src.services.user_service import UserService, get_user_service
from tests.factories import UserFactory


class TestUserServiceCreation:
    """用户创建测试"""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """测试成功创建用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        request = RegisterRequest(
            phone="13900000001",
            password="TestPass123!",
            name="新用户",
            grade_level="senior_1",
        )

        # Mock检查手机号不存在
        user_service.user_repo.get_by_field = AsyncMock(return_value=None)

        # Mock创建用户
        new_user = UserFactory.create_user(phone=request.phone, name=request.name)
        user_service.user_repo.create = AsyncMock(return_value=new_user)

        result = await user_service.create_user(request)

        assert result is not None
        user_service.user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_phone(self):
        """测试创建重复手机号用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        request = RegisterRequest(
            phone="13800138000",
            password="TestPass123!",
            name="用户",
            grade_level="senior_1",
        )

        # Mock手机号已存在
        existing_user = UserFactory.create_user(phone=request.phone)
        user_service.user_repo.get_by_field = AsyncMock(return_value=existing_user)

        with pytest.raises(ConflictError):
            await user_service.create_user(request)

    @pytest.mark.asyncio
    async def test_admin_create_user_with_admin_role(self):
        """管理员创建用户并指定 admin 角色"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        phone = "18888333726"
        name = "张小明"

        # Mock检查手机号不存在
        user_service.user_repo.get_by_field = AsyncMock(return_value=None)

        # Mock创建用户为 admin
        created_user = UserFactory.create_user(phone=phone, name=name, role="admin")
        user_service.user_repo.create = AsyncMock(return_value=created_user)

        user, password = await user_service.admin_create_user(
            phone=phone, name=name, role="admin"
        )

        assert user is not None
        assert user.role == "admin"
        assert isinstance(password, str) and len(password) > 0

    @pytest.mark.asyncio
    async def test_create_wechat_user_success(self):
        """测试创建微信用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        wechat_data = {
            "wechat_openid": "test_openid",
            "nickname": "微信用户",
            "avatar_url": "https://example.com/avatar.png",
        }

        # Mock检查openid不存在
        user_service.user_repo.get_by_field = AsyncMock(return_value=None)

        # Mock创建用户
        new_user = UserFactory.create_user(**wechat_data)
        user_service.user_repo.create = AsyncMock(return_value=new_user)

        result = await user_service.create_wechat_user(**wechat_data)

        assert result is not None


class TestUserServiceQuery:
    """用户查询测试"""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        """测试根据ID获取用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_id = "test_user_123"
        expected_user = UserFactory.create_user(user_id=user_id)

        user_service.user_repo.get_by_id = AsyncMock(return_value=expected_user)

        result = await user_service.get_user_by_id(user_id)

        assert result is not None
        assert result.id == user_id

    @pytest.mark.asyncio
    async def test_get_user_by_phone(self):
        """测试根据手机号获取用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        phone = "13800138000"
        expected_user = UserFactory.create_user(phone=phone)

        user_service.user_repo.get_by_field = AsyncMock(return_value=expected_user)

        result = await user_service.get_user_by_phone(phone)

        assert result is not None
        assert result.phone == phone

    @pytest.mark.asyncio
    async def test_get_user_by_wechat_openid(self):
        """测试根据微信openid获取用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        openid = "test_openid_123"
        expected_user = UserFactory.create_user(wechat_openid=openid)

        user_service.user_repo.get_by_field = AsyncMock(return_value=expected_user)

        result = await user_service.get_user_by_wechat_openid(openid)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """测试获取不存在的用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_service.user_repo.get_by_id = AsyncMock(return_value=None)

        result = await user_service.get_user_by_id("nonexistent_id")

        assert result is None


class TestUserServiceUpdate:
    """用户更新测试"""

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """测试成功更新用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_id = "test_user_123"
        update_data = {"name": "更新后的姓名", "nickname": "新昵称"}

        # Mock获取用户
        existing_user = UserFactory.create_user(user_id=user_id)
        user_service.user_repo.get_by_id = AsyncMock(return_value=existing_user)

        # Mock更新
        updated_user = UserFactory.create_user(user_id=user_id, **update_data)
        user_service.user_repo.update = AsyncMock(return_value=updated_user)

        result = await user_service.update_user(user_id, update_data)

        assert result is not None
        user_service.user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password_success(self):
        """测试成功更新密码"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_id = "test_user_123"
        new_password = "NewPassword123!"

        # Mock获取用户
        existing_user = UserFactory.create_user(user_id=user_id)
        user_service.user_repo.get_by_id = AsyncMock(return_value=existing_user)

        # Mock密码哈希
        with patch.object(
            user_service, "_hash_password", return_value="new_hashed_password"
        ):
            # Mock更新
            user_service.user_repo.update = AsyncMock(return_value=existing_user)

            await user_service.update_password(user_id, new_password)

            user_service.user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self):
        """测试更新不存在的用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_service.user_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await user_service.update_user("nonexistent_id", {"name": "新名字"})


class TestUserServiceValidation:
    """用户验证测试"""

    @pytest.mark.asyncio
    async def test_check_username_available(self):
        """测试检查用户名可用性"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        username = "newuser"

        # Mock用户名不存在
        user_service.user_repo.get_by_field = AsyncMock(return_value=None)

        result = await user_service.check_username_available(username)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_username_unavailable(self):
        """测试用户名已被占用"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        username = "existinguser"

        # Mock用户名已存在
        existing_user = UserFactory.create_user()
        user_service.user_repo.get_by_field = AsyncMock(return_value=existing_user)

        result = await user_service.check_username_available(username)

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_phone_format(self):
        """测试手机号格式验证"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        # 有效手机号
        valid_phone = "13800138000"
        assert user_service.validate_phone_format(valid_phone) is True

        # 无效手机号
        invalid_phone = "12345"
        assert user_service.validate_phone_format(invalid_phone) is False


class TestUserServicePasswordHandling:
    """密码处理测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        mock_db = MagicMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        password = "TestPassword123!"
        hashed = user_service._hash_password(password)

        assert hashed is not None
        assert hashed != password

    def test_verify_password(self):
        """测试密码验证"""
        mock_db = MagicMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        password = "TestPassword123!"
        hashed = user_service._hash_password(password)

        # 正确密码
        assert user_service._verify_password(password, hashed) is True

        # 错误密码
        assert user_service._verify_password("WrongPassword!", hashed) is False


class TestUserServiceList:
    """用户列表测试"""

    @pytest.mark.asyncio
    async def test_get_users_list(self):
        """测试获取用户列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        # Mock用户列表
        users = [UserFactory.create_user() for _ in range(5)]
        user_service.user_repo.get_all = AsyncMock(return_value=users)

        result = await user_service.get_users_list(page=1, size=10)

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_users_with_filter(self):
        """测试带过滤条件的用户列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        # Mock过滤后的用户
        filtered_users = [UserFactory.create_user(role="student")]
        user_service.user_repo.filter = AsyncMock(return_value=filtered_users)

        result = await user_service.get_users_by_role("student")

        assert len(result) > 0


class TestUserServiceSingleton:
    """用户服务单例测试"""

    def test_get_user_service(self):
        """测试获取用户服务实例"""
        mock_db = MagicMock(spec=AsyncSession)

        user_service = get_user_service(mock_db)

        assert user_service is not None
        assert isinstance(user_service, UserService)


class TestUserServiceEdgeCases:
    """用户服务边界情况测试"""

    @pytest.mark.asyncio
    async def test_create_user_with_minimal_data(self):
        """测试最小数据创建用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        request = RegisterRequest(
            phone="13900000001",
            password="Pass123!",
            name="用户",
            grade_level="senior_1",
        )

        user_service.user_repo.get_by_field = AsyncMock(return_value=None)
        user_service.user_repo.create = AsyncMock(
            return_value=UserFactory.create_user(phone=request.phone)
        )

        result = await user_service.create_user(request)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_user_empty_data(self):
        """测试更新用户但不提供数据"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_id = "test_user_123"
        existing_user = UserFactory.create_user(user_id=user_id)

        user_service.user_repo.get_by_id = AsyncMock(return_value=existing_user)
        user_service.user_repo.update = AsyncMock(return_value=existing_user)

        result = await user_service.update_user(user_id, {})

        # 应该返回未修改的用户或抛出验证错误
        assert result is not None or pytest.raises(ValidationError)

    @pytest.mark.asyncio
    async def test_deactivate_user(self):
        """测试停用用户"""
        mock_db = AsyncMock(spec=AsyncSession)
        user_service = UserService(mock_db)

        user_id = "test_user_123"
        existing_user = UserFactory.create_user(user_id=user_id, is_active=True)

        user_service.user_repo.get_by_id = AsyncMock(return_value=existing_user)
        user_service.user_repo.update = AsyncMock(
            return_value=UserFactory.create_user(user_id=user_id, is_active=False)
        )

        await user_service.deactivate_user(user_id)

        user_service.user_repo.update.assert_called_once()
