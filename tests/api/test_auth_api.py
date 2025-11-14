"""
认证API端点测试
测试用户注册、登录、登出、token管理等认证功能
"""

from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from tests.factories import UserFactory, RequestFactory, MockDataFactory


class TestRegisterAPI:
    """用户注册API测试"""

    def test_register_success(self, test_client: TestClient):
        """测试成功注册"""
        register_data = RequestFactory.create_register_request(
            phone="13900000001",
            password="TestPass123!",
            name="新用户"
        )
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_user = AsyncMock(return_value=UserFactory.create_user(
                phone=register_data["phone"],
                name=register_data["name"]
            ))
            mock_service.return_value = mock_instance
            
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
                mock_auth_instance = MagicMock()
                mock_auth_instance.create_tokens = MagicMock(return_value={
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token"
                })
                mock_auth_instance.create_user_session = AsyncMock()
                mock_auth.return_value = mock_auth_instance
                
                response = test_client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_duplicate_phone(self, test_client: TestClient):
        """测试重复手机号注册"""
        register_data = RequestFactory.create_register_request(
            phone="13800138000"  # 已存在的手机号
        )
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_service:
            from src.core.exceptions import ConflictError
            mock_instance = MagicMock()
            mock_instance.create_user = AsyncMock(side_effect=ConflictError("手机号已存在"))
            mock_service.return_value = mock_instance
            
            response = test_client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 409

    def test_register_invalid_phone(self, test_client: TestClient):
        """测试无效手机号"""
        register_data = RequestFactory.create_register_request(
            phone="12345"  # 无效手机号
        )
        
        response = test_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, test_client: TestClient):
        """测试弱密码"""
        register_data = RequestFactory.create_register_request(
            password="123"  # 弱密码
        )
        
        response = test_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 422  # Validation error


class TestLoginAPI:
    """用户登录API测试"""

    def test_login_success(self, test_client: TestClient):
        """测试成功登录"""
        login_data = RequestFactory.create_login_request()
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_user_by_phone = AsyncMock(return_value=UserFactory.create_user())
            mock_service.return_value = mock_instance
            
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
                mock_auth_instance = MagicMock()
                mock_auth_instance.verify_password = MagicMock(return_value=True)
                mock_auth_instance.create_tokens = MagicMock(return_value={
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token"
                })
                mock_auth_instance.create_user_session = AsyncMock()
                mock_auth.return_value = mock_auth_instance
                
                response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, test_client: TestClient):
        """测试错误密码"""
        login_data = RequestFactory.create_login_request(password="WrongPass123!")
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_user_by_phone = AsyncMock(return_value=UserFactory.create_user())
            mock_service.return_value = mock_instance
            
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
                mock_auth_instance = MagicMock()
                mock_auth_instance.verify_password = MagicMock(return_value=False)
                mock_auth.return_value = mock_auth_instance
                
                response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401

    def test_login_user_not_found(self, test_client: TestClient):
        """测试用户不存在"""
        login_data = RequestFactory.create_login_request(phone="13900000099")
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_user_by_phone = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance
            
            response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401


