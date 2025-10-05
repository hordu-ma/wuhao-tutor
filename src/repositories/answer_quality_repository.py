"""
答案质量评分仓库
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.answer_quality import AnswerQualityScore
from src.repositories.base_repository import BaseRepository


class AnswerQualityRepository(BaseRepository[AnswerQualityScore]):
    """答案质量评分仓库"""

    def __init__(self, session: AsyncSession):
        super().__init__(AnswerQualityScore, session)

    async def get_by_answer_id(self, answer_id: UUID) -> Optional[AnswerQualityScore]:
        """
        根据答案ID获取评分

        Args:
            answer_id: 答案ID

        Returns:
            答案质量评分或None
        """
        result = await self.db.execute(
            select(AnswerQualityScore).where(AnswerQualityScore.answer_id == answer_id)
        )
        return result.scalar_one_or_none()

    async def get_by_question_id(self, question_id: UUID) -> list[AnswerQualityScore]:
        """
        根据问题ID获取所有答案的评分

        Args:
            question_id: 问题ID

        Returns:
            答案质量评分列表
        """
        result = await self.db.execute(
            select(AnswerQualityScore)
            .where(AnswerQualityScore.question_id == question_id)
            .order_by(AnswerQualityScore.total_score.desc())
        )
        return list(result.scalars().all())

    async def get_high_quality_answers(
        self, min_score: float = 0.8, limit: int = 100
    ) -> list[AnswerQualityScore]:
        """
        获取高质量答案

        Args:
            min_score: 最低分数
            limit: 最大数量

        Returns:
            高质量答案评分列表
        """
        result = await self.db.execute(
            select(AnswerQualityScore)
            .where(AnswerQualityScore.total_score >= min_score)
            .order_by(AnswerQualityScore.total_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
