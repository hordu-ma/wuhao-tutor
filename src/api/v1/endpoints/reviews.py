from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.study import MistakeRecord
from src.repositories.mistake_repository import MistakeRepository
from src.repositories.review_repository import ReviewRepository
from src.schemas.review import ReviewAnswerSubmitRequest, ReviewSessionStartRequest
from src.services.bailian_service import BailianService
from src.services.review_service import ReviewService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", status_code=201)
async def start_review_session(
    request: ReviewSessionStartRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """启动一个新的复习会话"""
    try:
        logger.info(
            f"Starting review session for user {user_id}, mistake {request.mistake_id}"
        )
        # 创建 Service 实例
        review_repo = ReviewRepository(db)
        mistake_repo = MistakeRepository(MistakeRecord, db)
        bailian_service = BailianService()
        review_service = ReviewService(db, review_repo, mistake_repo, bailian_service)

        session_data = await review_service.start_review_session(
            user_id=user_id, mistake_id=request.mistake_id
        )
        logger.info(
            f"Review session created successfully: {session_data.get('session_id')}"
        )
        return session_data
    except ValueError as e:
        logger.error(f"Validation error in review session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"参数验证失败: {str(e)}")
    except Exception as e:
        logger.error(
            f"Failed to start review session: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}")
async def get_review_session(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取复习会话状态"""
    try:
        # 创建 Service 实例
        review_repo = ReviewRepository(db)
        mistake_repo = MistakeRepository(MistakeRecord, db)
        bailian_service = BailianService()
        review_service = ReviewService(db, review_repo, mistake_repo, bailian_service)

        session_data = await review_service.get_review_session(
            session_id=session_id, user_id=user_id
        )
        return session_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{session_id}/submit")
async def submit_review_answer(
    session_id: UUID,
    request: ReviewAnswerSubmitRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """提交复习答案（AI判断版本）"""
    try:
        logger.info(
            f"Submitting answer for session {session_id}, user {user_id}: "
            f"answer={request.answer[:50] if request.answer else 'None'}, "
            f"skip={request.skip}"
        )
        # 创建 Service 实例
        review_repo = ReviewRepository(db)
        mistake_repo = MistakeRepository(MistakeRecord, db)
        bailian_service = BailianService()
        review_service = ReviewService(db, review_repo, mistake_repo, bailian_service)

        result = await review_service.submit_review_answer(
            session_id=session_id,
            user_id=user_id,
            answer=request.answer or "",
            skip=request.skip,
        )
        logger.info(f"Answer submission successful: {result}")
        return result
    except Exception as e:
        logger.error(
            f"Failed to submit answer for session {session_id}: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))
