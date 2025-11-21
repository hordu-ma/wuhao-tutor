"""
复习计划仓储模块
"""

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.revision_plan import RevisionPlan
from src.repositories.base_repository import BaseRepository


class RevisionPlanRepository(BaseRepository[RevisionPlan]):
    """
    复习计划仓储类
    """

    def __init__(self, db: AsyncSession):
        super().__init__(RevisionPlan, db)

    async def find_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[RevisionPlan], int]:
        """
        查询用户复习计划列表
        """
        stmt = (
            select(RevisionPlan)
            .where(RevisionPlan.user_id == str(user_id))
            .order_by(RevisionPlan.created_at.desc())
        )

        # 分页
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        # 总数
        count_stmt = (
            select(func.count())
            .select_from(RevisionPlan)
            .where(RevisionPlan.user_id == str(user_id))
        )
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar() or 0

        return list(items), total
