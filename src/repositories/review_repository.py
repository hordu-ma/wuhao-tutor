from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.review import MistakeReviewSession
from src.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[MistakeReviewSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(MistakeReviewSession, db)

    async def find_by_id(self, session_id: UUID) -> Optional[MistakeReviewSession]:
        """
        根据ID查找复习会话

        Args:
            session_id: 会话ID

        Returns:
            复习会话对象，不存在返回None
        """
        return await self.get_by_id(str(session_id))