class TestWechatLoginAPI:
    """微信登录API测试"""

    def test_wechat_login_new_user(self, test_client: TestClient):
        """测试微信登录-新用户"""
        wechat_data = RequestFactory.create_wechat_login_request()
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user_service:
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth_service:
                # Mock微信服务
                with patch("src.services.wechat_service.WechatService.code_to_session") as mock_wechat:
                    mock_wechat.return_value = MockDataFactory.create_wechat_session_response()
                    
                    # Mock用户服务
                    mock_user_instance = MagicMock()
                    mock_user_instance.get_user_by_wechat_openid = AsyncMock(return_value=None)
                    mock_user_instance.create_wechat_user = AsyncMock(
                        return_value=UserFactory.create_user(wechat_openid="test_openid_123")
                    )
                    mock_user_service.return_value = mock_user_instance
                    
                    # Mock认证服务
                    mock_auth_instance = MagicMock()
                    mock_auth_instance.create_tokens = MagicMock(return_value={
                        "access_token": "test_access_token",
                        "refresh_token": "test_refresh_token"
                    })
                    mock_auth_instance.create_user_session = AsyncMock()
                    mock_auth_service.return_value = mock_auth_instance
                    
                    response = test_client.post("/api/v1/auth/wechat-login", json=wechat_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_wechat_login_existing_user(self, test_client: TestClient):
        """测试微信登录-已存在用户"""
        wechat_data = RequestFactory.create_wechat_login_request()
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user_service:
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth_service:
                with patch("src.services.wechat_service.WechatService.code_to_session") as mock_wechat:
                    mock_wechat.return_value = MockDataFactory.create_wechat_session_response()
                    
                    # Mock用户服务 - 返回已存在用户
                    mock_user_instance = MagicMock()
                    mock_user_instance.get_user_by_wechat_openid = AsyncMock(
                        return_value=UserFactory.create_user(wechat_openid="test_openid_123")
                    )
                    mock_user_service.return_value = mock_user_instance
                    
                    # Mock认证服务
                    mock_auth_instance = MagicMock()
                    mock_auth_instance.create_tokens = MagicMock(return_value={
                        "access_token": "test_access_token",
                        "refresh_token": "test_refresh_token"
                    })
                    mock_auth_instance.create_user_session = AsyncMock()
                    mock_auth_service.return_value = mock_auth_instance
                    
                    response = test_client.post("/api/v1/auth/wechat-login", json=wechat_data)
        
        assert response.status_code == 200

    def test_wechat_login_invalid_code(self, test_client: TestClient):
        """测试微信登录-无效code"""
        wechat_data = RequestFactory.create_wechat_login_request(code="invalid_code")
        
        with patch("src.services.wechat_service.WechatService.code_to_session") as mock_wechat:
            from src.core.exceptions import ValidationError
            mock_wechat.side_effect = ValidationError("无效的微信code")
            
            response = test_client.post("/api/v1/auth/wechat-login", json=wechat_data)
        
        assert response.status_code == 400


class TestTokenManagement:
    """Token管理API测试"""

    def test_refresh_token_success(self, test_client: TestClient):
        """测试刷新token成功"""
        refresh_data = {"refresh_token": "valid_refresh_token"}
        
        with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
            mock_instance = MagicMock()
            mock_instance.verify_token = MagicMock(return_value={
                "sub": "test_user_123",
                "type": "refresh",
                "jti": "session_123"
            })
            mock_instance.verify_user_session = AsyncMock(return_value=MagicMock())
            mock_instance.create_tokens = MagicMock(return_value={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            })
            mock_instance.invalidate_session = AsyncMock()
            mock_instance.create_user_session = AsyncMock()
            mock_auth.return_value = mock_instance
            
            response = test_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, test_client: TestClient):
        """测试无效refresh token"""
        refresh_data = {"refresh_token": "invalid_token"}
        
        with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
            from src.core.exceptions import AuthenticationError
            mock_instance = MagicMock()
            mock_instance.verify_token = MagicMock(side_effect=AuthenticationError("无效token"))
            mock_auth.return_value = mock_instance
            
            response = test_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401

    def test_verify_token_success(self, test_client: TestClient):
        """测试验证token成功"""
        with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
            mock_instance = MagicMock()
            mock_instance.verify_token = MagicMock(return_value={
                "sub": "test_user_123",
                "type": "access"
            })
            mock_auth.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/auth/verify-token",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200


