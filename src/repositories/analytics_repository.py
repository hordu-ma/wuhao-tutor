"""
学情分析数据仓库 (Analytics Repository)

提供高效的学情分析数据查询方法，优化数据库查询性能
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.homework import HomeworkReview, HomeworkSubmission
from src.models.learning import Answer, ChatSession, Question
from src.models.user import User
from src.repositories.base_repository import BaseRepository

logger = logging.getLogger("analytics_repository")


class AnalyticsRepository(BaseRepository):
    """学情分析数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_study_activity_stats(
        self, user_id: UUID, start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取学习活动统计（优化版本）

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            学习活动统计数据
        """
        try:
            # 构建作业查询条件
            homework_conditions = [HomeworkSubmission.student_id == str(user_id)]
            if start_date:
                homework_conditions.append(HomeworkSubmission.created_at >= start_date)

            # 使用子查询优化性能
            homework_subq = (
                select(
                    func.count(HomeworkSubmission.id).label("homework_count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.sum(func.coalesce(HomeworkSubmission.time_spent, 30)).label(
                        "total_time"
                    ),
                )
                .where(and_(*homework_conditions))
                .subquery()
            )

            # 构建问题查询条件
            question_conditions = [Question.user_id == str(user_id)]
            if start_date:
                question_conditions.append(Question.created_at >= start_date)

            question_subq = (
                select(
                    func.count(Question.id).label("question_count"),
                )
                .where(and_(*question_conditions))
                .subquery()
            )

            # 单次查询获取所有统计数据
            stmt = select(
                homework_subq.c.homework_count,
                homework_subq.c.avg_score,
                homework_subq.c.total_time,
                question_subq.c.question_count,
            )

            result = await self.db.execute(stmt)
            row = result.one_or_none()

            if not row:
                return {
                    "homework_count": 0,
                    "avg_score": 0.0,
                    "total_time": 0,
                    "question_count": 0,
                }

            return {
                "homework_count": row.homework_count or 0,
                "avg_score": float(row.avg_score or 0),
                "total_time": row.total_time or 0,
                "question_count": row.question_count or 0,
            }

        except Exception as e:
            logger.error(f"获取学习活动统计失败: {e}", exc_info=True)
            return {
                "homework_count": 0,
                "avg_score": 0.0,
                "total_time": 0,
                "question_count": 0,
            }

    async def get_subject_performance_batch(
        self, user_id: UUID, start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        批量获取学科表现数据（优化版本）

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            学科表现数据列表
        """
        try:
            # 构建查询条件
            conditions = [HomeworkSubmission.student_id == str(user_id)]
            if start_date:
                conditions.append(HomeworkSubmission.created_at >= start_date)

            # 使用窗口函数优化排序查询
            stmt = (
                select(
                    HomeworkSubmission.subject,
                    func.count(HomeworkSubmission.id).label("homework_count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.max(HomeworkSubmission.created_at).label("last_study"),
                    func.sum(func.coalesce(HomeworkSubmission.time_spent, 30)).label(
                        "study_duration"
                    ),
                    func.stddev(HomeworkSubmission.total_score).label("score_variance"),
                    func.row_number()
                    .over(order_by=desc(func.avg(HomeworkSubmission.total_score)))
                    .label("rank"),
                )
                .where(and_(*conditions))
                .group_by(HomeworkSubmission.subject)
                .having(func.count(HomeworkSubmission.id) > 0)  # 只返回有数据的学科
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            subjects = []
            for row in rows:
                if not row.subject:
                    continue

                # 计算进步趋势（基于分数方差）
                trend = "stable"
                if row.score_variance:
                    if row.score_variance > 15:
                        trend = "improving" if row.avg_score > 70 else "declining"

                subjects.append(
                    {
                        "subject": row.subject,
                        "homework_count": row.homework_count,
                        "avg_score": float(row.avg_score or 0),
                        "last_study": row.last_study,
                        "study_duration": row.study_duration or 0,
                        "rank": row.rank,
                        "trend": trend,
                        "score_variance": float(row.score_variance or 0),
                    }
                )

            return subjects

        except Exception as e:
            logger.error(f"获取学科表现数据失败: {e}", exc_info=True)
            return []

    async def get_time_series_data(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        获取时间序列数据（优化版本）

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            granularity: 时间粒度

        Returns:
            时间序列数据
        """
        try:
            # 根据粒度选择日期截断函数
            if granularity == "weekly":
                date_trunc = func.date_trunc("week", HomeworkSubmission.created_at)
            elif granularity == "monthly":
                date_trunc = func.date_trunc("month", HomeworkSubmission.created_at)
            else:  # daily
                date_trunc = func.date(HomeworkSubmission.created_at)

            # 使用 CTE 优化复杂查询
            homework_cte = (
                select(
                    date_trunc.label("period"),
                    func.count(HomeworkSubmission.id).label("homework_count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.sum(func.coalesce(HomeworkSubmission.time_spent, 30)).label(
                        "study_time"
                    ),
                )
                .where(
                    and_(
                        HomeworkSubmission.student_id == str(user_id),
                        HomeworkSubmission.created_at >= start_date,
                        HomeworkSubmission.created_at <= end_date,
                    )
                )
                .group_by(date_trunc)
                .cte("homework_stats")
            )

            question_cte = (
                select(
                    date_trunc.label("period"),
                    func.count(Question.id).label("question_count"),
                )
                .where(
                    and_(
                        Question.user_id == str(user_id),
                        Question.created_at >= start_date,
                        Question.created_at <= end_date,
                    )
                )
                .group_by(date_trunc)
                .cte("question_stats")
            )

            # 左连接合并数据
            stmt = (
                select(
                    homework_cte.c.period,
                    func.coalesce(homework_cte.c.homework_count, 0).label(
                        "homework_count"
                    ),
                    func.coalesce(homework_cte.c.avg_score, 0).label("avg_score"),
                    func.coalesce(homework_cte.c.study_time, 0).label("study_time"),
                    func.coalesce(question_cte.c.question_count, 0).label(
                        "question_count"
                    ),
                )
                .select_from(
                    homework_cte.outerjoin(
                        question_cte, homework_cte.c.period == question_cte.c.period
                    )
                )
                .order_by(homework_cte.c.period)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            time_series = []
            for row in rows:
                period_str = (
                    str(row.period.date())
                    if hasattr(row.period, "date")
                    else str(row.period)
                )

                time_series.append(
                    {
                        "period": period_str,
                        "homework_count": row.homework_count,
                        "question_count": row.question_count,
                        "avg_score": float(row.avg_score),
                        "study_time": row.study_time,
                        "completion_rate": (
                            1.0 if row.homework_count > 0 else 0.0
                        ),  # 简化计算
                        "accuracy_rate": (
                            float(row.avg_score) / 100.0 if row.avg_score else 0.0
                        ),
                    }
                )

            return time_series

        except Exception as e:
            logger.error(f"获取时间序列数据失败: {e}", exc_info=True)
            return []

    async def get_knowledge_point_stats(
        self, user_id: UUID, subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取知识点统计数据（基于作业表现）

        Args:
            user_id: 用户ID
            subject: 学科筛选

        Returns:
            知识点统计数据
        """
        try:
            conditions = [HomeworkSubmission.student_id == str(user_id)]
            if subject:
                conditions.append(HomeworkSubmission.subject == subject)

            # 基于学科和作业类型分析知识点掌握情况
            stmt = (
                select(
                    HomeworkSubmission.subject,
                    HomeworkSubmission.homework_type,
                    func.count(HomeworkSubmission.id).label("attempts"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.max(HomeworkSubmission.created_at).label("last_attempt"),
                    func.min(HomeworkSubmission.created_at).label("first_attempt"),
                    func.stddev(HomeworkSubmission.total_score).label("score_std"),
                )
                .where(and_(*conditions))
                .group_by(HomeworkSubmission.subject, HomeworkSubmission.homework_type)
                .having(func.count(HomeworkSubmission.id) >= 1)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            knowledge_points = []
            for i, row in enumerate(rows):
                mastery_level = (row.avg_score or 0) / 100.0
                attempts = row.attempts

                # 基于表现判断趋势
                if mastery_level >= 0.8:
                    trend = "stable"
                elif mastery_level >= 0.6:
                    trend = "improving"
                else:
                    trend = "declining"

                knowledge_points.append(
                    {
                        "id": f"kp_{row.subject}_{i+1}",
                        "name": f"{row.subject}-{row.homework_type or '基础'}",
                        "subject": row.subject,
                        "mastery_level": mastery_level,
                        "accuracy_rate": mastery_level,
                        "total_attempts": attempts,
                        "correct_attempts": int(attempts * mastery_level),
                        "last_practice": row.last_attempt,
                        "trend": trend,
                        "score_stability": 1.0 - min((row.score_std or 0) / 50.0, 1.0),
                    }
                )

            return knowledge_points

        except Exception as e:
            logger.error(f"获取知识点统计失败: {e}", exc_info=True)
            return []

    async def create_performance_indexes(self) -> bool:
        """
        创建学情分析性能索引

        Returns:
            是否创建成功
        """
        try:
            # 定义需要创建的索引
            indexes = [
                # 作业提交表索引
                "CREATE INDEX IF NOT EXISTS idx_homework_submission_student_created "
                "ON homework_submissions(student_id, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_homework_submission_subject_score "
                "ON homework_submissions(subject, total_score) "
                "WHERE total_score IS NOT NULL",
                "CREATE INDEX IF NOT EXISTS idx_homework_submission_status_created "
                "ON homework_submissions(status, created_at DESC)",
                # 问题表索引
                "CREATE INDEX IF NOT EXISTS idx_question_user_created "
                "ON questions(user_id, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_question_subject_created "
                "ON questions(subject, created_at DESC) "
                "WHERE subject IS NOT NULL",
                # 答案表索引
                "CREATE INDEX IF NOT EXISTS idx_answer_question_created "
                "ON answers(question_id, created_at DESC)",
                # 复合索引优化
                "CREATE INDEX IF NOT EXISTS idx_homework_multi_analytics "
                "ON homework_submissions(student_id, subject, created_at, total_score) "
                "WHERE status != 'deleted'",
            ]

            # 执行索引创建
            for index_sql in indexes:
                try:
                    await self.db.execute(text(index_sql))
                    logger.info(f"索引创建成功: {index_sql[:50]}...")
                except Exception as e:
                    logger.warning(f"索引创建失败: {e}")

            await self.db.commit()
            logger.info("学情分析性能索引创建完成")
            return True

        except Exception as e:
            logger.error(f"创建性能索引失败: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def analyze_query_performance(
        self, user_id: UUID, query_type: str = "all"
    ) -> Dict[str, Any]:
        """
        分析查询性能

        Args:
            user_id: 用户ID
            query_type: 查询类型

        Returns:
            性能分析结果
        """
        try:
            performance_stats = {}

            # 测试基础统计查询性能
            if query_type in ("all", "basic"):
                start_time = datetime.utcnow()
                await self.get_study_activity_stats(user_id)
                basic_time = (datetime.utcnow() - start_time).total_seconds()
                performance_stats["basic_stats_query_time"] = basic_time

            # 测试学科统计查询性能
            if query_type in ("all", "subject"):
                start_time = datetime.utcnow()
                await self.get_subject_performance_batch(user_id)
                subject_time = (datetime.utcnow() - start_time).total_seconds()
                performance_stats["subject_stats_query_time"] = subject_time

            # 测试时间序列查询性能
            if query_type in ("all", "timeseries"):
                start_time = datetime.utcnow()
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                await self.get_time_series_data(user_id, start_date, end_date)
                timeseries_time = (datetime.utcnow() - start_time).total_seconds()
                performance_stats["timeseries_query_time"] = timeseries_time

            performance_stats["analyzed_at"] = datetime.utcnow().isoformat()
            performance_stats["user_id"] = str(user_id)

            return performance_stats

        except Exception as e:
            logger.error(f"查询性能分析失败: {e}", exc_info=True)
            return {"error": str(e)}


def get_analytics_repository(db: AsyncSession) -> AnalyticsRepository:
    """获取 AnalyticsRepository 实例"""
    return AnalyticsRepository(db=db)
