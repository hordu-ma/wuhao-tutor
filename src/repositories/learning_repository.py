"""
学习问答专用仓储类
提供学习问答业务相关的复杂查询和数据访问方法
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, and_, or_, text
from sqlalchemy.orm import selectinload, joinedload

from src.core.logging import get_logger
from src.models.learning import (
    ChatSession, Question, Answer, LearningAnalytics,
    QuestionType, SessionStatus
)
from src.models.user import User
from src.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class LearningRepository:
    """
    学习问答专用仓储
    封装复杂的学习相关查询逻辑
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = BaseRepository(ChatSession, db)
        self.question_repo = BaseRepository(Question, db)
        self.answer_repo = BaseRepository(Answer, db)
        self.analytics_repo = BaseRepository(LearningAnalytics, db)

    # ========== 会话相关查询 ==========

    async def get_user_active_session(
        self,
        user_id: str,
        subject: Optional[str] = None
    ) -> Optional[ChatSession]:
        """
        获取用户的活跃会话

        Args:
            user_id: 用户ID
            subject: 学科过滤

        Returns:
            活跃的会话或None
        """
        try:
            stmt = select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.status == SessionStatus.ACTIVE.value
                )
            )

            if subject:
                stmt = stmt.where(ChatSession.subject == subject)

            stmt = stmt.order_by(desc(ChatSession.last_active_at)).limit(1)

            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()

            if session:
                logger.debug(f"Found active session {session.id} for user {user_id}")
            else:
                logger.debug(f"No active session found for user {user_id}")

            return session

        except Exception as e:
            logger.error(f"Error getting active session for user {user_id}: {e}")
            raise

    async def get_user_sessions_with_stats(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户的会话列表及统计信息

        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            status: 状态过滤
            subject: 学科过滤

        Returns:
            包含统计信息的会话列表
        """
        try:
            # 构建基础查询
            stmt = select(
                ChatSession,
                func.count(Question.id).label('question_count'),
                func.avg(Answer.user_rating).label('avg_rating'),
                func.max(Question.created_at).label('last_question_time')
            ).outerjoin(Question).outerjoin(Answer).where(
                ChatSession.user_id == user_id
            ).group_by(ChatSession.id)

            # 应用过滤条件
            if status:
                stmt = stmt.where(ChatSession.status == status)
            if subject:
                stmt = stmt.where(ChatSession.subject == subject)

            # 排序和分页
            stmt = stmt.order_by(desc(ChatSession.updated_at))
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            rows = result.all()

            sessions = []
            for session, q_count, avg_rating, last_q_time in rows:
                session_data = {
                    'session': session,
                    'question_count': q_count or 0,
                    'avg_rating': round(avg_rating, 2) if avg_rating else None,
                    'last_question_time': last_q_time
                }
                sessions.append(session_data)

            logger.debug(f"Found {len(sessions)} sessions for user {user_id}")
            return sessions

        except Exception as e:
            logger.error(f"Error getting sessions with stats for user {user_id}: {e}")
            raise

    async def get_session_with_qa_history(
        self,
        session_id: str,
        user_id: str,
        limit: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取会话及其问答历史

        Args:
            session_id: 会话ID
            user_id: 用户ID（用于权限验证）
            limit: 限制问答数量

        Returns:
            包含问答历史的会话信息
        """
        try:
            # 获取会话信息
            session = await self.session_repo.get_by_field('id', session_id)
            if not session or str(getattr(session, 'user_id', '')) != str(user_id):
                return None

            # 获取问答历史
            stmt = select(Question).options(
                selectinload(Question.answer)
            ).where(
                Question.session_id == session_id
            ).order_by(asc(Question.created_at))

            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            return {
                'session': session,
                'qa_history': list(questions)
            }

        except Exception as e:
            logger.error(f"Error getting session with QA history {session_id}: {e}")
            raise

    # ========== 问答相关查询 ==========

    async def get_recent_questions_by_topic(
        self,
        user_id: str,
        topic: str,
        days: int = 7,
        limit: int = 5
    ) -> List[Question]:
        """
        获取用户最近关于某话题的问题

        Args:
            user_id: 用户ID
            topic: 话题
            days: 最近天数
            limit: 限制数量

        Returns:
            问题列表
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = select(Question).where(
                and_(
                    Question.user_id == user_id,
                    Question.topic.ilike(f"%{topic}%"),
                    Question.created_at >= cutoff_date.isoformat()
                )
            ).order_by(desc(Question.created_at)).limit(limit)

            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            logger.debug(f"Found {len(questions)} recent questions on topic '{topic}' for user {user_id}")
            return list(questions)

        except Exception as e:
            logger.error(f"Error getting recent questions by topic: {e}")
            raise

    async def get_questions_with_low_ratings(
        self,
        user_id: str,
        max_rating: int = 2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户评分较低的问答

        Args:
            user_id: 用户ID
            max_rating: 最大评分
            limit: 限制数量

        Returns:
            包含问题和答案的列表
        """
        try:
            stmt = select(Question, Answer).join(Answer).where(
                and_(
                    Question.user_id == user_id,
                    Answer.user_rating <= max_rating,
                    Answer.user_rating.is_not(None)
                )
            ).order_by(desc(Question.created_at)).limit(limit)

            result = await self.db.execute(stmt)
            rows = result.all()

            qa_pairs = []
            for question, answer in rows:
                qa_pairs.append({
                    'question': question,
                    'answer': answer
                })

            logger.debug(f"Found {len(qa_pairs)} low-rated QA pairs for user {user_id}")
            return qa_pairs

        except Exception as e:
            logger.error(f"Error getting questions with low ratings: {e}")
            raise

    async def search_questions_by_content(
        self,
        user_id: str,
        search_term: str,
        subject: Optional[str] = None,
        limit: int = 20
    ) -> List[Question]:
        """
        根据内容搜索问题

        Args:
            user_id: 用户ID
            search_term: 搜索词
            subject: 学科过滤
            limit: 限制数量

        Returns:
            匹配的问题列表
        """
        try:
            stmt = select(Question).where(
                and_(
                    Question.user_id == user_id,
                    or_(
                        Question.content.ilike(f"%{search_term}%"),
                        Question.topic.ilike(f"%{search_term}%")
                    )
                )
            )

            if subject:
                stmt = stmt.where(Question.subject == subject)

            stmt = stmt.order_by(desc(Question.created_at)).limit(limit)

            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            logger.debug(f"Found {len(questions)} questions matching '{search_term}' for user {user_id}")
            return list(questions)

        except Exception as e:
            logger.error(f"Error searching questions by content: {e}")
            raise

    # ========== 学习分析相关查询 ==========

    async def get_user_learning_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户学习统计数据

        Args:
            user_id: 用户ID
            days: 统计天数

        Returns:
            学习统计数据
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # 基础统计查询
            stats_query = select(
                func.count(Question.id).label('total_questions'),
                func.count(func.distinct(ChatSession.id)).label('total_sessions'),
                func.count(func.distinct(Question.subject)).label('active_subjects'),
                func.avg(Answer.user_rating).label('avg_rating'),
                func.count(
                    func.case((Answer.is_helpful == True, 1))
                ).label('helpful_answers')
            ).select_from(Question).outerjoin(
                ChatSession, Question.session_id == ChatSession.id
            ).outerjoin(
                Answer, Question.id == Answer.question_id
            ).where(
                and_(
                    Question.user_id == user_id,
                    Question.created_at >= cutoff_date.isoformat()
                )
            )

            result = await self.db.execute(stats_query)
            stats_row = result.first()

            # 学科分布查询
            subject_query = select(
                Question.subject,
                func.count(Question.id).label('count')
            ).where(
                and_(
                    Question.user_id == user_id,
                    Question.created_at >= cutoff_date.isoformat(),
                    Question.subject.is_not(None)
                )
            ).group_by(Question.subject).order_by(desc('count'))

            subject_result = await self.db.execute(subject_query)
            subject_rows = subject_result.all()
            subject_stats = {row[0]: row[1] for row in subject_rows}

            # 问题类型分布查询
            type_query = select(
                Question.question_type,
                func.count(Question.id).label('count')
            ).where(
                and_(
                    Question.user_id == user_id,
                    Question.created_at >= cutoff_date.isoformat(),
                    Question.question_type.is_not(None)
                )
            ).group_by(Question.question_type).order_by(desc('count'))

            type_result = await self.db.execute(type_query)
            type_rows = type_result.all()
            type_stats = {row[0]: row[1] for row in type_rows}

            # 组合统计结果
            if stats_row:
                learning_stats = {
                    'total_questions': getattr(stats_row, 'total_questions', 0) or 0,
                    'total_sessions': getattr(stats_row, 'total_sessions', 0) or 0,
                    'active_subjects': getattr(stats_row, 'active_subjects', 0) or 0,
                    'avg_rating': round(getattr(stats_row, 'avg_rating', 0), 2) if getattr(stats_row, 'avg_rating', None) else None,
                    'helpful_answers': getattr(stats_row, 'helpful_answers', 0) or 0,
                    'subject_distribution': subject_stats,
                    'question_type_distribution': type_stats,
                    'period_days': days
                }
            else:
                learning_stats = {
                    'total_questions': 0,
                    'total_sessions': 0,
                    'active_subjects': 0,
                    'avg_rating': None,
                    'helpful_answers': 0,
                    'subject_distribution': subject_stats,
                    'question_type_distribution': type_stats,
                    'period_days': days
                }

            logger.debug(f"Generated learning stats for user {user_id}: {learning_stats}")
            return learning_stats

        except Exception as e:
            logger.error(f"Error getting user learning stats: {e}")
            raise

    async def get_daily_activity_pattern(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, int]:
        """
        获取用户每日活动模式

        Args:
            user_id: 用户ID
            days: 统计天数

        Returns:
            每日问题数量分布
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # 使用原生SQL进行日期分组（适应不同数据库）
            stmt = text("""
                SELECT DATE(created_at) as question_date, COUNT(*) as count
                FROM questions
                WHERE user_id = :user_id
                  AND created_at >= :cutoff_date
                GROUP BY DATE(created_at)
                ORDER BY question_date
            """)

            result = await self.db.execute(
                stmt,
                {'user_id': user_id, 'cutoff_date': cutoff_date.isoformat()}
            )

            daily_pattern = {}
            for row in result:
                daily_pattern[str(row.question_date)] = row.count

            logger.debug(f"Generated daily activity pattern for user {user_id}")
            return daily_pattern

        except Exception as e:
            logger.error(f"Error getting daily activity pattern: {e}")
            raise

    async def get_knowledge_mastery_analysis(
        self,
        user_id: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析用户知识掌握情况

        Args:
            user_id: 用户ID
            subject: 学科过滤

        Returns:
            知识掌握分析结果
        """
        try:
            base_query = select(
                Question.topic,
                func.count(Question.id).label('question_count'),
                func.avg(Answer.user_rating).label('avg_rating'),
                func.avg(Answer.confidence_score).label('avg_confidence'),
                func.count(
                    func.case((Answer.is_helpful == True, 1))
                ).label('helpful_count')
            ).select_from(Question).join(
                Answer, Question.id == Answer.question_id
            ).where(
                and_(
                    Question.user_id == user_id,
                    Question.topic.is_not(None),
                    Answer.user_rating.is_not(None)
                )
            )

            if subject:
                base_query = base_query.where(Question.subject == subject)

            base_query = base_query.group_by(Question.topic).having(
                func.count(Question.id) >= 2  # 至少2个问题才能分析
            ).order_by(desc('avg_rating'))

            result = await self.db.execute(base_query)
            topic_analysis = []

            for row in result:
                mastery_level = 'high' if row.avg_rating >= 4 else 'medium' if row.avg_rating >= 3 else 'low'
                topic_analysis.append({
                    'topic': row.topic,
                    'question_count': row.question_count,
                    'avg_rating': round(row.avg_rating, 2),
                    'avg_confidence': round(row.avg_confidence, 2) if row.avg_confidence else None,
                    'helpful_rate': round(row.helpful_count / row.question_count * 100, 2),
                    'mastery_level': mastery_level
                })

            # 按掌握程度分组
            mastery_summary = {
                'high': [t for t in topic_analysis if t['mastery_level'] == 'high'],
                'medium': [t for t in topic_analysis if t['mastery_level'] == 'medium'],
                'low': [t for t in topic_analysis if t['mastery_level'] == 'low']
            }

            analysis_result = {
                'topics_analyzed': len(topic_analysis),
                'mastery_distribution': {
                    'high': len(mastery_summary['high']),
                    'medium': len(mastery_summary['medium']),
                    'low': len(mastery_summary['low'])
                },
                'topic_details': topic_analysis,
                'improvement_areas': mastery_summary['low'][:5],  # 前5个需要改进的话题
                'strong_areas': mastery_summary['high'][:5]       # 前5个强势话题
            }

            logger.debug(f"Generated knowledge mastery analysis for user {user_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error getting knowledge mastery analysis: {e}")
            raise

    # ========== 缓存相关方法 ==========

    async def invalidate_user_cache(self, user_id: str):
        """
        清除用户相关的缓存

        Args:
            user_id: 用户ID
        """
        try:
            # 这里可以实现具体的缓存清理逻辑
            # 例如使用Redis的pattern删除
            logger.debug(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.warning(f"Error invalidating cache for user {user_id}: {e}")

    # ========== 批量操作 ==========

    async def bulk_update_session_stats(self, session_ids: List[str]) -> int:
        """
        批量更新会话统计信息

        Args:
            session_ids: 会话ID列表

        Returns:
            更新的会话数量
        """
        try:
            updated_count = 0

            for session_id in session_ids:
                # 计算会话的问题数量和token消耗
                stats_query = select(
                    func.count(Question.id).label('question_count'),
                    func.sum(Answer.tokens_used).label('total_tokens')
                ).select_from(Question).outerjoin(
                    Answer, Question.id == Answer.question_id
                ).where(Question.session_id == session_id)

                result = await self.db.execute(stats_query)
                stats = result.first()

                # 更新会话统计
                if stats:
                    await self.session_repo.update(session_id, {
                        'question_count': stats.question_count or 0,
                        'total_tokens': stats.total_tokens or 0
                    })
                    updated_count += 1

            logger.debug(f"Bulk updated stats for {updated_count} sessions")
            return updated_count

        except Exception as e:
            logger.error(f"Error bulk updating session stats: {e}")
            raise
