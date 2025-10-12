"""
错题记录仓储层
提供错题记录的数据访问方法

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.base import is_sqlite
from src.models.study import MistakeRecord
from src.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class MistakeRepository(BaseRepository[MistakeRecord]):
    """错题记录仓储"""

    async def find_by_user(
        self,
        user_id: UUID,
        subject: Optional[str] = None,
        mastery_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MistakeRecord], int]:
        """
        查询用户错题列表

        Args:
            user_id: 用户ID
            subject: 学科筛选 (可选)
            mastery_status: 掌握状态筛选 (可选)
            page: 页码
            page_size: 每页数量

        Returns:
            (错题列表, 总数)
        """
        # 构建基础查询条件
        conditions = [MistakeRecord.user_id == str(user_id)]

        if subject:
            conditions.append(MistakeRecord.subject == subject)

        if mastery_status:
            conditions.append(MistakeRecord.mastery_status == mastery_status)

        # 查询总数
        count_stmt = select(func.count()).select_from(MistakeRecord).where(and_(*conditions))
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        # 查询数据
        offset = (page - 1) * page_size
        stmt = (
            select(MistakeRecord)
            .where(and_(*conditions))
            .order_by(MistakeRecord.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} mistakes for user {user_id}, page {page}, total {total}"
        )

        return list(items), total

    async def find_due_for_review(
        self, user_id: UUID, limit: int = 20
    ) -> List[MistakeRecord]:
        """
        查询今日需要复习的错题

        条件: next_review_at <= now() AND mastery_status != 'mastered'

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            待复习错题列表
        """
        now = datetime.now()

        stmt = (
            select(MistakeRecord)
            .where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    MistakeRecord.next_review_at <= now,
                    MistakeRecord.mastery_status != "mastered",
                )
            )
            .order_by(MistakeRecord.next_review_at.asc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(f"Found {len(items)} mistakes due for review for user {user_id}")

        return list(items)

    async def find_by_knowledge_point(
        self, user_id: UUID, knowledge_point: str
    ) -> List[MistakeRecord]:
        """
        查询包含特定知识点的错题

        使用 JSON 查询，兼容 SQLite 和 PostgreSQL

        Args:
            user_id: 用户ID
            knowledge_point: 知识点名称

        Returns:
            包含该知识点的错题列表
        """
        if is_sqlite:
            # SQLite: 使用 contains 方法
            stmt = select(MistakeRecord).where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    MistakeRecord.knowledge_points.contains(knowledge_point),
                )
            )
        else:
            # PostgreSQL: 使用 @> 运算符
            stmt = select(MistakeRecord).where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    MistakeRecord.knowledge_points.op("@>")(
                        cast([knowledge_point], JSON)
                    ),
                )
            )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} mistakes with knowledge point '{knowledge_point}' for user {user_id}"
        )

        return list(items)

    async def update_mastery_status(
        self, mistake_id: UUID, mastery_status: str, next_review_at: datetime
    ) -> MistakeRecord:
        """
        更新掌握状态和下次复习时间

        Args:
            mistake_id: 错题ID
            mastery_status: 掌握状态
            next_review_at: 下次复习时间

        Returns:
            更新后的错题记录
        """
        update_data = {
            "mastery_status": mastery_status,
            "next_review_at": next_review_at,
            "updated_at": datetime.now(),
        }

        mistake = await self.update(str(mistake_id), update_data)

        logger.debug(
            f"Updated mistake {mistake_id} mastery_status to {mastery_status}, next_review_at to {next_review_at}"
        )

        return mistake

    async def get_statistics(
        self, user_id: UUID, subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计数据

        Args:
            user_id: 用户ID
            subject: 学科筛选 (可选)

        Returns:
            统计数据字典:
            {
                "total": 100,
                "mastered": 30,
                "reviewing": 50,
                "learning": 20,
                "by_subject": {...},
                "by_difficulty": {...}
            }
        """
        # 构建基础条件
        conditions = [MistakeRecord.user_id == str(user_id)]
        if subject:
            conditions.append(MistakeRecord.subject == subject)

        # 总数
        total_stmt = (
            select(func.count()).select_from(MistakeRecord).where(and_(*conditions))
        )
        result = await self.db.execute(total_stmt)
        total = result.scalar() or 0

        # 按掌握状态统计
        mastery_stmt = (
            select(
                MistakeRecord.mastery_status,
                func.count(MistakeRecord.id).label("count"),
            )
            .where(and_(*conditions))
            .group_by(MistakeRecord.mastery_status)
        )
        result = await self.db.execute(mastery_stmt)
        mastery_stats = {row[0]: row[1] for row in result.all()}

        # 按学科统计
        subject_stmt = (
            select(
                MistakeRecord.subject, func.count(MistakeRecord.id).label("count")
            )
            .where(MistakeRecord.user_id == str(user_id))
            .group_by(MistakeRecord.subject)
        )
        result = await self.db.execute(subject_stmt)
        by_subject = {row[0]: row[1] for row in result.all()}

        # 按难度统计
        difficulty_stmt = (
            select(
                MistakeRecord.difficulty_level,
                func.count(MistakeRecord.id).label("count"),
            )
            .where(and_(*conditions))
            .group_by(MistakeRecord.difficulty_level)
        )
        result = await self.db.execute(difficulty_stmt)
        by_difficulty = {str(row[0]): row[1] for row in result.all()}

        stats = {
            "total": total,
            "mastered": mastery_stats.get("mastered", 0),
            "reviewing": mastery_stats.get("reviewing", 0),
            "learning": mastery_stats.get("learning", 0),
            "by_subject": by_subject,
            "by_difficulty": by_difficulty,
        }

        logger.debug(f"Retrieved statistics for user {user_id}: {stats}")

        return stats

    async def find_by_subject_and_difficulty(
        self, user_id: UUID, subject: str, difficulty_level: int
    ) -> List[MistakeRecord]:
        """
        按学科和难度查询错题

        Args:
            user_id: 用户ID
            subject: 学科
            difficulty_level: 难度级别

        Returns:
            符合条件的错题列表
        """
        stmt = select(MistakeRecord).where(
            and_(
                MistakeRecord.user_id == str(user_id),
                MistakeRecord.subject == subject,
                MistakeRecord.difficulty_level == difficulty_level,
            )
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} mistakes for user {user_id}, subject {subject}, difficulty {difficulty_level}"
        )

        return list(items)

    async def get_review_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        获取复习汇总信息

        Args:
            user_id: 用户ID

        Returns:
            复习汇总数据
        """
        # 需要复习的错题数量
        now = datetime.now()
        due_count_stmt = (
            select(func.count())
            .select_from(MistakeRecord)
            .where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    MistakeRecord.next_review_at <= now,
                    MistakeRecord.mastery_status != "mastered",
                )
            )
        )
        result = await self.db.execute(due_count_stmt)
        due_count = result.scalar() or 0

        # 平均复习次数
        avg_review_stmt = (
            select(func.avg(MistakeRecord.review_count))
            .select_from(MistakeRecord)
            .where(MistakeRecord.user_id == str(user_id))
        )
        result = await self.db.execute(avg_review_stmt)
        avg_reviews = result.scalar() or 0

        # 平均正确率
        total_stmt = (
            select(
                func.sum(MistakeRecord.review_count).label("total_reviews"),
                func.sum(MistakeRecord.correct_count).label("total_correct"),
            )
            .select_from(MistakeRecord)
            .where(MistakeRecord.user_id == str(user_id))
        )
        result = await self.db.execute(total_stmt)
        row = result.first()
        total_reviews = row[0] or 0
        total_correct = row[1] or 0
        accuracy = (
            round(total_correct / total_reviews * 100, 2)
            if total_reviews > 0
            else 0.0
        )

        summary = {
            "due_for_review": due_count,
            "average_review_count": round(float(avg_reviews), 2),
            "overall_accuracy": accuracy,
        }

        logger.debug(f"Retrieved review summary for user {user_id}: {summary}")

        return summary

    async def search_mistakes(
        self, user_id: UUID, search_term: str, limit: int = 20
    ) -> List[MistakeRecord]:
        """
        搜索错题（标题、OCR文本）

        Args:
            user_id: 用户ID
            search_term: 搜索关键词
            limit: 返回数量限制

        Returns:
            匹配的错题列表
        """
        search_pattern = f"%{search_term}%"

        stmt = (
            select(MistakeRecord)
            .where(
                and_(
                    MistakeRecord.user_id == str(user_id),
                    or_(
                        MistakeRecord.title.ilike(search_pattern),
                        MistakeRecord.ocr_text.ilike(search_pattern),
                    ),
                )
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        logger.debug(
            f"Found {len(items)} mistakes matching search term '{search_term}' for user {user_id}"
        )

        return list(items)

    async def get_mastery_progress(
        self, user_id: UUID, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取掌握度进度（最近N天）

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            每日掌握度变化列表
        """
        # 这个方法需要配合 MistakeReview 表查询
        # 暂时返回空列表，待 Service 层实现
        logger.debug(
            f"get_mastery_progress called for user {user_id}, days {days} - to be implemented with MistakeReview"
        )
        return []

    async def bulk_update_review_time(
        self, mistake_ids: List[UUID], next_review_at: datetime
    ) -> int:
        """
        批量更新复习时间

        Args:
            mistake_ids: 错题ID列表
            next_review_at: 下次复习时间

        Returns:
            更新的记录数量
        """
        count = 0
        for mistake_id in mistake_ids:
            try:
                await self.update(
                    str(mistake_id),
                    {
                        "next_review_at": next_review_at,
                        "updated_at": datetime.now(),
                    },
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to update mistake {mistake_id}: {e}")

        logger.debug(f"Bulk updated {count} mistakes with next_review_at {next_review_at}")

        return count

    async def get_knowledge_point_distribution(
        self, user_id: UUID
    ) -> Dict[str, int]:
        """
        获取知识点分布统计

        Args:
            user_id: 用户ID

        Returns:
            知识点及其出现次数的字典
        """
        # 由于 knowledge_points 是 JSON 数组，统计比较复杂
        # 需要在应用层展开统计
        stmt = select(MistakeRecord.knowledge_points).where(
            MistakeRecord.user_id == str(user_id)
        )

        result = await self.db.execute(stmt)
        all_kps = result.scalars().all()

        # 统计知识点出现次数
        kp_count: Dict[str, int] = {}
        for kp_list in all_kps:
            if kp_list:
                for kp in kp_list:
                    kp_count[kp] = kp_count.get(kp, 0) + 1

        # 排序并返回 Top 10
        sorted_kps = sorted(kp_count.items(), key=lambda x: x[1], reverse=True)[:10]

        logger.debug(f"Retrieved knowledge point distribution for user {user_id}")

        return dict(sorted_kps)
