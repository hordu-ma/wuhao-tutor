"""
复习计划 API 端点
"""

import logging
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_user_id
from src.core.database import get_db
from src.core.exceptions import ServiceError
from src.schemas.revision_plan import (
    RevisionPlanDetailResponse,
    RevisionPlanGenerateRequest,
    RevisionPlanListResponse,
)
from src.services.bailian_service import BailianService
from src.services.file_service import FileService
from src.services.mistake_service import MistakeService
from src.services.revision_plan_service import RevisionPlanService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_revision_service(db: AsyncSession = Depends(get_db)) -> RevisionPlanService:
    mistake_service = MistakeService(db)
    bailian_service = BailianService()
    file_service = FileService()
    return RevisionPlanService(db, mistake_service, bailian_service, file_service)


@router.post(
    "/generate",
    response_model=RevisionPlanDetailResponse,
    summary="生成复习计划",
    description="根据错题数据生成个性化复习计划",
)
async def generate_revision_plan(
    request: RevisionPlanGenerateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: RevisionPlanService = Depends(get_revision_service),
):
    try:
        plan = await service.generate_revision_plan(
            user_id=user_id,
            cycle_type=request.cycle_type,
            days_lookback=request.days_lookback,
            force_regenerate=request.force_regenerate,
            title=request.title,
        )
        logger.info(f"📤 返回复习计划: id={plan.id}, title={plan.title}")
        return plan
    except ServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"生成复习计划失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成复习计划失败，请稍后重试",
        )


@router.get(
    "/",
    response_model=RevisionPlanListResponse,
    summary="获取复习计划列表",
)
async def list_revision_plans(
    page: int = 1,
    page_size: int = 10,
    user_id: UUID = Depends(get_current_user_id),
    service: RevisionPlanService = Depends(get_revision_service),
):
    try:
        result = await service.list_revision_plans(
            user_id=user_id, limit=page_size, offset=(page - 1) * page_size
        )
        logger.info(
            f"📋 返回复习计划列表: 共{result['total']}条, "
            f"当前页{len(result['items'])}条, "
            f"IDs={[str(p.id) for p in result['items'][:3]]}"
        )
        return result
    except Exception as e:
        logger.error(f"获取复习计划列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取复习计划列表失败",
        )


@router.get(
    "/{plan_id}",
    response_model=RevisionPlanDetailResponse,
    summary="获取复习计划详情",
)
async def get_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RevisionPlanService = Depends(get_revision_service),
):
    try:
        plan = await service.get_revision_plan(user_id=user_id, plan_id=plan_id)
        return plan
    except ServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取复习计划详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取复习计划详情失败",
        )


@router.get(
    "/{plan_id}/download",
    response_model=Dict[str, str],
    summary="获取复习计划下载链接",
)
async def download_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RevisionPlanService = Depends(get_revision_service),
):
    try:
        url = await service.download_revision_plan(user_id=user_id, plan_id=plan_id)
        return {"url": url}
    except ServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取下载链接失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取下载链接失败",
        )


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除复习计划",
)
async def delete_revision_plan(
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RevisionPlanService = Depends(get_revision_service),
):
    try:
        await service.delete_revision_plan(user_id=user_id, plan_id=plan_id)
    except ServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除复习计划失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除复习计划失败",
        )
