from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.study import MistakeRecord
from src.repositories.mistake_repository import MistakeRepository
from src.repositories.review_repository import ReviewRepository
from src.services.bailian_service import BailianService
from src.services.review_service import ReviewService


async def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    review_repo = ReviewRepository(db)
    mistake_repo = MistakeRepository(MistakeRecord, db)
    bailian_service = BailianService()
    return ReviewService(db, review_repo, mistake_repo, bailian_service)
