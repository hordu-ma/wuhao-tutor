"""
错题复习记录仓储层
提供复习记录的数据访问方法

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.study import MistakeReview
from src.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class MistakeReviewRepository(BaseRepository[MistakeReview]):
    """错题复习记录仓储"""

    async def find_by_mistake(
        self, mistake_id: UUID, limit: int = 10
    ) -> List[MistakeReview]:
        """
        查询某错题的复习历史（按时间倒序）

        Args:
            mistake_id: 错题ID
            limit: 返回数量限制

        Returns:
            复习记录列表
        """
        stmt = (
            select(MistakeReview)
            .where(MistakeReview.mistake_id == str(mistake_id))
            .order_by(desc(MistakeReview.review_date))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} review records for mistake {mistake_id}"
        )

        return list(items)

    async def get_latest_review(
        self, mistake_id: UUID
    ) -> Optional[MistakeReview]:
        """
        获取最近一次复习记录

        Args:
            mistake_id: 错题ID

        Returns:
            最近的复习记录，如果不存在则返回 None
        """
        stmt = (
            select(MistakeReview)
            .where(MistakeReview.mistake_id == str(mistake_id))
            .order_by(desc(MistakeReview.review_date))
            .limit(1)
        )

        result = await self.db.execute(stmt)
        review = result.scalar_one_or_none()

        logger.debug(
            f"Retrieved latest review for mistake {mistake_id}: {review.id if review else 'None'}"
        )

        return review

    async def calculate_average_mastery(
        self, mistake_id: UUID
    ) -> float:
        """
        计算平均掌握度

        Args:
            mistake_id: 错题ID

        Returns:
            平均掌握度（0.0-1.0）
        """
        stmt = (
            select(func.avg(MistakeReview.mastery_level))
            .where(MistakeReview.mistake_id == str(mistake_id))
        )

        result = await self.db.execute(stmt)
        avg_mastery = result.scalar() or 0.0

        logger.debug(
            f"Calculated average mastery for mistake {mistake_id}: {avg_mastery}"
        )

        return round(float(avg_mastery), 2)

    async def get_review_streak(
        self, user_id: UUID
    ) -> int:
        """
        获取连续复习天数

        计算用户连续复习的天数（从今天向前推算）

        Args:
            user_id: 用户ID

        Returns:
            连续复习天数
        """
        # 获取最近30天的复习记录日期（去重）
        thirty_days_ago = datetime.now() - timedelta(days=30)

        stmt = (
            select(func.date(MistakeReview.review_date).label("review_day"))
            .where(
                and_(
                    MistakeReview.user_id == str(user_id),
                    MistakeReview.review_date >= thirty_days_ago,
                )
            )
            .group_by(func.date(MistakeReview.review_date))
            .order_by(desc(func.date(MistakeReview.review_date)))
        )

        result = await self.db.execute(stmt)
        review_dates = [row[0] for row in result.all()]

        if not review_dates:
            return 0

        # 计算连续天数
        streak = 0
        today = datetime.now().date()

        for i, review_date in enumerate(review_dates):
            # 转换为 date 对象（如果是字符串）
            if isinstance(review_date, str):
                review_date = datetime.fromisoformat(review_date).date()

            expected_date = today - timedelta(days=i)

            if review_date == expected_date:
                streak += 1
            else:
                break

        logger.debug(
            f"Calculated review streak for user {user_id}: {streak} days"
        )

        return streak

    async def find_by_user(
        self, user_id: UUID, limit: int = 50
    ) -> List[MistakeReview]:
        """
        查询用户的所有复习记录

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            复习记录列表
        """
        stmt = (
            select(MistakeReview)
            .where(MistakeReview.user_id == str(user_id))
            .order_by(desc(MistakeReview.review_date))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} review records for user {user_id}"
        )

        return list(items)

    async def count_reviews_by_date_range(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> int:
        """
        统计日期范围内的复习次数

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            复习次数
        """
        stmt = (
            select(func.count())
            .select_from(MistakeReview)
            .where(
                and_(
                    MistakeReview.user_id == str(user_id),
                    MistakeReview.review_date >= start_date,
                    MistakeReview.review_date <= end_date,
                )
            )
        )

        result = await self.db.execute(stmt)
        count = result.scalar() or 0

        logger.debug(
            f"Counted {count} reviews for user {user_id} between {start_date} and {end_date}"
        )

        return count

    async def get_review_accuracy(
        self, user_id: UUID
    ) -> float:
        """
        获取复习正确率

        Args:
            user_id: 用户ID

        Returns:
            正确率百分比（0-100）
        """
        # 统计 correct 结果的数量
        total_stmt = (
            select(func.count())
            .select_from(MistakeReview)
            .where(MistakeReview.user_id == str(user_id))
        )
        result = await self.db.execute(total_stmt)
        total = result.scalar() or 0

        if total == 0:
            return 0.0

        correct_stmt = (
            select(func.count())
            .select_from(MistakeReview)
            .where(
                and_(
                    MistakeReview.user_id == str(user_id),
                    MistakeReview.review_result == "correct",
                )
            )
        )
        result = await self.db.execute(correct_stmt)
        correct = result.scalar() or 0

        accuracy = round(correct / total * 100, 2)

        logger.debug(
            f"Calculated review accuracy for user {user_id}: {accuracy}% ({correct}/{total})"
        )

        return accuracy

    async def get_recent_reviews(
        self, user_id: UUID, days: int = 7
    ) -> List[MistakeReview]:
        """
        获取最近N天的复习记录

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            复习记录列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(MistakeReview)
            .where(
                and_(
                    MistakeReview.user_id == str(user_id),
                    MistakeReview.review_date >= cutoff_date,
                )
            )
            .order_by(desc(MistakeReview.review_date))
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} reviews in the last {days} days for user {user_id}"
        )

        return list(items)
