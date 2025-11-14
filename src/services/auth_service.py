"""
JWT认证服务
提供token生成、验证、刷新等功能
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from src.core.config import get_settings
from src.core.exceptions import AuthenticationError, ServiceError, ValidationError
from src.models.user import User, UserSession
from src.schemas.auth import LoginResponse, RefreshTokenResponse, UserResponse
from src.services.user_service import UserService

logger = logging.getLogger("auth_service")
settings = get_settings()


class AuthService:
    """JWT认证服务"""

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    # ========== Token生成和验证 ==========

    def create_access_token(
        self, subject: str, jti: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌

        Args:
            subject: 用户ID
            jti: JWT ID
            expires_delta: 过期时间增量

        Returns:
            str: JWT访问令牌
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        payload = {
            "sub": subject,
            "jti": jti,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self, subject: str, jti: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建刷新令牌

        Args:
            subject: 用户ID
            jti: JWT ID
            expires_delta: 过期时间增量

        Returns:
            str: JWT刷新令牌
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.refresh_token_expire_minutes
            )

        payload = {
            "sub": subject,
            "jti": jti,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌

        Returns:
            Dict: 解码后的载荷

        Raises:
            AuthenticationError: 令牌无效或过期
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查必要字段
            if not payload.get("sub") or not payload.get("jti"):
                raise AuthenticationError("令牌格式无效")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("令牌已过期")
        except jwt.InvalidTokenError:
            raise AuthenticationError("令牌无效")
        except Exception as e:
            logger.error(f"令牌验证失败: {str(e)}")
            raise AuthenticationError("令牌验证失败")

    def extract_token_from_header(self, authorization: Optional[str]) -> Optional[str]:
        """
        从Authorization头中提取token

        Args:
            authorization: Authorization头值

        Returns:
            Optional[str]: 提取的token
        """
        if not authorization:
            return None

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None

    # ========== 认证业务逻辑 ==========

    async def authenticate_with_password(
        self,
        phone: str,
        password: str,
        device_type: str = "web",
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False,
    ) -> LoginResponse:
        """
        密码认证登录

        Args:
            phone: 手机号
            password: 密码
            device_type: 设备类型
            device_id: 设备ID
            ip_address: IP地址
            user_agent: 用户代理
            remember_me: 是否记住登录

        Returns:
            LoginResponse: 登录响应

        Raises:
            AuthenticationError: 认证失败
        """
        try:
            # 验证用户凭据
            user = await self.user_service.authenticate_user(phone, password)
            if not user:
                raise AuthenticationError("手机号或密码错误")

            # 创建用户会话
            session = await self.user_service.create_user_session(
                user_id=str(user.id),
                device_type=device_type,
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # 设置token过期时间
            access_expires = timedelta(minutes=self.access_token_expire_minutes)
            refresh_expires = timedelta(minutes=self.refresh_token_expire_minutes)

            if remember_me:
                # 记住登录状态，延长过期时间
                access_expires = timedelta(days=7)
                refresh_expires = timedelta(days=30)

            # 生成JWT令牌
            access_token = self.create_access_token(
                subject=str(user.id),
                jti=str(session.access_token_jti),
                expires_delta=access_expires,
            )

            refresh_token = self.create_refresh_token(
                subject=str(user.id),
                jti=str(session.refresh_token_jti),
                expires_delta=refresh_expires,
            )

            # 构建响应
            # 构建用户响应数据
            # 手动转换UUID为字符串以避免Pydantic验证问题
            user_dict = {
                **{k: v for k, v in user.__dict__.items() if not k.startswith("_")},
                "id": str(user.id),  # 确保ID是字符串
            }
            user_response = UserResponse.model_validate(user_dict)

            response = LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=int(access_expires.total_seconds()),
                user=user_response,
                session_id=str(session.id),
            )

            logger.info(
                f"用户登录成功: user_id={str(user.id)}, phone={phone}, device_type={device_type}"
            )

            return response

        except AuthenticationError:
            logger.warning(f"用户登录失败: 认证错误, phone={phone}")
            raise
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}, phone={phone}", exc_info=True)
            raise ServiceError(f"登录失败: {str(e)}") from e

    async def authenticate_with_wechat(
        self,
        code: str,
        device_type: str = "mini_program",
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_info: Optional[Dict] = None,
    ) -> LoginResponse:
        """
        微信登录认证

        Args:
            code: 微信登录code
            device_type: 设备类型
            device_id: 设备ID
            ip_address: IP地址
            user_agent: 用户代理
            user_info: 用户信息（可选，用于新用户注册）

        Returns:
            LoginResponse: 登录响应

        Raises:
            AuthenticationError: 认证失败
            ServiceError: 服务错误
        """
        try:
            # 导入微信服务
            from src.services.wechat_service import get_wechat_service

            wechat_service = get_wechat_service()

            # 通过code获取openid和session_key
            wechat_data = await wechat_service.code2session(code)
            openid = wechat_data.get("openid")
            unionid = wechat_data.get("unionid")

            if not openid:
                raise AuthenticationError("获取微信openid失败")

            # 查找是否已存在该openid的用户
            user = await self.user_service.get_user_by_wechat_openid(openid)

            if not user:
                # 新用户，创建账号
                logger.info(f"新微信用户注册: openid={openid}")

                # 生成默认用户信息
                nickname = (
                    user_info.get("nickname", "微信用户") if user_info else "微信用户"
                )
                avatar = user_info.get("avatar_url", "") if user_info else ""

                user = await self.user_service.create_wechat_user(
                    openid=openid,
                    unionid=unionid,
                    nickname=nickname,
                    avatar_url=avatar,
                    name=user_info.get("name") if user_info else None,
                    phone=user_info.get("phone") if user_info else None,
                    role=user_info.get("role", "student") if user_info else "student",
                )

            # 创建用户会话
            session = await self.user_service.create_user_session(
                user_id=str(user.id),
                device_type=device_type,
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # 生成JWT令牌
            access_expires = timedelta(minutes=self.access_token_expire_minutes)
            refresh_expires = timedelta(minutes=self.refresh_token_expire_minutes)

            access_token = self.create_access_token(
                subject=str(user.id),
                jti=str(session.access_token_jti),
                expires_delta=access_expires,
            )

            refresh_token = self.create_refresh_token(
                subject=str(user.id),
                jti=str(session.refresh_token_jti),
                expires_delta=refresh_expires,
            )

            # 构建响应
            # 手动转换UUID为字符串
            user_dict = {
                **{k: v for k, v in user.__dict__.items() if not k.startswith("_")},
                "id": str(user.id),
            }
            user_response = UserResponse.model_validate(user_dict)

            response = LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=int(access_expires.total_seconds()),
                user=user_response,
                session_id=str(session.id),
            )

            logger.info(
                f"微信登录成功: user_id={str(user.id)}, openid={openid}, device_type={device_type}"
            )

            return response

        except AuthenticationError:
            logger.warning(f"微信登录失败: 认证错误, code={code[:10]}...")
            raise
        except Exception as e:
            logger.error(f"微信登录失败: {str(e)}, code={code[:10]}...", exc_info=True)
            raise ServiceError(f"微信登录失败: {str(e)}") from e

    async def refresh_access_token(
        self, refresh_token: str, device_type: str = "web"
    ) -> RefreshTokenResponse:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌
            device_type: 设备类型

        Returns:
            RefreshTokenResponse: 刷新令牌响应

        Raises:
            AuthenticationError: 刷新失败
        """
        try:
            # 验证刷新令牌
            payload = self.verify_token(refresh_token)

            if payload.get("type") != "refresh":
                raise AuthenticationError("令牌类型错误")

            user_id = payload.get("sub")
            jti = payload.get("jti")

            if not user_id or not jti:
                raise AuthenticationError("令牌格式错误")

            # 检查会话是否存在且未撤销
            session = await self.user_service.session_repo.get_by_field(
                "refresh_token_jti", jti
            )

            if not session or getattr(session, "is_revoked", True):
                raise AuthenticationError("会话已失效")

            if str(getattr(session, "user_id", "")) != str(user_id):
                raise AuthenticationError("令牌用户不匹配")

            # 获取用户信息
            user = await self.user_service.get_user_by_id(user_id)
            if not user:
                raise AuthenticationError("用户不存在")

            # 生成新的访问令牌
            access_token = self.create_access_token(
                subject=str(user_id),
                jti=str(getattr(session, "access_token_jti", "")),
                expires_delta=timedelta(minutes=self.access_token_expire_minutes),
            )

            # 构建用户信息响应
            from src.schemas.auth import UserResponse

            user_info = UserResponse(
                id=str(user.id),
                phone=user.phone,
                name=user.name,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                role=user.role,
                school=user.school,
                grade_level=user.grade_level,
                class_name=user.class_name,
                institution=user.institution,
                parent_contact=user.parent_contact,
                parent_name=user.parent_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                notification_enabled=getattr(user, "notification_enabled", True),
                last_login_at=getattr(user, "last_login_at", None),
                login_count=getattr(user, "login_count", 0),
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            response = RefreshTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # 刷新令牌保持不变
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                session_id=str(session.id),
                user=user_info,
            )

            logger.info(f"令牌刷新成功: user_id={user_id}, device_type={device_type}")
            return response

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"令牌刷新失败: {str(e)}", exc_info=True)
            raise AuthenticationError(f"令牌刷新失败: {str(e)}") from e

    async def logout_user(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        logout_all_devices: bool = False,
    ) -> bool:
        """
        用户登出

        Args:
            user_id: 用户ID
            session_id: 会话ID
            logout_all_devices: 是否登出所有设备

        Returns:
            bool: 是否成功
        """
        try:
            if logout_all_devices:
                # 撤销所有会话
                revoked_count = await self.user_service.revoke_all_user_sessions(
                    user_id
                )
                logger.info(
                    f"用户登出所有设备: user_id={user_id}, count={revoked_count}"
                )
                return revoked_count > 0
            elif session_id:
                # 撤销指定会话
                success = await self.user_service.revoke_user_session(
                    session_id, user_id
                )
                if success:
                    logger.info(
                        f"用户登出成功: user_id={user_id}, session_id={session_id}"
                    )
                return success
            else:
                logger.warning(f"登出参数不足: user_id={user_id}")
                return False

        except Exception as e:
            logger.error(f"用户登出失败: {str(e)}, user_id={user_id}", exc_info=True)
            return False

    async def verify_user_session(self, jti: str) -> Optional[UserSession]:
        """
        验证用户会话

        Args:
            jti: JWT ID

        Returns:
            Optional[UserSession]: 用户会话
        """
        try:
            session = await self.user_service.get_user_session(jti)

            if not session:
                return None

            if getattr(session, "is_revoked", True):
                return None

            # 检查是否过期
            expires_at = getattr(session, "expires_at", None)
            if expires_at:
                expire_time = datetime.fromisoformat(str(expires_at))
                if expire_time < datetime.utcnow():
                    # 会话已过期，标记为撤销
                    await self.user_service.session_repo.update(
                        str(getattr(session, "id", "")), {"is_revoked": True}
                    )
                    return None

            return session

        except Exception as e:
            logger.error(f"会话验证失败: {str(e)}, jti={jti[:8]}", exc_info=True)
            return None

    # ========== 权限验证 ==========

    async def check_user_permission(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """
        检查用户权限

        Args:
            user_id: 用户ID
            resource: 资源
            action: 操作

        Returns:
            bool: 是否有权限
        """
        try:
            user = await self.user_service.get_user_by_id(user_id)
            if not user:
                return False

            # 简化的权限检查逻辑 - 所有用户都是学生角色
            if user.role == "admin":
                return True

            # 学生角色的基础权限（所有用户都是学生）
            student_permissions = {
                "learning": ["ask", "view"],
                "homework": ["submit", "view"],
                "profile": ["view", "update"],
                "mistakes": ["view", "create", "update", "delete"],  # 错题本权限
                "analytics": ["view"],  # 查看学习报告
            }

            resource_perms = student_permissions.get(resource, [])
            return action in resource_perms

        except Exception as e:
            logger.error(
                f"权限检查失败: {str(e)}, user_id={user_id}, resource={resource}, action={action}"
            )
            return False

    def require_permission(self, resource: str, action: str):
        """
        权限装饰器

        Args:
            resource: 资源
            action: 操作

        Returns:
            装饰器函数
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 这里需要从请求中获取用户信息
                # 实际使用时会与FastAPI依赖注入结合
                user_id = kwargs.get("current_user_id")
                if not user_id:
                    raise AuthenticationError("用户未认证")

                has_permission = await self.check_user_permission(
                    user_id, resource, action
                )
                if not has_permission:
                    raise AuthenticationError("权限不足")

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    # ========== 安全工具 ==========

    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)

    def generate_jti(self) -> str:
        """生成JWT ID"""
        return secrets.token_hex(16)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希（委托给用户服务）"""
        return self.user_service._hash_password(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码（委托给用户服务）"""
        return self.user_service._verify_password(password, hashed_password)


# 依赖注入函数
def get_auth_service(user_service: UserService) -> AuthService:
    """获取认证服务实例"""
    return AuthService(user_service)
