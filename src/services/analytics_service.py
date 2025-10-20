"""
学情分析服务 (Analytics Service)

提供学习数据统计、知识点分析、学习趋势等功能
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ServiceError
from src.models.homework import Homework, HomeworkReview, HomeworkSubmission
from src.models.learning import Answer, ChatSession, Question
from src.models.user import User

logger = logging.getLogger("analytics_service")


class AnalyticsService:
    """学情分析服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_learning_stats(
        self, user_id: UUID, time_range: str = "30d"
    ) -> Dict[str, Any]:
        """
        获取学习统计数据

        Args:
            user_id: 用户ID
            time_range: 时间范围 (7d, 30d, 90d, all)

        Returns:
            学习统计数据字典
        """
        try:
            # 计算时间范围
            start_date = self._calculate_start_date(time_range)

            # 并行查询多个数据源
            total_study_days = await self._count_study_days(user_id, start_date)
            total_questions = await self._count_questions(user_id, start_date)
            total_homework = await self._count_homework(user_id, start_date)
            avg_score = await self._calculate_avg_score(user_id, start_date)
            knowledge_points = await self._analyze_knowledge_points(user_id, start_date)
            study_trend = await self._get_study_trend(user_id, start_date)

            # 新增统计
            total_sessions = await self._count_sessions(user_id, start_date)
            rating_stats = await self._get_rating_stats(user_id, start_date)
            subject_stats = await self._get_subject_stats(user_id, start_date)
            learning_pattern = await self._analyze_learning_pattern(user_id, start_date)

            return {
                # 新格式（小程序前端需要的字段）
                "total_questions": total_questions,
                "total_sessions": total_sessions,
                "total_study_days": total_study_days,
                "avg_rating": rating_stats["avg_rating"],
                "positive_feedback_rate": rating_stats["positive_rate"],
                "subject_stats": subject_stats,
                "learning_pattern": learning_pattern,
                # 保留原有字段（保持向后兼容）
                "total_homework": total_homework,
                "avg_score": avg_score,
                "knowledge_points": knowledge_points,
                "study_trend": study_trend,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取学习统计失败: {e}", exc_info=True)
            raise ServiceError(f"获取学习统计失败: {str(e)}")

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        获取用户统计数据

        Args:
            user_id: 用户ID

        Returns:
            用户统计数据字典
        """
        try:
            # 查询用户基本信息
            user_stmt = select(User).where(User.id == str(user_id))
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                raise NotFoundError(f"用户 {user_id} 不存在")

            # 查询作业统计
            homework_stmt = select(
                func.count(HomeworkSubmission.id).label("count"),
                func.avg(HomeworkSubmission.total_score).label("avg_score"),
            ).where(HomeworkSubmission.student_id == str(user_id))
            homework_result = await self.db.execute(homework_stmt)
            homework_stats = homework_result.one()

            # 查询问答统计
            question_stmt = select(func.count(Question.id).label("count")).where(
                Question.user_id == str(user_id)
            )
            question_result = await self.db.execute(question_stmt)
            question_count = question_result.scalar() or 0

            # 计算学习天数
            study_days = await self._count_study_days(user_id, None)

            # 计算学习时长(估算:每个问答5分钟,每个作业15分钟)
            homework_count = (
                int(homework_stats[0]) if homework_stats and homework_stats[0] else 0
            )
            estimated_hours = (question_count * 5 + homework_count * 15) / 60

            return {
                "join_date": (
                    str(user.created_at)
                    if hasattr(user, "created_at") and user.created_at is not None
                    else None
                ),
                "last_login": (
                    str(user.updated_at)
                    if hasattr(user, "updated_at") and user.updated_at is not None
                    else None
                ),
                "homework_count": homework_count,
                "question_count": question_count,
                "study_days": study_days,
                "avg_score": round(
                    float(homework_stats.avg_score) if homework_stats.avg_score else 0,
                    1,
                ),
                "error_count": 0,  # TODO: 从错题本获取
                "study_hours": round(estimated_hours, 1),
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}", exc_info=True)
            raise ServiceError(f"获取用户统计失败: {str(e)}")

    async def get_knowledge_map(
        self, user_id: UUID, subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识图谱(可选功能)

        Args:
            user_id: 用户ID
            subject: 学科筛选

        Returns:
            知识图谱数据
        """
        try:
            # 查询问题和作业数据
            conditions = [Question.user_id == str(user_id)]
            if subject:
                conditions.append(Question.subject == subject)

            question_stmt = select(Question).where(and_(*conditions))
            question_result = await self.db.execute(question_stmt)
            questions = question_result.scalars().all()

            # 简单的知识点提取(基于topic字段)
            knowledge_map: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {"count": 0, "topics": []}
            )

            for question in questions:
                # 修复: 使用 is not None 而不是直接布尔检查
                subject_key = (
                    str(question.subject) if question.subject is not None else "其他"
                )
                topic = str(question.topic) if question.topic is not None else "未分类"

                knowledge_map[subject_key]["count"] += 1
                if topic not in knowledge_map[subject_key]["topics"]:
                    knowledge_map[subject_key]["topics"].append(topic)

            # 转换为列表格式
            result = [
                {
                    "subject": subject_key,
                    "question_count": data["count"],
                    "topics": data["topics"][:10],  # 限制数量
                }
                for subject_key, data in knowledge_map.items()
            ]

            return {
                "knowledge_points": result,
                "total_subjects": len(result),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取知识图谱失败: {e}", exc_info=True)
            raise ServiceError(f"获取知识图谱失败: {str(e)}")

    # ========== 私有辅助方法 ==========

    def _calculate_start_date(self, time_range: str) -> Optional[datetime]:
        """计算开始日期"""
        if time_range == "all":
            return None

        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 30)
        return datetime.utcnow() - timedelta(days=days)

    async def _count_study_days(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> int:
        """计算学习天数"""
        try:
            # 从问答和作业记录计算活跃天数
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            stmt = (
                select(func.date(Question.created_at))
                .where(and_(*conditions))
                .distinct()
            )

            result = await self.db.execute(stmt)
            return len(result.all())

        except Exception as e:
            logger.warning(f"计算学习天数失败: {e}")
            return 0

    async def _count_questions(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> int:
        """统计问题数量"""
        try:
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            stmt = select(func.count(Question.id)).where(and_(*conditions))
            result = await self.db.execute(stmt)
            return result.scalar() or 0

        except Exception as e:
            logger.warning(f"统计问题数量失败: {e}")
            return 0

    async def _count_homework(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> int:
        """统计作业数量"""
        try:
            conditions = [HomeworkSubmission.student_id == str(user_id)]
            if start_date:
                conditions.append(HomeworkSubmission.created_at >= start_date)

            stmt = select(func.count(HomeworkSubmission.id)).where(and_(*conditions))
            result = await self.db.execute(stmt)
            return result.scalar() or 0

        except Exception as e:
            logger.warning(f"统计作业数量失败: {e}")
            return 0

    async def _calculate_avg_score(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> float:
        """计算平均分"""
        try:
            conditions = [
                HomeworkSubmission.student_id == str(user_id),
                HomeworkSubmission.total_score.isnot(None),
            ]
            if start_date:
                conditions.append(HomeworkSubmission.created_at >= start_date)

            stmt = select(func.avg(HomeworkSubmission.total_score)).where(
                and_(*conditions)
            )
            result = await self.db.execute(stmt)
            avg_score = result.scalar()

            return round(avg_score, 1) if avg_score else 0.0

        except Exception as e:
            logger.warning(f"计算平均分失败: {e}")
            return 0.0

    async def _analyze_knowledge_points(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """分析知识点掌握情况"""
        try:
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            # 按topic分组统计
            stmt = (
                select(Question.topic, func.count(Question.id).label("count"))
                .where(and_(*conditions), Question.topic.isnot(None))
                .group_by(Question.topic)
                .order_by(desc("count"))
                .limit(10)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            # 计算掌握度(简化版:基于问题数量估算)
            # 修复: row是元组,row[1]是count值
            total_questions = sum(int(row[1]) for row in rows)

            knowledge_points = []
            for row in rows:
                count_val = int(row[1]) if row[1] else 1  # row[1]是count
                mastery_level = min(count_val / 10.0, 1.0)  # 每10个问题提升10%

                knowledge_points.append(
                    {
                        "name": row[0],  # row[0]是topic
                        "mastery_level": round(mastery_level, 2),
                        "question_count": count_val,
                    }
                )

            return knowledge_points

        except Exception as e:
            logger.warning(f"分析知识点失败: {e}")
            return []

    async def _get_study_trend(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """获取学习趋势"""
        try:
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            # 按日期分组统计
            stmt = (
                select(
                    func.date(Question.created_at).label("date"),
                    func.count(Question.id).label("activity"),
                )
                .where(and_(*conditions))
                .group_by(func.date(Question.created_at))
                .order_by("date")
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            return [{"date": str(row.date), "activity": row.activity} for row in rows]

        except Exception as e:
            logger.warning(f"获取学习趋势失败: {e}")
            return []

    async def get_learning_progress(
        self, user_id: UUID, start_date: str, end_date: str, granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        获取学习进度数据

        Args:
            user_id: 用户ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            granularity: 时间粒度 (daily/weekly/monthly)

        Returns:
            学习进度数据
        """
        try:
            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            # 检测数据库类型
            is_sqlite = "sqlite" in str(self.db.bind.engine.url)

            # 根据粒度和数据库类型调整查询
            if granularity == "weekly":
                if is_sqlite:
                    # SQLite: 使用strftime获取周开始日期
                    date_format = func.date(
                        HomeworkSubmission.created_at,
                        "-"
                        + func.strftime("%w", HomeworkSubmission.created_at)
                        + " days",
                    )
                else:
                    # PostgreSQL: 使用date_trunc
                    date_format = func.date_trunc("week", HomeworkSubmission.created_at)
            elif granularity == "monthly":
                if is_sqlite:
                    # SQLite: 使用strftime格式化为月份开始
                    date_format = func.strftime(
                        "%Y-%m-01", HomeworkSubmission.created_at
                    )
                else:
                    # PostgreSQL: 使用date_trunc
                    date_format = func.date_trunc(
                        "month", HomeworkSubmission.created_at
                    )
            else:  # daily
                date_format = func.date(HomeworkSubmission.created_at)

            # 查询作业进度数据
            homework_stmt = (
                select(
                    date_format.label("period"),
                    func.count(HomeworkSubmission.id).label("homework_count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.count(func.nullif(HomeworkSubmission.status, "pending")).label(
                        "completed_count"
                    ),
                )
                .where(
                    and_(
                        HomeworkSubmission.student_id == str(user_id),
                        HomeworkSubmission.created_at >= start_dt,
                        HomeworkSubmission.created_at <= end_dt,
                    )
                )
                .group_by(date_format)
                .order_by(date_format)
            )

            homework_result = await self.db.execute(homework_stmt)
            homework_data = homework_result.all()

            # 查询问答进度数据
            question_stmt = (
                select(
                    date_format.label("period"),
                    func.count(Question.id).label("question_count"),
                )
                .where(
                    and_(
                        Question.user_id == str(user_id),
                        Question.created_at >= start_dt,
                        Question.created_at <= end_dt,
                    )
                )
                .group_by(date_format)
                .order_by(date_format)
            )

            question_result = await self.db.execute(question_stmt)
            question_data = {
                row.period: row.question_count for row in question_result.all()
            }

            # 合并数据
            progress_data = []
            total_homework = 0
            total_questions = 0
            total_score_sum = 0
            score_count = 0

            for row in homework_data:
                period_str = (
                    str(row.period.date())
                    if hasattr(row.period, "date")
                    else str(row.period)
                )
                question_count = question_data.get(row.period, 0)

                completion_rate = (
                    row.completed_count / row.homework_count
                    if row.homework_count > 0
                    else 0
                )
                accuracy_rate = row.avg_score / 100.0 if row.avg_score else 0

                progress_data.append(
                    {
                        "date": period_str,
                        "study_duration": (row.homework_count + question_count)
                        * 15,  # 估算学习时长
                        "completion_rate": completion_rate,
                        "accuracy_rate": accuracy_rate,
                        "homework_count": row.homework_count,
                        "question_count": question_count,
                    }
                )

                total_homework += row.homework_count
                total_questions += question_count
                if row.avg_score:
                    total_score_sum += row.avg_score
                    score_count += 1

            # 计算摘要统计
            summary = {
                "total_homework": total_homework,
                "total_questions": total_questions,
                "avg_accuracy": (
                    total_score_sum / score_count / 100.0 if score_count > 0 else 0
                ),
                "total_study_duration": sum(
                    item["study_duration"] for item in progress_data
                ),
            }

            return {
                "period": granularity,
                "start_date": start_date,
                "end_date": end_date,
                "data": progress_data,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"获取学习进度失败: {e}", exc_info=True)
            raise ServiceError(f"获取学习进度失败: {str(e)}")

    async def get_knowledge_points_mastery(
        self, user_id: UUID, subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取知识点掌握情况

        Args:
            user_id: 用户ID
            subject: 学科筛选(可选)

        Returns:
            知识点掌握数据
        """
        try:
            # 基于作业批改结果分析知识点掌握情况
            # 这里使用简化的实现，实际可以结合知识图谱

            conditions = [HomeworkSubmission.student_id == str(user_id)]
            if subject:
                conditions.append(HomeworkSubmission.subject == subject)

            # 查询作业中的知识点表现
            stmt = (
                select(
                    HomeworkSubmission.subject,
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.count(HomeworkSubmission.id).label("attempts"),
                    func.max(HomeworkSubmission.created_at).label("last_practice"),
                )
                .where(and_(*conditions))
                .group_by(HomeworkSubmission.subject)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            knowledge_points = []
            mastered_count = 0
            improving_count = 0
            weak_count = 0

            for i, row in enumerate(rows):
                mastery_level = row.avg_score / 100.0 if row.avg_score else 0
                accuracy_rate = mastery_level

                # 简化的趋势分析
                if mastery_level >= 0.8:
                    trend = "stable"
                    mastered_count += 1
                elif mastery_level >= 0.6:
                    trend = "improving"
                    improving_count += 1
                else:
                    trend = "declining"
                    weak_count += 1

                knowledge_points.append(
                    {
                        "id": f"kp_{i+1}",
                        "name": f"{row.subject}核心知识点",
                        "subject": row.subject,
                        "mastery_level": mastery_level,
                        "accuracy_rate": accuracy_rate,
                        "total_attempts": row.attempts,
                        "correct_attempts": int(row.attempts * accuracy_rate),
                        "last_practice": row.last_practice,
                        "trend": trend,
                    }
                )

            return {
                "subject": subject,
                "total_count": len(knowledge_points),
                "mastered_count": mastered_count,
                "improving_count": improving_count,
                "weak_count": weak_count,
                "knowledge_points": knowledge_points,
            }

        except Exception as e:
            logger.error(f"获取知识点掌握情况失败: {e}", exc_info=True)
            raise ServiceError(f"获取知识点掌握情况失败: {str(e)}")

    async def get_subject_statistics(
        self, user_id: UUID, time_range: str = "30d"
    ) -> Dict[str, Any]:
        """
        获取学科统计数据

        Args:
            user_id: 用户ID
            time_range: 时间范围

        Returns:
            学科统计数据
        """
        try:
            start_date = self._calculate_start_date(time_range)

            # 查询学科统计数据
            conditions = [HomeworkSubmission.student_id == str(user_id)]
            if start_date:
                conditions.append(HomeworkSubmission.created_at >= start_date)

            homework_stmt = (
                select(
                    HomeworkSubmission.subject,
                    func.count(HomeworkSubmission.id).label("homework_count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                    func.max(HomeworkSubmission.created_at).label("last_study"),
                    func.sum(func.coalesce(HomeworkSubmission.time_spent, 30)).label(
                        "study_duration"
                    ),
                )
                .where(and_(*conditions))
                .group_by(HomeworkSubmission.subject)
                .order_by(desc("avg_score"))
            )

            homework_result = await self.db.execute(homework_stmt)
            homework_data = homework_result.all()

            # 查询问答统计
            question_conditions = [Question.user_id == str(user_id)]
            if start_date:
                question_conditions.append(Question.created_at >= start_date)

            question_stmt = (
                select(
                    Question.subject,
                    func.count(Question.id).label("question_count"),
                )
                .where(and_(*question_conditions))
                .group_by(Question.subject)
            )

            question_result = await self.db.execute(question_stmt)
            question_data = {
                row.subject: row.question_count for row in question_result.all()
            }

            # 合并并处理数据
            subjects = []
            total_subjects = len(homework_data)
            best_subject = None
            most_active_subject = None
            max_score = 0
            max_activity = 0

            for i, row in enumerate(homework_data):
                if not row.subject:
                    continue

                subject = row.subject
                question_count = question_data.get(subject, 0)
                activity_score = row.homework_count + question_count

                # 计算进步率(简化实现)
                improvement_rate = (
                    min(row.avg_score / 60.0, 1.0) * 100 if row.avg_score else 0
                )

                subjects.append(
                    {
                        "subject": subject,
                        "study_duration": row.study_duration
                        or (row.homework_count * 30),
                        "homework_count": row.homework_count,
                        "question_count": question_count,
                        "avg_score": row.avg_score or 0,
                        "accuracy_rate": (row.avg_score or 0) / 100.0,
                        "improvement_rate": improvement_rate,
                        "last_study": row.last_study,
                        "weak_knowledge_points": [],  # 可以进一步实现
                        "rank": i + 1,
                    }
                )

                # 跟踪最佳和最活跃学科
                if row.avg_score and row.avg_score > max_score:
                    max_score = row.avg_score
                    best_subject = subject

                if activity_score > max_activity:
                    max_activity = activity_score
                    most_active_subject = subject

            # 生成学习建议
            recommendations = []
            if subjects:
                weak_subjects = [s for s in subjects if s["avg_score"] < 60]
                if weak_subjects:
                    recommendations.append(
                        f"建议加强 {weak_subjects[0]['subject']} 的练习"
                    )

                if best_subject:
                    recommendations.append(f"保持 {best_subject} 的优秀表现")

                if len(subjects) >= 3:
                    recommendations.append("均衡发展各学科，避免偏科")

            return {
                "time_range": time_range,
                "total_subjects": total_subjects,
                "most_active_subject": most_active_subject,
                "strongest_subject": best_subject,
                "subjects": subjects,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"获取学科统计失败: {e}", exc_info=True)
            raise ServiceError(f"获取学科统计失败: {str(e)}")

    async def _count_sessions(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> int:
        """
        统计会话数

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            会话总数
        """
        try:
            from src.models.learning import ChatSession

            conditions = [ChatSession.user_id == str(user_id)]
            if start_date:
                conditions.append(ChatSession.created_at >= start_date)

            stmt = select(func.count(ChatSession.id)).where(and_(*conditions))
            result = await self.db.execute(stmt)
            count = result.scalar() or 0

            return int(count)

        except Exception as e:
            logger.warning(f"统计会话数失败: {e}")
            return 0

    async def _get_rating_stats(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """
        统计评分数据

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            评分统计字典 {avg_rating, positive_rate}
        """
        try:
            from src.models.learning import Answer, Question

            # 构建查询条件
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            # 查询所有评分
            stmt = (
                select(Answer.user_rating)
                .join(Question, Question.id == Answer.question_id)
                .where(and_(*conditions))
                .where(Answer.user_rating.isnot(None))
            )

            result = await self.db.execute(stmt)
            ratings = [row[0] for row in result.all()]

            if not ratings:
                return {"avg_rating": 0.0, "positive_rate": 0.0}

            # 计算平均评分
            avg_rating = sum(ratings) / len(ratings)

            # 计算好评率（评分>=4为好评）
            positive_count = sum(1 for r in ratings if r >= 4)
            positive_rate = (positive_count / len(ratings)) * 100

            return {
                "avg_rating": round(avg_rating, 1),
                "positive_rate": round(positive_rate, 1),
            }

        except Exception as e:
            logger.warning(f"统计评分失败: {e}")
            return {"avg_rating": 0.0, "positive_rate": 0.0}

    async def _get_subject_stats(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """
        统计学科分布

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            学科统计列表
        """
        try:
            from src.models.learning import Answer, Question

            # 构建查询条件
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            # 按学科分组统计
            stmt = (
                select(
                    Question.subject,
                    func.count(Question.id).label("question_count"),
                    func.avg(Answer.user_rating).label("avg_rating"),
                )
                .outerjoin(Answer, Question.id == Answer.question_id)
                .where(and_(*conditions))
                .where(Question.subject.isnot(None))
                .group_by(Question.subject)
            )

            result = await self.db.execute(stmt)
            rows = result.all()

            subject_stats = []
            for row in rows:
                subject_stats.append(
                    {
                        "subject": row.subject,
                        "subject_name": row.subject,  # 可以添加中文映射
                        "question_count": int(row.question_count or 0),
                        "avg_rating": round(float(row.avg_rating or 0), 1),
                    }
                )

            return subject_stats

        except Exception as e:
            logger.warning(f"统计学科分布失败: {e}")
            return []

    async def _analyze_learning_pattern(
        self, user_id: UUID, start_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """
        分析学习模式

        Args:
            user_id: 用户ID
            start_date: 开始日期

        Returns:
            学习模式字典
        """
        try:
            from src.models.learning import ChatSession, Question

            # 构建查询条件
            conditions = [Question.user_id == str(user_id)]
            if start_date:
                conditions.append(Question.created_at >= start_date)

            # 查询所有问题的创建时间和难度
            stmt = select(
                Question.created_at, Question.difficulty_level, Question.session_id
            ).where(and_(*conditions))

            result = await self.db.execute(stmt)
            rows = result.all()

            if not rows:
                return {
                    "most_active_hour": 0,
                    "most_active_day": 0,
                    "avg_session_length": 0,
                    "preferred_difficulty": "medium",
                }

            # 分析最活跃时段（小时）
            hour_counts = {}
            day_counts = {}
            difficulty_counts = {}

            for row in rows:
                if row.created_at:
                    # 解析时间字符串
                    if isinstance(row.created_at, str):
                        dt = datetime.fromisoformat(
                            row.created_at.replace("Z", "+00:00")
                        )
                    else:
                        dt = row.created_at

                    hour = dt.hour
                    weekday = dt.weekday()

                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    day_counts[weekday] = day_counts.get(weekday, 0) + 1

                if row.difficulty_level:
                    difficulty_counts[row.difficulty_level] = (
                        difficulty_counts.get(row.difficulty_level, 0) + 1
                    )

            # 找出最活跃时段和日期
            most_active_hour = (
                max(hour_counts, key=hour_counts.get) if hour_counts else 0
            )
            most_active_day = max(day_counts, key=day_counts.get) if day_counts else 0

            # 找出偏好难度
            difficulty_map = {1: "easy", 2: "easy", 3: "medium", 4: "hard", 5: "hard"}
            preferred_difficulty = "medium"
            if difficulty_counts:
                avg_difficulty = sum(k * v for k, v in difficulty_counts.items()) / sum(
                    difficulty_counts.values()
                )
                preferred_difficulty = difficulty_map.get(
                    round(avg_difficulty), "medium"
                )

            # 计算平均会话时长（会话中的问题数作为时长估算）
            session_counts = {}
            for row in rows:
                if row.session_id:
                    session_counts[row.session_id] = (
                        session_counts.get(row.session_id, 0) + 1
                    )

            avg_session_length = 0
            if session_counts:
                # 估算：每个问题5分钟
                avg_questions = sum(session_counts.values()) / len(session_counts)
                avg_session_length = int(avg_questions * 5)

            return {
                "most_active_hour": most_active_hour,
                "most_active_day": most_active_day,
                "avg_session_length": avg_session_length,
                "preferred_difficulty": preferred_difficulty,
            }

        except Exception as e:
            logger.warning(f"分析学习模式失败: {e}")
            return {
                "most_active_hour": 0,
                "most_active_day": 0,
                "avg_session_length": 0,
                "preferred_difficulty": "medium",
            }


# ========== 依赖注入 ==========


def get_analytics_service(db: AsyncSession) -> AnalyticsService:
    """获取AnalyticsService实例(依赖注入)"""
    return AnalyticsService(db=db)
