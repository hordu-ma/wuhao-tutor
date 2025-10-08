"""
学情分析API端点 (Analytics Endpoints)

提供学习统计、用户数据、知识图谱等API
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.exceptions import NotFoundError, ServiceError
from src.schemas.analytics import (
    KnowledgePointsResponse,
    LearningProgress,
    SubjectStatsResponse,
)
from src.schemas.common import DataResponse
from src.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["学情分析"])


@router.get(
    "/learning-stats",
    summary="获取学习统计数据",
    description="获取用户的学习统计数据,包括学习天数、问题数、作业数、知识点掌握度等",
    response_model=DataResponse[dict],
)
async def get_learning_stats(
    time_range: str = Query("30d", regex="^(7d|30d|90d|all)$", description="时间范围"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取学习统计数据

    **参数:**
    - **time_range**: 时间范围
      - `7d`: 最近7天
      - `30d`: 最近30天
      - `90d`: 最近90天
      - `all`: 全部时间

    **返回数据:**
    - `total_study_days`: 总学习天数
    - `total_questions`: 总问题数
    - `total_homework`: 总作业数
    - `avg_score`: 平均分
    - `knowledge_points`: 知识点掌握度列表
    - `study_trend`: 学习趋势数据
    """
    try:
        analytics_service = get_analytics_service(db)

        stats = await analytics_service.get_learning_stats(
            user_id=UUID(current_user_id), time_range=time_range
        )

        return DataResponse(success=True, data=stats, message="获取学习统计成功")

    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习统计失败: {str(e)}",
        )


@router.get(
    "/user/stats",
    summary="获取用户统计数据",
    description="获取用户的基本统计数据,用于个人中心展示",
    response_model=DataResponse[dict],
)
async def get_user_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户统计数据

    **返回数据:**
    - `join_date`: 注册日期
    - `last_login`: 最后登录时间
    - `homework_count`: 作业总数
    - `question_count`: 提问总数
    - `study_days`: 学习天数
    - `avg_score`: 平均分
    - `error_count`: 错题数
    - `study_hours`: 学习时长(小时)
    """
    try:
        analytics_service = get_analytics_service(db)

        stats = await analytics_service.get_user_stats(user_id=UUID(current_user_id))

        return DataResponse(success=True, data=stats, message="获取用户统计成功")

    except NotFoundError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}",
        )


@router.get(
    "/knowledge-map",
    summary="获取知识图谱",
    description="获取用户的知识图谱,展示各学科和知识点的掌握情况(可选功能)",
    response_model=DataResponse[dict],
)
async def get_knowledge_map(
    subject: Optional[str] = Query(None, description="学科筛选"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取知识图谱(可选功能)

    **参数:**
    - **subject**: 学科筛选(可选)

    **返回数据:**
    - `knowledge_points`: 知识点列表
    - `total_subjects`: 学科总数
    """
    try:
        analytics_service = get_analytics_service(db)

        knowledge_map = await analytics_service.get_knowledge_map(
            user_id=UUID(current_user_id), subject=subject
        )

        return DataResponse(
            success=True, data=knowledge_map, message="获取知识图谱成功"
        )

    except ServiceError as e:
        # 检查是否是表不存在的错误
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg:
            # 返回空知识图谱
            empty_map = {
                "knowledge_points": [],
                "total_subjects": 0,
                "nodes": [],
                "edges": [],
            }
            return DataResponse(
                success=True, data=empty_map, message="暂无知识图谱数据"
            )
        # 其他服务错误正常抛出
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        # 处理其他未预期的错误
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "undefinedtable" in error_msg:
            # 返回空知识图谱
            empty_map = {
                "knowledge_points": [],
                "total_subjects": 0,
                "nodes": [],
                "edges": [],
            }
            return DataResponse(
                success=True, data=empty_map, message="暂无知识图谱数据"
            )

        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识图谱失败: {str(e)}",
        )


@router.get(
    "/health", summary="Analytics模块健康检查", description="检查学情分析模块的健康状态"
)
async def analytics_health():
    """Analytics模块健康检查"""
    return {"status": "ok", "module": "analytics", "version": "1.0.0"}


@router.get(
    "/learning-progress",
    summary="获取学习进度数据",
    description="获取用户学习进度的趋势分析，支持不同时间粒度查询",
    response_model=DataResponse[LearningProgress],
)
async def get_learning_progress(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    granularity: str = Query(
        "daily", regex="^(daily|weekly|monthly)$", description="时间粒度"
    ),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取学习进度数据

    **参数:**
    - **start_date**: 开始日期，格式 YYYY-MM-DD
    - **end_date**: 结束日期，格式 YYYY-MM-DD
    - **granularity**: 时间粒度
      - `daily`: 按天统计
      - `weekly`: 按周统计
      - `monthly`: 按月统计

    **返回数据:**
    - `period`: 时间周期
    - `start_date`: 开始日期
    - `end_date`: 结束日期
    - `data`: 进度数据列表
    - `summary`: 摘要统计
    """
    try:
        analytics_service = get_analytics_service(db)

        progress = await analytics_service.get_learning_progress(
            user_id=UUID(current_user_id),
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )

        return DataResponse(success=True, data=progress, message="获取学习进度成功")

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"日期格式错误: {str(e)}",
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学习进度失败: {str(e)}",
        )


@router.get(
    "/knowledge-points",
    summary="获取知识点掌握情况",
    description="获取用户各知识点的掌握度统计和分析",
    response_model=DataResponse[KnowledgePointsResponse],
)
async def get_knowledge_points(
    subject: Optional[str] = Query(None, description="学科筛选"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取知识点掌握情况

    **参数:**
    - **subject**: 学科筛选(可选)，如 "数学"、"语文" 等

    **返回数据:**
    - `subject`: 筛选的学科
    - `total_count`: 总知识点数
    - `mastered_count`: 已掌握数量
    - `improving_count`: 提升中数量
    - `weak_count`: 薄弱知识点数量
    - `knowledge_points`: 知识点详细列表
    """
    try:
        analytics_service = get_analytics_service(db)

        knowledge_points = await analytics_service.get_knowledge_points_mastery(
            user_id=UUID(current_user_id), subject=subject
        )

        return DataResponse(
            success=True, data=knowledge_points, message="获取知识点掌握情况成功"
        )

    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识点掌握情况失败: {str(e)}",
        )


@router.get(
    "/subject-stats",
    summary="获取学科统计数据",
    description="获取各学科的学习时长、成绩、进步趋势等统计信息",
    response_model=DataResponse[SubjectStatsResponse],
)
async def get_subject_stats(
    time_range: str = Query("30d", regex="^(7d|30d|90d|all)$", description="时间范围"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取学科统计数据

    **参数:**
    - **time_range**: 时间范围
      - `7d`: 最近7天
      - `30d`: 最近30天
      - `90d`: 最近90天
      - `all`: 全部时间

    **返回数据:**
    - `time_range`: 时间范围
    - `total_subjects`: 总学科数
    - `most_active_subject`: 最活跃学科
    - `strongest_subject`: 最强学科
    - `subjects`: 学科详细统计列表
    - `recommendations`: 学习建议
    """
    try:
        analytics_service = get_analytics_service(db)

        subject_stats = await analytics_service.get_subject_statistics(
            user_id=UUID(current_user_id), time_range=time_range
        )

        return DataResponse(
            success=True, data=subject_stats, message="获取学科统计成功"
        )

    except ServiceError as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学科统计失败: {str(e)}",
        )
