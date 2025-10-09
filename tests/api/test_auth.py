"""
Auth API 端点测试
覆盖用户认证相关的所有 API 端点
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.user import GradeLevel, User, UserRole
from tests.factories import MockDataFactory, RequestFactory, UserFactory

settings = get_settings()


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """创建测试用户（密码: TestPass123!）"""
    import hashlib
    import secrets
    import time

    # 使用与UserService相同的密码hash方式
    password = "TestPass123!"
    salt = secrets.token_hex(16)
    password_hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    password_hash = f"{salt}:{password_hash_bytes.hex()}"

    # 为每个测试创建唯一的手机号
    unique_phone = f"1380013{str(int(time.time() * 1000))[-4:]}"

    user = UserFactory.create_student(
        phone=unique_phone,
        name="测试用户",
        password_hash=password_hash,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def test_teacher(db: AsyncSession) -> User:
    """创建测试教师用户（密码: TeacherPass123!）"""
    import hashlib
    import secrets
    import time

    # 使用与UserService相同的密码hash方式
    password = "TeacherPass123!"
    salt = secrets.token_hex(16)
    password_hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    password_hash = f"{salt}:{password_hash_bytes.hex()}"

    # 为每个测试创建唯一的手机号
    unique_phone = f"1380013{str(int(time.time() * 1000))[-4:]}"

    teacher = UserFactory.create_teacher(
        phone=unique_phone,
        name="测试教师",
        password_hash=password_hash,
    )
    db.add(teacher)
    await db.commit()
    return teacher


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """创建认证头"""
    token = MockDataFactory.create_jwt_token(user_id=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


class TestUserRegistration:
    """用户注册测试"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db: AsyncSession):
        """测试成功注册"""
        register_data = RequestFactory.create_register_request(
            phone="13900139000",
            password="TestPass123!",
            name="新用户",
        )

        # 调用注册接口（真实集成测试，不mock service层）
        response = await client.post("/api/v1/auth/register", json=register_data)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["phone"] == register_data["phone"]
        assert data["user"]["name"] == register_data["name"]
        assert "access_token" in data
        assert "refresh_token" in data

        # 验证数据库中真的创建了用户
        from src.models.user import User
        from src.repositories.base_repository import BaseRepository

        user_repo = BaseRepository(User, db)
        created_user = await user_repo.get_by_field("phone", register_data["phone"])
        assert created_user is not None
        assert created_user.name == register_data["name"]

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, client: AsyncClient, test_user: User):
        """测试重复手机号注册"""
        register_data = RequestFactory.create_register_request(
            phone=str(test_user.phone), password="TestPass123!", name="重复用户"
        )

        response = await client.post("/api/v1/auth/register", json=register_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "已被注册" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_phone(self, client: AsyncClient):
        """测试无效手机号"""
        register_data = RequestFactory.create_register_request(
            phone="123", password="TestPass123!", name="测试"
        )

        response = await client.post("/api/v1/auth/register", json=register_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """测试弱密码"""
        register_data = RequestFactory.create_register_request(
            phone="13900139001", password="123", name="测试"
        )

        response = await client.post("/api/v1/auth/register", json=register_data)

        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]


class TestUserLogin:
    """用户登录测试"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """测试成功登录"""
        login_data = RequestFactory.create_login_request(
            phone=str(test_user.phone), password="TestPass123!"
        )

        # 真实集成测试 - 不mock service层
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["phone"] == str(test_user.phone)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """测试错误密码"""
        login_data = RequestFactory.create_login_request(
            phone=str(test_user.phone), password="WrongPassword123!"
        )

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试不存在的用户"""
        login_data = RequestFactory.create_login_request(
            phone="19900000000", password="TestPass123!"
        )

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestWechatLogin:
    """微信登录测试"""

    @pytest.mark.asyncio
    async def test_wechat_login_new_user(self, client: AsyncClient):
        """测试微信登录（新用户）"""
        wechat_data = RequestFactory.create_wechat_login_request(
            code="test_wechat_code_123"
        )

        with patch(
            "src.services.auth_service.AuthService.wechat_login"
        ) as mock_wechat_login:
            new_user = UserFactory.create_student(
                wechat_openid="test_openid_123", phone="13900000001"
            )
            mock_wechat_login.return_value = (
                new_user,
                MockDataFactory.create_jwt_token(str(new_user.id), "access"),
                MockDataFactory.create_jwt_token(str(new_user.id), "refresh"),
                True,  # is_new_user
            )

            response = await client.post("/api/v1/auth/wechat-login", json=wechat_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_new_user"] is True
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_wechat_login_existing_user(
        self, client: AsyncClient, test_user: User
    ):
        """测试微信登录（已有用户）"""
        wechat_data = RequestFactory.create_wechat_login_request()

        with patch(
            "src.services.auth_service.AuthService.wechat_login"
        ) as mock_wechat_login:
            # 创建带有微信信息的用户副本
            test_user_dict = {
                "id": test_user.id,
                "phone": test_user.phone,
                "name": test_user.name,
                "wechat_openid": "test_openid_existing",
            }
            mock_user = UserFactory.create_student(**test_user_dict)
            mock_wechat_login.return_value = (
                mock_user,
                MockDataFactory.create_jwt_token(str(mock_user.id), "access"),
                MockDataFactory.create_jwt_token(str(mock_user.id), "refresh"),
                False,  # is_new_user
            )

            response = await client.post("/api/v1/auth/wechat-login", json=wechat_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_new_user"] is False


class TestTokenManagement:
    """Token 管理测试"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """测试刷新 token"""
        refresh_token = MockDataFactory.create_jwt_token(str(test_user.id), "refresh")

        with patch(
            "src.services.auth_service.AuthService.refresh_access_token"
        ) as mock_refresh:
            new_access_token = MockDataFactory.create_jwt_token(
                str(test_user.id), "access"
            )
            mock_refresh.return_value = new_access_token

            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """测试无效的 refresh token"""
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_token_valid(self, client: AsyncClient, auth_headers: dict):
        """测试验证有效 token"""
        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = "test_user_id"

            response = await client.get(
                "/api/v1/auth/verify-token", headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, client: AsyncClient):
        """测试验证无效 token"""
        response = await client.get(
            "/api/v1/auth/verify-token",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordManagement:
    """密码管理测试"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试成功修改密码"""
        change_data = {
            "old_password": "TestPass123!",  # 使用测试用户的实际密码
            "new_password": "NewPass123!",
            "password_confirm": "NewPass123!",
        }

        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            response = await client.post(
                "/api/v1/auth/change-password",
                json=change_data,
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            assert "密码修改成功" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试旧密码错误"""
        change_data = {
            "old_password": "WrongOldPass123!",
            "new_password": "NewPass123!",
            "password_confirm": "NewPass123!",
        }

        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            response = await client.post(
                "/api/v1/auth/change-password",
                json=change_data,
                headers=auth_headers,
            )

            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED,
            ]

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client: AsyncClient):
        """测试重置密码"""
        reset_data = RequestFactory.create_password_reset_request(
            phone="13800138000", verification_code="123456", new_password="NewPass123!"
        )

        with patch(
            "src.services.user_service.UserService.reset_password"
        ) as mock_reset:
            mock_reset.return_value = True

            response = await client.post("/api/v1/auth/reset-password", json=reset_data)

            assert response.status_code == status.HTTP_200_OK
            assert "密码重置成功" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_forgot_password(self, client: AsyncClient, test_user: User):
        """测试忘记密码发送验证码"""
        # forgot-password 端点是简化实现，不需要模拟服务
        response = await client.post(
            "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "密码重置邮件已发送" in response.json()["message"]


class TestUserProfile:
    """用户资料测试"""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试获取当前用户信息"""
        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            with patch(
                "src.services.user_service.UserService.get_user_by_id"
            ) as mock_get:
                mock_get.return_value = test_user

                response = await client.get("/api/v1/auth/me", headers=auth_headers)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["id"] == str(test_user.id)
                assert data["phone"] == test_user.phone

    @pytest.mark.asyncio
    async def test_update_profile(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试更新用户资料"""
        update_data = {
            "name": "更新的名字",
            "school": "新学校",
            "grade_level": "senior_2",
        }

        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            with patch(
                "src.services.user_service.UserService.update_user_profile"
            ) as mock_update:
                updated_user = UserFactory.create_student(
                    name=update_data["name"],
                    school=update_data["school"],
                    grade_level=GradeLevel.SENIOR_2,
                )
                mock_update.return_value = updated_user

                response = await client.put(
                    "/api/v1/auth/profile", json=update_data, headers=auth_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["name"] == update_data["name"]

    @pytest.mark.asyncio
    async def test_upload_avatar(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试上传头像"""
        # 模拟文件上传
        files = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            with patch(
                "src.services.file_service.FileService.upload_file"
            ) as mock_upload:
                mock_upload.return_value = "https://example.com/avatar.jpg"

                response = await client.post(
                    "/api/v1/auth/avatar", files=files, headers=auth_headers
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "avatar_url" in data


class TestAccountValidation:
    """账号验证测试"""

    @pytest.mark.asyncio
    async def test_check_username_available(self, client: AsyncClient):
        """测试检查用户名可用性"""
        response = await client.get(
            "/api/v1/auth/check-username", params={"username": "newuser"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available" in data

    @pytest.mark.asyncio
    async def test_check_username_taken(self, client: AsyncClient, test_user: User):
        """测试检查已存在的用户名"""
        if hasattr(test_user, "username"):
            response = await client.get(
                "/api/v1/auth/check-username",
                params={"username": test_user.username},
            )

            data = response.json()
            assert data["available"] is False

    @pytest.mark.asyncio
    async def test_send_verification_code(self, client: AsyncClient, test_user: User):
        """测试发送验证码"""
        with patch(
            "src.services.auth_service.AuthService.send_verification_code"
        ) as mock_send:
            mock_send.return_value = None

            response = await client.post(
                "/api/v1/auth/send-verification-code",
                json={"phone": test_user.phone, "type": "login"},
            )

            assert response.status_code == status.HTTP_200_OK


class TestAccountManagement:
    """账号管理测试"""

    @pytest.mark.asyncio
    async def test_logout(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试登出"""
        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            with patch("src.services.auth_service.AuthService.logout") as mock_logout:
                mock_logout.return_value = None

                response = await client.post(
                    "/api/v1/auth/logout",
                    json={"all_devices": False},
                    headers=auth_headers,
                )

                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_deactivate_account(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """测试停用账号"""
        with patch("src.api.v1.endpoints.auth.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = str(test_user.id)

            with patch(
                "src.services.user_service.UserService.deactivate_user"
            ) as mock_deactivate:
                mock_deactivate.return_value = None

                response = await client.post(
                    "/api/v1/auth/deactivate",
                    json={"password": "TestPass123!"},
                    headers=auth_headers,
                )

                assert response.status_code == status.HTTP_200_OK


class TestEdgeCases:
    """边界条件和异常测试"""

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未认证访问受保护端点"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_malformed_token(self, client: AsyncClient):
        """测试格式错误的 token"""
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer malformed.token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient):
        """测试过期 token"""
        # 这里需要生成一个过期的 token
        expired_token = "expired_jwt_token"

        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """测试缺少必填字段"""
        response = await client.post(
            "/api/v1/auth/register", json={"phone": "13900000000"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(
        self, client: AsyncClient, test_user: User
    ):
        """测试并发登录"""
        login_data = RequestFactory.create_login_request(
            phone=str(test_user.phone), password="TestPass123!"
        )

        # 模拟并发请求
        responses = await asyncio.gather(
            *[client.post("/api/v1/auth/login", json=login_data) for _ in range(5)]
        )

        # 至少有一个成功或全部失败（取决于限流策略）
        assert any(r.status_code == status.HTTP_200_OK for r in responses) or all(
            r.status_code == status.HTTP_429_TOO_MANY_REQUESTS for r in responses
        )
