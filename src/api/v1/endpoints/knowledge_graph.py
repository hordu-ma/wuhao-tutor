"""
知识图谱 API 端点
提供知识点关联、图谱快照、学习轨迹等功能
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.exceptions import NotFoundError, ServiceError, ValidationError
from src.schemas.knowledge_graph import (
    CreateSnapshotRequest,
    KnowledgeGraphSnapshot,
    LearningCurveResponse,
    MistakeKnowledgePointsResponse,
    UserKnowledgeMasteryResponse,
    WeakKnowledgeChainsResponse,
)
from src.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter()
logger = logging.getLogger(__name__)


# ========== 知识点关联 ==========


@router.get(
    "/mistakes/{mistake_id}/knowledge-points",
    response_model=MistakeKnowledgePointsResponse,
    summary="获取错题关联的知识点",
    description="获取指定错题关联的所有知识点及掌握度信息",
)
async def get_mistake_knowledge_points(
    mistake_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeKnowledgePointsResponse:
    """获取错题关联的知识点"""
    try:
        service = KnowledgeGraphService(db)

        # 获取关联的知识点
        associations = await service.mkp_repo.find_by_mistake(mistake_id)

        # 构建响应
        from src.schemas.knowledge_graph import KnowledgePointAssociation

        kp_list = []
        for assoc in associations:
            # 获取知识点掌握度信息
            kp_id_str = getattr(assoc, "knowledge_point_id", None)
            if not kp_id_str:
                continue

            km = await service._get_knowledge_mastery_by_id(UUID(str(kp_id_str)))
            if not km:
                continue

            # 安全地提取属性
            mastery_value = getattr(km, "mastery_level", None)
            mastery_level = float(str(mastery_value)) if mastery_value else 0.0

            kp_list.append(
                KnowledgePointAssociation(
                    id=UUID(str(getattr(assoc, "id"))),
                    knowledge_point_id=UUID(str(kp_id_str)),
                    knowledge_point_name=str(getattr(km, "knowledge_point", "")),
                    relevance_score=float(str(getattr(assoc, "relevance_score", 0.5))),
                    is_primary=bool(getattr(assoc, "is_primary", False)),
                    error_type=str(getattr(assoc, "error_type", "")),
                    error_reason=getattr(assoc, "error_reason", None),
                    mastery_level=mastery_level,
                    mastered=bool(getattr(assoc, "mastered_after_review", False)),
                    review_count=int(getattr(assoc, "review_count", 0)),
                )
            )

        return MistakeKnowledgePointsResponse(
            mistake_id=mistake_id,
            knowledge_points=kp_list,
            total_count=len(kp_list),
        )

    except Exception as e:
        logger.error(f"获取错题知识点关联失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识点关联失败: {str(e)}",
        )


# ========== 薄弱知识链 ==========


@router.get(
    "/weak-chains",
    response_model=WeakKnowledgeChainsResponse,
    summary="获取薄弱知识链",
    description="识别用户在指定学科的薄弱知识点及其关联关系",
)
async def get_weak_knowledge_chains(
    subject: str = Query(..., description="学科"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeakKnowledgeChainsResponse:
    """获取薄弱知识链"""
    try:
        service = KnowledgeGraphService(db)
        chains = await service.get_weak_knowledge_chains(user_id, subject, limit)

        from src.schemas.knowledge_graph import WeakKnowledgeChain

        chain_list = [WeakKnowledgeChain(**chain) for chain in chains]

        return WeakKnowledgeChainsResponse(
            subject=subject,
            chains=chain_list,
            total_count=len(chain_list),
        )

    except Exception as e:
        logger.error(f"获取薄弱知识链失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取薄弱知识链失败: {str(e)}",
        )


# ========== 知识图谱快照 ==========


@router.post(
    "/snapshots",
    response_model=KnowledgeGraphSnapshot,
    status_code=status.HTTP_201_CREATED,
    summary="创建知识图谱快照",
    description="为用户创建指定学科的知识图谱快照",
)
async def create_snapshot(
    request: CreateSnapshotRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphSnapshot:
    """创建知识图谱快照"""
    try:
        service = KnowledgeGraphService(db)
        snapshot = await service.create_knowledge_graph_snapshot(
            user_id, request.subject, request.period_type
        )

        # 构建响应
        from src.schemas.knowledge_graph import (
            GraphData,
            GraphNode,
            MasteryDistribution,
            WeakKnowledgeChain,
        )

        # 解析图谱数据
        graph_data_raw = getattr(snapshot, "graph_data", {})
        nodes = [GraphNode(**node) for node in graph_data_raw.get("nodes", [])]
        graph_data = GraphData(nodes=nodes, edges=[])

        # 掌握度分布
        mastery_dist_raw = getattr(snapshot, "mastery_distribution", {})
        mastery_dist = MasteryDistribution(
            weak=mastery_dist_raw.get("weak", 0),
            learning=mastery_dist_raw.get("learning", 0),
            mastered=mastery_dist_raw.get("mastered", 0),
        )

        # 薄弱知识链
        weak_chains_raw = getattr(snapshot, "weak_knowledge_chains", [])
        weak_chains = [WeakKnowledgeChain(**chain) for chain in weak_chains_raw]

        return KnowledgeGraphSnapshot(
            id=UUID(str(getattr(snapshot, "id"))),
            user_id=UUID(str(getattr(snapshot, "user_id"))),
            subject=str(getattr(snapshot, "subject")),
            snapshot_date=getattr(snapshot, "snapshot_date"),
            graph_data=graph_data,
            mastery_distribution=mastery_dist,
            weak_knowledge_chains=weak_chains,
            total_knowledge_points=int(getattr(snapshot, "total_knowledge_points", 0)),
            mastered_count=int(getattr(snapshot, "mastered_count", 0)),
            learning_count=int(getattr(snapshot, "learning_count", 0)),
            weak_count=int(getattr(snapshot, "weak_count", 0)),
        )

    except Exception as e:
        logger.error(f"创建知识图谱快照失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建快照失败: {str(e)}",
        )


@router.get(
    "/snapshots/latest",
    response_model=KnowledgeGraphSnapshot,
    summary="获取最新快照",
    description="获取用户指定学科的最新知识图谱快照",
)
async def get_latest_snapshot(
    subject: str = Query(..., description="学科"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphSnapshot:
    """获取最新快照"""
    try:
        service = KnowledgeGraphService(db)
        snapshot = await service.snapshot_repo.find_latest_by_user(user_id, subject)

        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到知识图谱快照，请先创建快照",
            )

        # 构建响应（同上）
        from src.schemas.knowledge_graph import (
            GraphData,
            GraphNode,
            MasteryDistribution,
            WeakKnowledgeChain,
        )

        graph_data_raw = getattr(snapshot, "graph_data", {})
        nodes = [GraphNode(**node) for node in graph_data_raw.get("nodes", [])]
        graph_data = GraphData(nodes=nodes, edges=[])

        mastery_dist_raw = getattr(snapshot, "mastery_distribution", {})
        mastery_dist = MasteryDistribution(
            weak=mastery_dist_raw.get("weak", 0),
            learning=mastery_dist_raw.get("learning", 0),
            mastered=mastery_dist_raw.get("mastered", 0),
        )

        weak_chains_raw = getattr(snapshot, "weak_knowledge_chains", [])
        weak_chains = [WeakKnowledgeChain(**chain) for chain in weak_chains_raw]

        return KnowledgeGraphSnapshot(
            id=UUID(str(getattr(snapshot, "id"))),
            user_id=UUID(str(getattr(snapshot, "user_id"))),
            subject=str(getattr(snapshot, "subject")),
            snapshot_date=getattr(snapshot, "snapshot_date"),
            graph_data=graph_data,
            mastery_distribution=mastery_dist,
            weak_knowledge_chains=weak_chains,
            total_knowledge_points=int(getattr(snapshot, "total_knowledge_points", 0)),
            mastered_count=int(getattr(snapshot, "mastered_count", 0)),
            learning_count=int(getattr(snapshot, "learning_count", 0)),
            weak_count=int(getattr(snapshot, "weak_count", 0)),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最新快照失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取快照失败: {str(e)}",
        )


# ========== 学习轨迹 ==========


@router.get(
    "/knowledge-points/{knowledge_point_id}/learning-curve",
    response_model=LearningCurveResponse,
    summary="获取学习曲线",
    description="获取指定知识点的学习轨迹和掌握度变化曲线",
)
async def get_learning_curve(
    knowledge_point_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> LearningCurveResponse:
    """获取学习曲线"""
    try:
        service = KnowledgeGraphService(db)

        # 获取知识点信息
        km = await service._get_knowledge_mastery_by_id(knowledge_point_id)
        if not km:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识点不存在",
            )

        # 获取学习曲线
        curve_data = await service.track_repo.get_learning_curve(
            user_id, knowledge_point_id
        )

        from src.schemas.knowledge_graph import LearningTrackPoint

        curve = [LearningTrackPoint(**point) for point in curve_data]

        mastery_value = getattr(km, "mastery_level", None)
        current_mastery = float(str(mastery_value)) if mastery_value else 0.0

        return LearningCurveResponse(
            knowledge_point_id=knowledge_point_id,
            knowledge_point_name=str(getattr(km, "knowledge_point", "")),
            current_mastery=current_mastery,
            curve=curve,
            total_activities=len(curve),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习曲线失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习曲线失败: {str(e)}",
        )


# ========== 智能复习推荐 ==========


@router.get(
    "/review/recommendations",
    response_model=list,
    summary="获取智能复习推荐",
    description="基于用户学情、遗忘曲线、前置知识点等多维度推荐复习路径",
)
async def get_review_recommendations(
    subject: str = Query(..., description="学科"),
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取智能复习推荐"""
    try:
        service = KnowledgeGraphService(db)
        recommendations = await service.recommend_review_path(user_id, subject, limit)

        return recommendations

    except Exception as e:
        logger.error(f"获取复习推荐失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取复习推荐失败: {str(e)}",
        )