class TestLogout:
    """登出API测试"""

    def test_logout_success(self, test_client: TestClient):
        """测试成功登出"""
        logout_data = {"all_devices": False}
        
        with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
            mock_instance = MagicMock()
            mock_instance.verify_token = MagicMock(return_value={
                "jti": "session_123"
            })
            mock_instance.invalidate_session = AsyncMock()
            mock_auth.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/auth/logout",
                json=logout_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200

    def test_logout_all_devices(self, test_client: TestClient):
        """测试登出所有设备"""
        logout_data = {"all_devices": True}
        
        with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
            mock_instance = MagicMock()
            mock_instance.verify_token = MagicMock(return_value={
                "sub": "test_user_123",
                "jti": "session_123"
            })
            mock_instance.invalidate_all_user_sessions = AsyncMock()
            mock_auth.return_value = mock_instance
            
            response = test_client.post(
                "/api/v1/auth/logout",
                json=logout_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200


class TestPasswordManagement:
    """密码管理API测试"""

    def test_change_password_success(self, test_client: TestClient):
        """测试成功修改密码"""
        password_data = {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!"
        }
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
                mock_user_instance = MagicMock()
                mock_user_instance.get_user_by_id = AsyncMock(
                    return_value=UserFactory.create_user()
                )
                mock_user_instance.update_password = AsyncMock()
                mock_user.return_value = mock_user_instance
                
                mock_auth_instance = MagicMock()
                mock_auth_instance.verify_password = MagicMock(return_value=True)
                mock_auth_instance.hash_password = MagicMock(return_value="new_hashed_password")
                mock_auth.return_value = mock_auth_instance
                
                response = test_client.post(
                    "/api/v1/auth/change-password",
                    json=password_data,
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == 200

    def test_change_password_wrong_old_password(self, test_client: TestClient):
        """测试旧密码错误"""
        password_data = {
            "old_password": "WrongOldPass!",
            "new_password": "NewPass123!"
        }
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            with patch("src.api.v1.endpoints.auth.get_auth_service") as mock_auth:
                mock_user_instance = MagicMock()
                mock_user_instance.get_user_by_id = AsyncMock(
                    return_value=UserFactory.create_user()
                )
                mock_user.return_value = mock_user_instance
                
                mock_auth_instance = MagicMock()
                mock_auth_instance.verify_password = MagicMock(return_value=False)
                mock_auth.return_value = mock_auth_instance
                
                response = test_client.post(
                    "/api/v1/auth/change-password",
                    json=password_data,
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == 401


class TestUserProfile:
    """用户资料API测试"""

    def test_get_current_user_info(self, test_client: TestClient):
        """测试获取当前用户信息"""
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            mock_instance = MagicMock()
            test_user = UserFactory.create_user()
            mock_instance.get_user_by_id = AsyncMock(return_value=test_user)
            mock_user.return_value = mock_instance
            
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_update_profile(self, test_client: TestClient):
        """测试更新用户资料"""
        profile_data = {
            "name": "更新后的姓名",
            "email": "newemail@example.com"
        }
        
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            mock_instance = MagicMock()
            updated_user = UserFactory.create_user(**profile_data)
            mock_instance.update_user = AsyncMock(return_value=updated_user)
            mock_user.return_value = mock_instance
            
            response = test_client.put(
                "/api/v1/auth/profile",
                json=profile_data,
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == 200


class TestAccountValidation:
    """账号验证API测试"""

    def test_check_username_available(self, test_client: TestClient):
        """测试检查用户名可用性"""
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            mock_instance = MagicMock()
            mock_instance.get_user_by_username = AsyncMock(return_value=None)
            mock_user.return_value = mock_instance
            
            response = test_client.get("/api/v1/auth/check-username?username=newuser")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("available") is True

    def test_check_username_unavailable(self, test_client: TestClient):
        """测试用户名已被占用"""
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            mock_instance = MagicMock()
            mock_instance.get_user_by_username = AsyncMock(
                return_value=UserFactory.create_user()
            )
            mock_user.return_value = mock_instance
            
            response = test_client.get("/api/v1/auth/check-username?username=existinguser")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("available") is False

    def test_check_email_available(self, test_client: TestClient):
        """测试检查邮箱可用性"""
        with patch("src.api.v1.endpoints.auth.get_user_service") as mock_user:
            mock_instance = MagicMock()
            mock_instance.get_user_by_email = AsyncMock(return_value=None)
            mock_user.return_value = mock_instance
            
            response = test_client.get("/api/v1/auth/check-email?email=new@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("available") is True
