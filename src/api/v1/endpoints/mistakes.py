"""
错题手册 API 端点
提供错题管理、复习计划、统计分析等功能
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.exceptions import NotFoundError, ServiceError, ValidationError
from src.schemas.common import SuccessResponse
from src.schemas.mistake import (
    CreateMistakeRequest,
    MistakeDetailResponse,
    MistakeListResponse,
    MistakeStatisticsResponse,
    ReviewCompleteRequest,
    ReviewCompleteResponse,
    TodayReviewResponse,
)
from src.services.mistake_service import MistakeService

router = APIRouter()
logger = logging.getLogger(__name__)


# ========== 错题管理 ==========


@router.get(
    "/",
    response_model=MistakeListResponse,
    summary="获取错题列表",
    description="分页查询用户的错题列表,支持按学科、掌握状态、知识点、错题分类、来源、关键词筛选",
)
async def get_mistake_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    mastery_status: Optional[str] = Query(None, description="掌握状态筛选"),
    knowledge_point: Optional[str] = Query(None, description="知识点筛选"),
    category: Optional[str] = Query(
        None, description="错题分类筛选(empty_question/wrong_answer/hard_question)"
    ),
    source: Optional[str] = Query(
        None, description="来源筛选(learning_empty/learning_wrong/learning_hard/manual)"
    ),
    search: Optional[str] = Query(None, description="关键词搜索"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeListResponse:
    """获取错题列表"""
    try:
        # 🔍 临时调试日志 - 记录所有筛选参数
        logger.info(
            f"""
=== 错题列表筛选参数 ===
user_id: {user_id}
subject: {subject}
mastery_status: {mastery_status}
knowledge_point: {knowledge_point}
category: {category}
source: {source}
search: {search}
===========================
        """
        )

        service = MistakeService(db)

        # 构建筛选条件
        filters = {}
        if subject:
            filters["subject"] = subject
        if mastery_status:
            filters["mastery_status"] = mastery_status
        if knowledge_point:
            filters["knowledge_point"] = knowledge_point
        if category:
            filters["category"] = category
        if source:
            filters["source"] = source
        if search:
            filters["search"] = search

        result = await service.get_mistake_list(
            user_id=user_id,
            page=page,
            page_size=page_size,
            filters=filters,
        )

        return result
    except ServiceError as e:
        logger.error(f"获取错题列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错题列表失败: {str(e)}",
        )


# ========== 统计分析 ========== (移到这里，避免被 {mistake_id} 拦截)


@router.get(
    "/statistics",
    response_model=MistakeStatisticsResponse,
    summary="获取错题统计",
    description="获取用户的错题统计数据,包括总数、掌握情况、学科分布等",
)
async def get_mistake_statistics(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeStatisticsResponse:
    """获取错题统计"""
    try:
        service = MistakeService(db)
        statistics = await service.get_statistics(user_id)
        return statistics
    except ServiceError as e:
        logger.error(f"获取错题统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错题统计失败: {str(e)}",
        )


@router.get(
    "/{mistake_id}",
    response_model=MistakeDetailResponse,
    summary="获取错题详情",
    description="获取指定错题的详细信息",
)
async def get_mistake_detail(
    mistake_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeDetailResponse:
    """获取错题详情"""
    try:
        service = MistakeService(db)
        mistake = await service.get_mistake_detail(mistake_id, user_id)
        return mistake
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        logger.error(f"获取错题详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错题详情失败: {str(e)}",
        )


@router.post(
    "/",
    response_model=MistakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建错题",
    description="手动添加错题到错题本",
)
async def create_mistake(
    request: CreateMistakeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeDetailResponse:
    """创建错题"""
    try:
        service = MistakeService(db)
        mistake = await service.create_mistake(user_id, request)
        return mistake
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ServiceError as e:
        logger.error(f"创建错题失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建错题失败: {str(e)}",
        )


@router.delete(
    "/{mistake_id}",
    response_model=SuccessResponse,
    summary="删除错题",
    description="删除指定的错题",
)
async def delete_mistake(
    mistake_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """删除错题"""
    try:
        service = MistakeService(db)
        await service.delete_mistake(mistake_id, user_id)
        return SuccessResponse(message="错题删除成功")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        logger.error(f"删除错题失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除错题失败: {str(e)}",
        )


# ========== 复习管理 ==========


@router.get(
    "/today-review",
    response_model=TodayReviewResponse,
    summary="获取今日复习任务",
    description="获取今天需要复习的错题列表(基于艾宾浩斯遗忘曲线)",
)
async def get_today_review_tasks(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TodayReviewResponse:
    """获取今日复习任务"""
    try:
        service = MistakeService(db)
        tasks = await service.get_today_review_tasks(user_id)
        return tasks
    except ServiceError as e:
        logger.error(f"获取今日复习任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取今日复习任务失败: {str(e)}",
        )


@router.post(
    "/{mistake_id}/review",
    response_model=ReviewCompleteResponse,
    summary="完成复习",
    description="提交错题复习结果,系统将根据结果更新掌握状态和下次复习时间",
)
async def complete_review(
    mistake_id: UUID,
    request: ReviewCompleteRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ReviewCompleteResponse:
    """完成复习"""
    try:
        service = MistakeService(db)
        result = await service.complete_review(mistake_id, user_id, request)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ServiceError as e:
        logger.error(f"完成复习失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成复习失败: {str(e)}",
        )
