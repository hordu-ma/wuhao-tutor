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
from src.models.homework import HomeworkReview, HomeworkSubmission
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

            return {
                "total_study_days": total_study_days,
                "total_questions": total_questions,
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


# ========== 依赖注入 ==========


def get_analytics_service(db: AsyncSession) -> AnalyticsService:
    """获取AnalyticsService实例(依赖注入)"""
    return AnalyticsService(db=db)
