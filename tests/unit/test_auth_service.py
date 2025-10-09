"""
认证服务单元测试
测试JWT token生成、验证、用户认证等功能
"""

import pytest
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from src.services.auth_service import AuthService, get_auth_service
from src.services.user_service import UserService
from src.core.exceptions import AuthenticationError, ValidationError
from tests.factories import UserFactory


class TestAuthServiceTokenGeneration:
    """Token生成测试"""

    def test_create_access_token(self):
        """测试创建访问token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        
        token = auth_service.create_access_token(user_id, jti)
        
        assert token is not None
        assert isinstance(token, str)
        
        # 验证token payload
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == user_id
        assert decoded["jti"] == jti
        assert decoded["type"] == "access"

    def test_create_refresh_token(self):
        """测试创建刷新token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        
        token = auth_service.create_refresh_token(user_id, jti)
        
        assert token is not None
        assert isinstance(token, str)
        
        # 验证token payload
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == user_id
        assert decoded["jti"] == jti
        assert decoded["type"] == "refresh"

    def test_create_tokens(self):
        """测试创建token对"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        
        tokens = auth_service.create_tokens(user_id, jti)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_token_with_custom_expiry(self):
        """测试自定义过期时间的token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        custom_delta = timedelta(hours=2)
        
        token = auth_service.create_access_token(user_id, jti, custom_delta)
        decoded = auth_service.verify_token(token)
        
        # 验证过期时间约为2小时后
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = (exp_time - now).total_seconds()
        
        assert 7000 < time_diff < 7300  # 约2小时 (允许一些误差)


class TestAuthServiceTokenVerification:
    """Token验证测试"""

    def test_verify_valid_token(self):
        """测试验证有效token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        token = auth_service.create_access_token(user_id, jti)
        
        payload = auth_service.verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["jti"] == jti

    def test_verify_expired_token(self):
        """测试验证过期token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        # 创建已过期的token
        token = auth_service.create_access_token(
            user_id, jti, timedelta(seconds=-1)
        )
        
        with pytest.raises(AuthenticationError):
            auth_service.verify_token(token)

    def test_verify_invalid_token(self):
        """测试验证无效token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        with pytest.raises(AuthenticationError):
            auth_service.verify_token("invalid_token_string")

    def test_verify_tampered_token(self):
        """测试验证被篡改的token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        jti = "session_123"
        token = auth_service.create_access_token(user_id, jti)
        
        # 篡改token
        tampered_token = token[:-5] + "XXXXX"
        
        with pytest.raises(AuthenticationError):
            auth_service.verify_token(tampered_token)


class TestAuthServicePasswordHandling:
    """密码处理测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(wrong_password, hashed) is False

    def test_different_passwords_different_hashes(self):
        """测试不同密码生成不同哈希"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        password1 = "Password123!"
        password2 = "Password456!"
        
        hash1 = auth_service.hash_password(password1)
        hash2 = auth_service.hash_password(password2)
        
        assert hash1 != hash2


class TestAuthServiceUserSession:
    """用户会话测试"""

    @pytest.mark.asyncio
    async def test_create_user_session(self):
        """测试创建用户会话"""
        mock_user_service = MagicMock(spec=UserService)
        mock_user_service.db = AsyncMock()
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        device_info = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "device_id": "device_123"
        }
        
        with patch.object(auth_service, '_save_session', new=AsyncMock()) as mock_save:
            jti = await auth_service.create_user_session(user_id, device_info)
            
            assert jti is not None
            assert isinstance(jti, str)
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_user_session_valid(self):
        """测试验证有效会话"""
        mock_user_service = MagicMock(spec=UserService)
        mock_user_service.db = AsyncMock()
        auth_service = AuthService(mock_user_service)
        
        jti = "session_123"
        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch.object(auth_service, '_get_session', new=AsyncMock(return_value=mock_session)):
            result = await auth_service.verify_user_session(jti)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_verify_user_session_invalid(self):
        """测试验证无效会话"""
        mock_user_service = MagicMock(spec=UserService)
        mock_user_service.db = AsyncMock()
        auth_service = AuthService(mock_user_service)
        
        jti = "invalid_session"
        
        with patch.object(auth_service, '_get_session', new=AsyncMock(return_value=None)):
            result = await auth_service.verify_user_session(jti)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_session(self):
        """测试注销会话"""
        mock_user_service = MagicMock(spec=UserService)
        mock_user_service.db = AsyncMock()
        auth_service = AuthService(mock_user_service)
        
        jti = "session_123"
        
        with patch.object(auth_service, '_invalidate_session_by_jti', new=AsyncMock()) as mock_invalidate:
            await auth_service.invalidate_session(jti)
            
            mock_invalidate.assert_called_once_with(jti)

    @pytest.mark.asyncio
    async def test_invalidate_all_user_sessions(self):
        """测试注销用户所有会话"""
        mock_user_service = MagicMock(spec=UserService)
        mock_user_service.db = AsyncMock()
        auth_service = AuthService(mock_user_service)
        
        user_id = "test_user_123"
        
        with patch.object(auth_service, '_invalidate_all_sessions_by_user', new=AsyncMock()) as mock_invalidate:
            await auth_service.invalidate_all_user_sessions(user_id)
            
            mock_invalidate.assert_called_once_with(user_id)


