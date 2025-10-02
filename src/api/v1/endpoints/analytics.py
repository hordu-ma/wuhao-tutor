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
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
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
