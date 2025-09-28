"""
学习仓储使用示例
展示如何在服务层中集成和使用LearningRepository
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base_repository import BaseRepository
from src.repositories.learning_repository import LearningRepository
from src.models.learning import ChatSession, Question, Answer, LearningAnalytics
from src.schemas.learning import (
    SessionResponse, QuestionResponse, LearningAnalyticsResponse,
    PaginatedResponse, SessionListResponse, QuestionHistoryResponse,
    QuestionType, SubjectType, DifficultyLevel, SessionStatus
)
from src.utils.type_converters import (
    extract_orm_str, extract_orm_uuid_str, extract_orm_int,
    extract_orm_bool, wrap_orm
)
from src.core.logging import get_logger

logger = get_logger(__name__)


def safe_enum_convert(value: str, enum_class, default=None):
    """Safe enum conversion with fallback"""
    if not value:
        return default
    try:
        # Try direct enum access
        return enum_class(value)
    except (ValueError, AttributeError):
        # Try case-insensitive lookup
        if hasattr(enum_class, '__members__'):
            for enum_val in enum_class:
                if hasattr(enum_val, 'value') and str(enum_val.value).lower() == str(value).lower():
                    return enum_val
        return default


class EnhancedLearningService:
    """
    增强版学习服务
    展示如何结合使用BaseRepository和LearningRepository
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # 基础仓储 - 用于简单的CRUD操作
        self.session_repo = BaseRepository(ChatSession, db)
        self.question_repo = BaseRepository(Question, db)
        self.answer_repo = BaseRepository(Answer, db)
        self.analytics_repo = BaseRepository(LearningAnalytics, db)

        # 专用仓储 - 用于复杂查询和业务逻辑
        self.learning_repo = LearningRepository(db)

    # ========== 会话管理 ==========

    async def get_or_create_active_session(
        self,
        user_id: str,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None
    ) -> ChatSession:
        """
        获取或创建活跃会话
        使用LearningRepository的专门查询方法
        """
        try:
            # 使用专门的仓储方法查找活跃会话
            active_session = await self.learning_repo.get_user_active_session(
                user_id=user_id,
                subject=subject
            )

            if active_session:
                # 更新最后活跃时间
                session_id = extract_orm_uuid_str(active_session, "id")
                await self.session_repo.update(session_id, {
                    'last_activity_at': datetime.now().isoformat()
                })
                return active_session

            # 创建新会话 - 使用基础仓储的简单创建方法
            session_data = {
                'user_id': user_id,
                'title': f"学习会话 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'subject': subject,
                'grade_level': grade_level,
                'status': 'active',
                'last_active_at': datetime.now().isoformat()
            }

            new_session = await self.session_repo.create(session_data)
            logger.info(f"Created new session {new_session.id} for user {user_id}")

            return new_session

        except Exception as e:
            logger.error(f"Error getting/creating active session: {e}")
            raise

    async def get_session_list_with_stats(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> PaginatedResponse:
        """
        获取会话列表及统计信息
        展示复杂查询的使用
        """
        try:
            # 使用专门的仓储方法获取带统计的会话列表
            sessions_with_stats = await self.learning_repo.get_user_sessions_with_stats(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status
            )

            # 转换为响应格式
            session_responses = []
            for session_data in sessions_with_stats:
                session = session_data['session']
                stats = {
                    'question_count': session_data['question_count'],
                    'avg_rating': session_data['avg_rating'],
                    'last_question_time': session_data['last_question_time']
                }

                session_response = SessionResponse(
                    id=session.id,
                    title=session.title,
                    subject=session.subject,
                    grade_level=session.grade_level,
                    status=session.status,
                    question_count=stats['question_count'],
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    **stats
                )
                session_responses.append(session_response)

            # 获取总数 - 使用基础仓储的计数方法
            total = await self.session_repo.count({
                'user_id': user_id,
                'status': status
            } if status else {'user_id': user_id})

            return SessionListResponse(
                items=session_responses,
                total=total,
                page=offset // limit + 1,
                size=limit,
                pages=(total + limit - 1) // limit if total > 0 else 0
            )

        except Exception as e:
            logger.error(f"Error getting session list with stats: {e}")
            raise

    # ========== 问答管理 ==========

    async def search_questions(
        self,
        user_id: str,
        search_term: str,
        subject: Optional[str] = None,
        limit: int = 20
    ) -> List[QuestionResponse]:
        """
        搜索问题
        展示专门搜索方法的使用
        """
        try:
            # 使用专门的搜索方法
            questions = await self.learning_repo.search_questions_by_content(
                user_id=user_id,
                search_term=search_term,
                subject=subject,
                limit=limit
            )

            # 转换为响应格式
            question_responses = []
            for question in questions:
                question_response = QuestionResponse(
                    id=extract_orm_uuid_str(question, "id"),
                    session_id=extract_orm_uuid_str(question, "session_id"),
                    user_id=extract_orm_uuid_str(question, "user_id"),
                    content=extract_orm_str(question, "content"),
                    question_type=None,  # Simplify to None for now
                    subject=None,        # Simplify to None for now
                    topic=extract_orm_str(question, "topic"),
                    difficulty_level=None,  # Simplify to None for now
                    is_processed=extract_orm_bool(question, "is_processed", False),
                    processing_time=extract_orm_int(question, "processing_time"),
                    created_at=getattr(question, "created_at"),
                    updated_at=getattr(question, "updated_at")
                )
                question_responses.append(question_response)

            logger.info(f"Found {len(questions)} questions for search term '{search_term}'")
            return question_responses

        except Exception as e:
            logger.error(f"Error searching questions: {e}")
            raise

    async def get_recent_questions_by_topic(
        self,
        user_id: str,
        topic: str,
        days: int = 7,
        limit: int = 5
    ) -> List[QuestionResponse]:
        """
        获取最近的相关问题
        用于上下文构建和问题推荐
        """
        try:
            questions = await self.learning_repo.get_recent_questions_by_topic(
                user_id=user_id,
                topic=topic,
                days=days,
                limit=limit
            )

            return [
                QuestionResponse(
                    id=extract_orm_uuid_str(q, "id"),
                    session_id=extract_orm_uuid_str(q, "session_id"),
                    user_id=extract_orm_uuid_str(q, "user_id"),
                    content=extract_orm_str(q, "content"),
                    question_type=None,  # Simplify to None for now
                    subject=None,        # Simplify to None for now
                    topic=extract_orm_str(q, "topic"),
                    difficulty_level=None,  # Simplify to None for now
                    is_processed=extract_orm_bool(q, "is_processed", False),
                    processing_time=extract_orm_int(q, "processing_time"),
                    created_at=getattr(q, "created_at"),
                    updated_at=getattr(q, "updated_at")
                ) for q in questions
            ]

        except Exception as e:
            logger.error(f"Error getting recent questions by topic: {e}")
            raise

    # ========== 学习分析 ==========

    async def get_comprehensive_learning_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> LearningAnalyticsResponse:
        """
        获取综合学习分析
        展示复杂分析查询的组合使用
        """
        try:
            # 获取基础学习统计
            learning_stats = await self.learning_repo.get_user_learning_stats(
                user_id=user_id,
                days=days
            )

            # 获取每日活动模式
            daily_pattern = await self.learning_repo.get_daily_activity_pattern(
                user_id=user_id,
                days=days
            )

            # 获取知识掌握分析
            mastery_analysis = await self.learning_repo.get_knowledge_mastery_analysis(
                user_id=user_id
            )

            # 获取低评分问答（需要改进的地方）
            low_rated_qa = await self.learning_repo.get_questions_with_low_ratings(
                user_id=user_id,
                max_rating=2,
                limit=5
            )

            # 构建必需的数据结构
            from src.schemas.learning import SubjectStats, LearningPattern

            # 创建学科统计
            subject_stats = []
            for subject, stats in learning_stats.get('subject_distribution', {}).items():
                subject_stats.append(SubjectStats(
                    subject=subject,
                    question_count=stats.get('count', 0),
                    avg_difficulty=stats.get('avg_difficulty', 'medium'),
                    mastery_level=stats.get('mastery_level', 0.5)
                ))

            # 创建学习模式
            preferred_diff_str = str(daily_pattern.get('preferred_difficulty', 'medium'))
            preferred_diff = safe_enum_convert(preferred_diff_str, DifficultyLevel, DifficultyLevel.MEDIUM)

            learning_pattern = LearningPattern(
                most_active_hour=daily_pattern.get('peak_hour', 14),
                most_active_day=daily_pattern.get('peak_day', 1),
                avg_session_length=daily_pattern.get('avg_session_length', 30),
                preferred_difficulty=preferred_diff
            )

            # 组合所有分析结果
            analytics_response = LearningAnalyticsResponse(
                user_id=user_id,
                total_questions=learning_stats.get('total_questions', 0),
                total_sessions=learning_stats.get('total_sessions', 0),
                subject_stats=subject_stats,
                learning_pattern=learning_pattern,
                avg_rating=learning_stats.get('avg_rating', 0.0),
                positive_feedback_rate=int(learning_stats.get('helpful_answers', 0) * 100),
                improvement_suggestions=[
                    f"在{area}方面需要更多练习" for area in mastery_analysis.get('improvement_areas', [])[:3]
                ],
                knowledge_gaps=[
                    f"{topic}掌握度较低" for topic in mastery_analysis.get('weak_topics', [])[:3]
                ],
                last_analyzed_at=datetime.now()
            )

            # 更新或创建学习分析记录
            await self._update_analytics_record(user_id, analytics_response)

            logger.info(f"Generated comprehensive learning analytics for user {user_id}")
            return analytics_response

        except Exception as e:
            logger.error(f"Error getting comprehensive learning analytics: {e}")
            raise

    async def _update_analytics_record(
        self,
        user_id: str,
        analytics_response: LearningAnalyticsResponse
    ):
        """
        更新学习分析记录
        展示基础仓储和专门仓储的协同使用
        """
        try:
            # 检查是否已有记录
            existing_analytics = await self.analytics_repo.get_by_field('user_id', user_id)

            analytics_data = {
                'total_questions': analytics_response.total_questions,
                'total_sessions': analytics_response.total_sessions,
                'active_subjects': [stat.subject for stat in analytics_response.subject_stats],
                'question_types_stats': {},
                'preferred_subjects': [],
                'avg_rating': analytics_response.avg_rating,
                'positive_feedback_rate': analytics_response.positive_feedback_rate,
                'weekly_pattern': {},
                'knowledge_mastery': {},
                'improvement_areas': analytics_response.improvement_suggestions,
                'last_analyzed_at': datetime.now().isoformat()
            }

            if existing_analytics:
                # 更新现有记录
                analytics_id = extract_orm_uuid_str(existing_analytics, "id")
                await self.analytics_repo.update(analytics_id, analytics_data)
            else:
                # 创建新记录
                analytics_data['user_id'] = user_id
                await self.analytics_repo.create(analytics_data)

        except Exception as e:
            logger.error(f"Error updating analytics record: {e}")
            # 不抛出异常，因为这是辅助操作

    # ========== 批量操作示例 ==========

    async def bulk_update_session_statistics(self, user_id: str) -> Dict[str, int]:
        """
        批量更新用户的会话统计信息
        展示批量操作的使用
        """
        try:
            # 获取用户的所有会话
            user_sessions = await self.session_repo.get_all(
                filters={'user_id': user_id}
            )

            session_ids = [extract_orm_uuid_str(session, "id") for session in user_sessions]

            # 使用专门仓储的批量更新方法
            updated_count = await self.learning_repo.bulk_update_session_stats(session_ids)

            # 清除相关缓存
            await self.learning_repo.invalidate_user_cache(user_id)

            return {
                'total_sessions': len(session_ids),
                'updated_sessions': updated_count if isinstance(updated_count, int) else 0
            }

        except Exception as e:
            logger.error(f"Error bulk updating session statistics: {e}")
            raise

    # ========== 性能优化示例 ==========

    async def get_session_with_context(
        self,
        session_id: str,
        user_id: str,
        include_qa_limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        获取会话及其上下文信息
        展示优化查询的使用
        """
        try:
            # 使用专门方法一次性获取会话和问答历史
            session_with_qa = await self.learning_repo.get_session_with_qa_history(
                session_id=session_id,
                user_id=user_id,
                limit=include_qa_limit
            )

            if not session_with_qa:
                return None

            session = session_with_qa['session']
            qa_history = session_with_qa['qa_history']

            # 构建响应数据
            return {
                'session': SessionResponse(
                    id=extract_orm_uuid_str(session, "id"),
                    user_id=extract_orm_uuid_str(session, "user_id"),
                    title=extract_orm_str(session, "title", "学习会话"),
                    subject=None,  # Simplify to None for now
                    grade_level=extract_orm_str(session, "grade_level"),
                    status=session.status,
                    question_count=extract_orm_int(session, "question_count") or 0,
                    total_tokens=extract_orm_int(session, "total_tokens") or 0,
                    created_at=getattr(session, "created_at"),
                    updated_at=getattr(session, "updated_at")
                ),
                'qa_history': [
                    {
                        'question': QuestionResponse(
                            id=extract_orm_uuid_str(q, "id"),
                            session_id=extract_orm_uuid_str(q, "session_id"),
                            user_id=extract_orm_uuid_str(q, "user_id"),
                            content=extract_orm_str(q, "content"),
                            question_type=None,  # Simplify to None for now
                            subject=None,        # Simplify to None for now
                            topic=extract_orm_str(q, "topic"),
                            difficulty_level=None,  # Simplify to None for now
                            is_processed=extract_orm_bool(q, "is_processed", False),
                            processing_time=extract_orm_int(q, "processing_time"),
                            created_at=getattr(q, "created_at"),
                            updated_at=getattr(q, "updated_at")
                        ),
                        'answer': q.answer  # Answer对象，如果存在
                    } for q in qa_history
                ],
                'context_summary': {
                    'total_questions': len(qa_history),
                    'main_topics': list(set(q.topic for q in qa_history if q.topic)),
                    'subjects': list(set(q.subject for q in qa_history if q.subject))
                }
            }

        except Exception as e:
            logger.error(f"Error getting session with context: {e}")
            raise


# ========== 使用示例和最佳实践 ==========

"""
使用示例：

# 1. 初始化服务
learning_service = EnhancedLearningService(db)

# 2. 创建或获取活跃会话
session = await learning_service.get_or_create_active_session(
    user_id="user_123",
    subject="数学",
    grade_level="初二"
)

# 3. 获取会话列表及统计
session_list = await learning_service.get_session_list_with_stats(
    user_id="user_123",
    limit=10,
    offset=0
)

# 4. 搜索问题
questions = await learning_service.search_questions(
    user_id="user_123",
    search_term="二次函数",
    subject="数学"
)

# 5. 获取综合学习分析
analytics = await learning_service.get_comprehensive_learning_analytics(
    user_id="user_123",
    days=30
)

# 6. 批量更新统计信息
stats = await learning_service.bulk_update_session_statistics("user_123")

最佳实践：

1. **职责分离**：
   - BaseRepository：简单CRUD操作
   - LearningRepository：复杂查询和业务逻辑
   - Service层：业务流程和数据转换

2. **性能优化**：
   - 使用专门的查询方法减少数据库往返
   - 合理使用预加载（selectinload）
   - 批量操作处理大量数据

3. **错误处理**：
   - 分层异常处理
   - 记录详细的错误日志
   - 优雅的错误恢复

4. **缓存策略**：
   - 识别热点数据
   - 合理的缓存失效策略
   - 避免缓存雪崩

5. **可维护性**：
   - 清晰的方法命名
   - 充分的类型注解
   - 详细的文档说明
"""