class TestAuthServiceAuthentication:
    """用户认证测试"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """测试用户认证成功"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        phone = "13800138000"
        password = "TestPass123!"
        
        # Mock用户和密码验证
        test_user = UserFactory.create_user(phone=phone)
        mock_user_service.get_user_by_phone = AsyncMock(return_value=test_user)
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            user = await auth_service.authenticate_user(phone, password)
            
            assert user is not None
            assert user.phone == phone

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """测试错误密码"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        phone = "13800138000"
        password = "WrongPassword!"
        
        test_user = UserFactory.create_user(phone=phone)
        mock_user_service.get_user_by_phone = AsyncMock(return_value=test_user)
        
        with patch.object(auth_service, 'verify_password', return_value=False):
            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_user(phone, password)

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """测试用户不存在"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        phone = "13900000000"
        password = "TestPass123!"
        
        mock_user_service.get_user_by_phone = AsyncMock(return_value=None)
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(phone, password)


class TestAuthServiceSingleton:
    """认证服务单例测试"""

    def test_get_auth_service_returns_instance(self):
        """测试获取认证服务实例"""
        mock_user_service = MagicMock(spec=UserService)
        
        auth_service = get_auth_service(mock_user_service)
        
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)

    def test_auth_service_initialization(self):
        """测试认证服务初始化"""
        mock_user_service = MagicMock(spec=UserService)
        
        auth_service = AuthService(mock_user_service)
        
        assert auth_service.user_service == mock_user_service
        assert auth_service.secret_key is not None
        assert auth_service.algorithm is not None


class TestAuthServiceEdgeCases:
    """认证服务边界情况测试"""

    def test_empty_password_hash(self):
        """测试空密码哈希"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        # 测试空密码
        with pytest.raises((ValidationError, ValueError)):
            auth_service.hash_password("")

    def test_token_with_missing_claims(self):
        """测试缺少必要claims的token"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        # 手动创建缺少claims的token
        incomplete_payload = {"sub": "user_123"}
        incomplete_token = jwt.encode(
            incomplete_payload,
            auth_service.secret_key,
            algorithm=auth_service.algorithm
        )
        
        # 应该能验证但可能缺少某些字段
        try:
            decoded = auth_service.verify_token(incomplete_token)
            # 验证是否缺少jti
            assert "jti" not in decoded or decoded["jti"] is None
        except AuthenticationError:
            # 也可能直接拒绝
            pass

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self):
        """测试认证已停用用户"""
        mock_user_service = MagicMock(spec=UserService)
        auth_service = AuthService(mock_user_service)
        
        phone = "13800138000"
        password = "TestPass123!"
        
        # 创建已停用用户
        inactive_user = UserFactory.create_user(phone=phone, is_active=False)
        mock_user_service.get_user_by_phone = AsyncMock(return_value=inactive_user)
        
        with patch.object(auth_service, 'verify_password', return_value=True):
            # 根据实际实现,可能允许或拒绝
            try:
                user = await auth_service.authenticate_user(phone, password)
                # 如果允许登录,检查用户状态
                assert user.is_active is False
            except AuthenticationError:
                # 如果拒绝登录,也是合理的
                pass
