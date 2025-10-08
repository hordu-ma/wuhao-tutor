"""
用户管理服务
提供用户注册、登录、资料管理等功能
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import get_settings
from src.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from src.models.user import GradeLevel, User, UserRole, UserSession
from src.repositories.base_repository import BaseRepository
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
)
from src.schemas.user import (
    AddLearningGoalRequest,
    PaginatedResponse,
    UpdateStudyPreferencesRequest,
    UpdateUserRequest,
    UserActivityResponse,
    UserDetailResponse,
    UserListQuery,
    UserProgressResponse,
    UserResponse,
)
from src.utils.cache import cache_key, cache_result
from src.utils.type_converters import (
    build_user_response_data,
    extract_orm_bool,
    extract_orm_int,
    extract_orm_str,
    extract_orm_uuid_str,
    safe_json_loads,
    wrap_orm,
)

logger = logging.getLogger("user_service")
settings = get_settings()


class UserService:
    """用户管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = BaseRepository(User, db)
        self.session_repo = BaseRepository(UserSession, db)

    # ========== 用户基础管理 ==========

    async def create_user(self, request: RegisterRequest) -> UserResponse:
        """创建新用户"""
        try:
            # 检查手机号是否已存在
            existing_user = await self.user_repo.get_by_field("phone", request.phone)
            if existing_user:
                raise ConflictError("该手机号已被注册")

            # 创建用户数据
            password_hash = self._hash_password(request.password)

            user_data = {
                "phone": request.phone,
                "password_hash": password_hash,
                "name": request.name,
                "nickname": request.nickname,
                "avatar_url": request.avatar_url,
                "school": request.school,
                "grade_level": (
                    request.grade_level.value if request.grade_level else None
                ),
                "class_name": request.class_name,
                "institution": request.institution,
                "parent_contact": request.parent_contact,
                "parent_name": request.parent_name,
                "role": request.role.value,
                "is_active": True,
                "is_verified": True,  # 注册时假设已验证
                "login_count": 0,
            }

            user = await self.user_repo.create(user_data)

            logger.info(
                "用户注册成功",
                extra={
                    "user_id": extract_orm_uuid_str(user, "id"),
                    "phone": request.phone,
                    "name": request.name,
                },
            )

            return UserResponse.model_validate(user)

        except ConflictError:
            raise
        except Exception as e:
            logger.error(
                f"用户注册失败: {str(e)}", extra={"phone": request.phone}, exc_info=True
            )
            raise ServiceError(f"用户注册失败: {str(e)}") from e

    async def authenticate_user(self, phone: str, password: str) -> Optional[User]:
        """用户身份验证"""
        try:
            user = await self.user_repo.get_by_field("phone", phone)
            if not user:
                return None

            if not extract_orm_bool(user, "is_active"):
                raise AuthenticationError("用户账号已被禁用")

            if not self._verify_password(
                password, extract_orm_str(user, "password_hash")
            ):
                return None

            # 更新登录信息 - 暂时注释掉以绕过数据库错误
            # current_login_count = extract_orm_int(user, "login_count", 0) or 0
            # await self.user_repo.update(extract_orm_uuid_str(user, "id"), {
            #     "last_login_at": datetime.utcnow().isoformat(),
            #     "login_count": current_login_count + 1
            # })

            return user

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(
                f"用户认证失败: {str(e)}", extra={"phone": phone}, exc_info=True
            )
            return None

    async def get_user_by_wechat_openid(self, openid: str) -> Optional[User]:
        """根据微信openid获取用户"""
        try:
            result = await self.db.execute(
                select(User).where(User.wechat_openid == openid)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"根据openid查找用户失败: {str(e)}", exc_info=True)
            return None

    async def create_wechat_user(
        self,
        openid: str,
        unionid: Optional[str] = None,
        nickname: str = "微信用户",
        avatar_url: str = "",
        name: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "student",
    ) -> User:
        """创建微信用户"""
        try:
            # 检查openid是否已存在
            existing_user = await self.get_user_by_wechat_openid(openid)
            if existing_user:
                raise ConflictError("该微信账号已绑定其他用户")

            # 如果提供了手机号，检查是否已被注册
            if phone:
                existing_phone_user = await self.user_repo.get_by_field("phone", phone)
                if existing_phone_user:
                    # 绑定微信到现有账号
                    await self.user_repo.update(
                        extract_orm_uuid_str(existing_phone_user, "id"),
                        {
                            "wechat_openid": openid,
                            "wechat_unionid": unionid,
                            "nickname": nickname
                            or extract_orm_str(existing_phone_user, "nickname"),
                            "avatar_url": avatar_url
                            or extract_orm_str(existing_phone_user, "avatar_url"),
                        },
                    )
                    return existing_phone_user

            # 创建新用户
            user_data = {
                "phone": phone,  # 可能为None，后续可补充
                "password_hash": "",  # 微信用户无密码
                "name": name or nickname,
                "nickname": nickname,
                "avatar_url": avatar_url,
                "wechat_openid": openid,
                "wechat_unionid": unionid,
                "role": role,
                "is_active": True,
                "is_verified": True,  # 微信登录默认已验证
                "login_count": 0,
            }

            user = await self.user_repo.create(user_data)

            logger.info(
                "微信用户创建成功",
                extra={
                    "user_id": extract_orm_uuid_str(user, "id"),
                    "openid": openid,
                    "nickname": nickname,
                },
            )

            return user

        except ConflictError:
            raise
        except Exception as e:
            logger.error(
                f"创建微信用户失败: {str(e)}", extra={"openid": openid}, exc_info=True
            )
            raise ServiceError(f"创建微信用户失败: {str(e)}") from e

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户信息"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def get_user_detail(self, user_id: str) -> Optional[UserDetailResponse]:
        """获取用户详细信息"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # 解析学习偏好和目标
        study_subjects = []
        study_goals = []
        study_preferences = None

        study_subjects_str = extract_orm_str(user, "study_subjects")
        if study_subjects_str:
            try:
                import json

                study_subjects = json.loads(study_subjects_str)
            except:
                pass

        study_goals_str = extract_orm_str(user, "study_goals")
        if study_goals_str:
            try:
                import json

                study_goals = json.loads(study_goals_str)
            except:
                pass

        # 构建详细响应
        user_detail = UserDetailResponse.model_validate(user)
        user_detail.study_subjects = study_subjects
        user_detail.study_goals = study_goals
        user_detail.study_preferences = study_preferences

        return user_detail

    async def update_user(
        self, user_id: str, request: UpdateUserRequest
    ) -> UserResponse:
        """更新用户信息"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 构建更新数据
        update_data = {}
        for field, value in request.model_dump(exclude_unset=True).items():
            if hasattr(user, field):
                if field == "grade_level" and value:
                    update_data[field] = (
                        value.value if hasattr(value, "value") else value
                    )
                else:
                    update_data[field] = value

        if update_data:
            await self.user_repo.update(user_id, update_data)
            user = await self.user_repo.get_by_id(user_id)

        logger.info(
            "用户信息更新成功",
            extra={"user_id": user_id, "fields": list(update_data.keys())},
        )
        return UserResponse.model_validate(user)

    async def update_study_preferences(
        self, user_id: str, request: UpdateStudyPreferencesRequest
    ) -> bool:
        """更新学习偏好"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        import json

        # 更新学习学科
        if request.subjects is not None:
            subjects_data = [
                s.value if hasattr(s, "value") else s for s in request.subjects
            ]
            await self.user_repo.update(
                user_id, {"study_subjects": json.dumps(subjects_data)}
            )

        # 这里可以扩展更多学习偏好字段的更新
        logger.info("用户学习偏好更新成功", extra={"user_id": user_id})
        return True

    async def add_learning_goal(
        self, user_id: str, request: AddLearningGoalRequest
    ) -> bool:
        """添加学习目标"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        import json

        # 获取现有目标
        existing_goals = []
        study_goals_str = extract_orm_str(user, "study_goals")
        if study_goals_str:
            try:
                existing_goals = json.loads(study_goals_str)
            except:
                existing_goals = []

        # 添加新目标
        new_goal = request.model_dump()
        if hasattr(request.goal_type, "value") and request.goal_type is not None:
            new_goal["goal_type"] = request.goal_type.value
        if hasattr(request.subject, "value") and request.subject is not None:
            new_goal["subject"] = request.subject.value

        new_goal["id"] = secrets.token_hex(8)
        new_goal["created_at"] = datetime.utcnow().isoformat()
        new_goal["is_completed"] = False

        existing_goals.append(new_goal)

        # 更新数据库
        await self.user_repo.update(
            user_id, {"study_goals": json.dumps(existing_goals)}
        )

        logger.info(
            "学习目标添加成功",
            extra={"user_id": user_id, "goal_type": str(request.goal_type)},
        )
        return True

    # ========== 用户查询和统计 ==========

    async def get_user_list(self, query: UserListQuery) -> Dict[str, Any]:
        """获取用户列表"""
        # 构建查询条件
        conditions = []

        if query.role:
            conditions.append(User.role == query.role.value)

        if query.is_active is not None:
            conditions.append(User.is_active == query.is_active)

        if query.is_verified is not None:
            conditions.append(User.is_verified == query.is_verified)

        if query.school:
            conditions.append(User.school.contains(query.school))

        if query.grade_level:
            conditions.append(User.grade_level == query.grade_level.value)

        if query.search:
            search_condition = or_(
                User.name.contains(query.search),
                User.nickname.contains(query.search),
                User.phone.contains(query.search),
                User.school.contains(query.search),
            )
            conditions.append(search_condition)

        # 计算总数
        count_stmt = select(func.count(User.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # 查询数据
        stmt = select(User)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 排序
        if query.sort_by == "created_at":
            order_col = User.created_at
        elif query.sort_by == "name":
            order_col = User.name
        elif query.sort_by == "login_count":
            order_col = User.login_count
        else:
            order_col = User.created_at

        if query.sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        stmt = stmt.offset((query.page - 1) * query.size).limit(query.size)

        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return {
            "total": total,
            "page": query.page,
            "size": query.size,
            "pages": (total + query.size - 1) // query.size if total else 0,
            "items": [UserResponse.model_validate(user) for user in users],
        }

    @cache_result(ttl=300)  # 缓存5分钟
    async def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        # 总用户数
        total_users_stmt = select(func.count(User.id))
        total_result = await self.db.execute(total_users_stmt)
        total_users = total_result.scalar()

        # 活跃用户数
        active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
        active_result = await self.db.execute(active_users_stmt)
        active_users = active_result.scalar()

        # 今日新增用户
        today = datetime.utcnow().date()
        today_users_stmt = select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
        today_result = await self.db.execute(today_users_stmt)
        new_users_today = today_result.scalar()

        # 本周新增用户
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_users_stmt = select(func.count(User.id)).where(
            User.created_at >= week_ago.isoformat()
        )
        week_result = await self.db.execute(week_users_stmt)
        new_users_week = week_result.scalar()

        # 本月新增用户
        month_ago = datetime.utcnow() - timedelta(days=30)
        month_users_stmt = select(func.count(User.id)).where(
            User.created_at >= month_ago.isoformat()
        )
        month_result = await self.db.execute(month_users_stmt)
        new_users_month = month_result.scalar()

        # 已验证用户数
        verified_users_stmt = select(func.count(User.id)).where(
            User.is_verified == True
        )
        verified_result = await self.db.execute(verified_users_stmt)
        verified_users = verified_result.scalar()

        # 角色分布
        role_dist_stmt = select(User.role, func.count(User.id)).group_by(User.role)
        role_dist_result = await self.db.execute(role_dist_stmt)
        role_distribution = {row[0]: row[1] for row in role_dist_result}

        # 年级分布
        grade_dist_stmt = (
            select(User.grade_level, func.count(User.id))
            .where(User.grade_level.isnot(None))
            .group_by(User.grade_level)
        )
        grade_dist_result = await self.db.execute(grade_dist_stmt)
        grade_distribution = {row[0]: row[1] for row in grade_dist_result}

        # 学校分布（前10）
        school_dist_stmt = (
            select(User.school, func.count(User.id))
            .where(User.school.isnot(None))
            .group_by(User.school)
            .order_by(desc(func.count(User.id)))
            .limit(10)
        )
        school_dist_result = await self.db.execute(school_dist_stmt)
        school_distribution = {row[0]: row[1] for row in school_dist_result}

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
            "new_users_month": new_users_month,
            "verified_users": verified_users,
            "student_count": role_distribution.get("student", 0),
            "teacher_count": role_distribution.get("teacher", 0),
            "parent_count": role_distribution.get("parent", 0),
            "role_distribution": role_distribution,
            "grade_distribution": grade_distribution,
            "school_distribution": school_distribution,
        }

    # ========== 用户活动和进度 ==========

    async def get_user_activity(self, user_id: str) -> Optional[UserActivityResponse]:
        """获取用户活动统计"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # 这里需要跨模块查询，暂时返回基础数据
        # 实际实现需要查询问答记录、作业记录等

        last_login_str = extract_orm_str(user, "last_login_at")
        return UserActivityResponse(
            user_id=user_id,
            total_questions=0,  # TODO: 查询问答记录
            total_sessions=0,  # TODO: 查询会话记录
            total_homework=0,  # TODO: 查询作业记录
            study_streak_days=0,
            avg_daily_questions=0.0,
            most_active_subject=None,
            last_activity_at=(
                datetime.fromisoformat(last_login_str) if last_login_str else None
            ),
        )

    async def get_user_progress(self, user_id: str) -> Optional[UserProgressResponse]:
        """获取用户学习进度"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # 简化实现，返回基础进度信息
        return UserProgressResponse(
            user_id=user_id,
            overall_progress=65,  # 默认进度
            subject_progress={"math": 70, "chinese": 60, "english": 65},
            goal_completion_rate=50,
            knowledge_points_mastered=85,
            total_knowledge_points=120,
            strengths=["数学计算", "英语阅读"],
            weaknesses=["语文写作", "物理实验"],
            recommendations=[
                "建议加强语文写作练习",
                "可以多做物理实验题目",
                "继续保持数学优势",
            ],
        )

    # ========== 会话管理 ==========

    async def create_user_session(
        self,
        user_id: str,
        device_type: str = "web",
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """创建用户会话"""
        # 生成token JTI
        access_token_jti = secrets.token_hex(16)
        refresh_token_jti = secrets.token_hex(16)

        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        session_data = {
            "user_id": user_id,
            "device_type": device_type,
            "device_id": device_id,
            "access_token_jti": access_token_jti,
            "refresh_token_jti": refresh_token_jti,
            "expires_at": expires_at,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "is_revoked": False,
        }

        return await self.session_repo.create(session_data)

    async def get_user_session(self, jti: str) -> Optional[UserSession]:
        """根据JTI获取用户会话"""
        return await self.session_repo.get_by_field("access_token_jti", jti)

    async def revoke_user_session(self, session_id: str, user_id: str) -> bool:
        """撤销用户会话"""
        session = await self.session_repo.get_by_id(session_id)
        if not session or extract_orm_str(session, "user_id") != user_id:
            return False

        await self.session_repo.update(session_id, {"is_revoked": True})
        return True

    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """撤销用户所有会话"""
        # 查询用户所有活跃会话
        stmt = select(UserSession).where(
            UserSession.user_id == user_id, UserSession.is_revoked == False
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        # 批量撤销
        revoked_count = 0
        for session in sessions:
            session_id = extract_orm_uuid_str(session, "id")
            await self.session_repo.update(session_id, {"is_revoked": True})
            revoked_count += 1

        logger.info(
            "撤销用户所有会话", extra={"user_id": user_id, "count": revoked_count}
        )
        return revoked_count

    # ========== 密码管理 ==========

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """修改密码"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 验证旧密码
        if not self._verify_password(
            old_password, extract_orm_str(user, "password_hash")
        ):
            raise AuthenticationError("原密码错误")

        # 更新密码
        new_password_hash = self._hash_password(new_password)
        await self.user_repo.update(user_id, {"password_hash": new_password_hash})

        # 撤销所有会话，要求重新登录
        await self.revoke_all_user_sessions(user_id)

        logger.info("用户密码更新成功", extra={"user_id": user_id})
        return True

    async def reset_password(
        self, phone: str, new_password: str, verification_code: str
    ) -> bool:
        """重置密码（通过验证码）"""
        user = await self.user_repo.get_by_field("phone", phone)
        if not user:
            raise NotFoundError("用户不存在")

        # TODO: 验证短信验证码
        # if not self._verify_sms_code(phone, verification_code):
        #     raise ValidationError("验证码错误或已过期")

        # 更新密码
        new_password_hash = self._hash_password(new_password)
        user_id_str = extract_orm_uuid_str(user, "id")
        await self.user_repo.update(user_id_str, {"password_hash": new_password_hash})

        # 撤销所有会话
        await self.revoke_all_user_sessions(user_id_str)

        logger.info("用户密码重置成功", extra={"user_id": user_id_str, "phone": phone})
        return True

    # ========== 工具方法 ==========

    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        # 使用PBKDF2算法哈希密码
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000  # 迭代次数
        )
        return f"{salt}:{password_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = password_hash.split(":")
            calculated_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return calculated_hash.hex() == stored_hash
        except ValueError:
            return False

    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.utcnow().isoformat()

        stmt = select(UserSession).where(
            UserSession.expires_at < current_time, UserSession.is_revoked == False
        )
        result = await self.db.execute(stmt)
        expired_sessions = result.scalars().all()

        for session in expired_sessions:
            session_id = extract_orm_uuid_str(session, "id")
            await self.session_repo.update(session_id, {"is_revoked": True})

        if expired_sessions:
            logger.info("清理过期会话", extra={"count": len(expired_sessions)})


# 依赖注入函数
def get_user_service(db: AsyncSession) -> UserService:
    """获取用户服务实例"""
    return UserService(db)