# ========== 知识点掌握度 ==========


@router.get(
    "/mastery",
    response_model=UserKnowledgeMasteryResponse,
    summary="获取用户知识点掌握度列表",
    description="获取用户在指定学科的所有知识点掌握度信息",
)
async def get_user_knowledge_mastery(
    subject: str = Query(..., description="学科"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserKnowledgeMasteryResponse:
    """获取用户知识点掌握度列表"""
    try:
        from sqlalchemy import and_, select

        from src.models.study import KnowledgeMastery
        from src.schemas.knowledge_graph import KnowledgeMasteryItem

        # 查询知识点掌握度
        stmt = select(KnowledgeMastery).where(
            and_(
                KnowledgeMastery.user_id == str(user_id),
                KnowledgeMastery.subject == subject,
            )
        )
        result = await db.execute(stmt)
        kms = result.scalars().all()

        # 构建响应
        items = []
        total_mastery = 0.0

        for km in kms:
            mastery_value = getattr(km, "mastery_level", None)
            mastery_level = float(str(mastery_value)) if mastery_value else 0.0
            total_mastery += mastery_level

            conf_value = getattr(km, "confidence_level", None)
            confidence_level = float(str(conf_value)) if conf_value else 0.5

            items.append(
                KnowledgeMasteryItem(
                    id=UUID(str(getattr(km, "id"))),
                    knowledge_point=str(getattr(km, "knowledge_point", "")),
                    subject=str(getattr(km, "subject", "")),
                    mastery_level=mastery_level,
                    confidence_level=confidence_level,
                    mistake_count=int(getattr(km, "mistake_count", 0)),
                    correct_count=int(getattr(km, "correct_count", 0)),
                    total_attempts=int(getattr(km, "total_attempts", 0)),
                    last_practiced_at=getattr(km, "last_practiced_at", None),
                    first_mastered_at=getattr(km, "first_mastered_at", None),
                )
            )

        avg_mastery = total_mastery / len(items) if items else 0.0

        return UserKnowledgeMasteryResponse(
            subject=subject,
            items=items,
            total_count=len(items),
            avg_mastery=round(avg_mastery, 2),
        )

    except Exception as e:
        logger.error(f"获取知识点掌握度失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取掌握度失败: {str(e)}",
        )
