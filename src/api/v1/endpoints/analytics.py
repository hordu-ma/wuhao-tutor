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
from src.services.analytics_service import get_analytics_service

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


@router.get(
    "/homepage/recommendations",
    summary="获取首页推荐",
    description="基于错题本知识点的每日智能推荐，每天自动更新",
    response_model=DataResponse[list],
)
async def get_homepage_recommendations(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取首页每日推荐（3条）

    **推荐算法:**
    - 基于用户错题本中的知识点
    - 综合考虑掌握度、遗忘曲线、错误率
    - 每24小时自动更新

    **返回数据:**
    每条推荐包含:
    - `id`: 推荐ID
    - `title`: 推荐标题
    - `content`: 推荐内容
    - `icon`: 图标名称
    - `color`: 颜色值
    - `knowledge_point_id`: 知识点ID（可选）
    - `priority`: 优先级分数
    """
    try:
        from datetime import date

        from sqlalchemy import desc, func, select

        from src.models.study import MistakeRecord
        from src.services.knowledge_graph_service import KnowledgeGraphService

        # 1. 获取用户主要学科（从错题统计）
        stmt = (
            select(MistakeRecord.subject, func.count(MistakeRecord.id).label("count"))
            .where(MistakeRecord.user_id == current_user_id)
            .group_by(MistakeRecord.subject)
            .order_by(desc("count"))
            .limit(1)
        )
        result = await db.execute(stmt)
        main_subject_row = result.first()
        main_subject = main_subject_row[0] if main_subject_row else "数学"

        # 2. 调用知识图谱服务的推荐算法
        kg_service = KnowledgeGraphService(db)
        raw_recommendations = await kg_service.recommend_review_path(
            user_id=UUID(current_user_id), subject=main_subject, limit=3
        )

        # 3. 转换为首页展示格式
        recommendations = []
        icon_map = ["star-o", "fire-o", "like-o"]
        color_map = ["#ff9800", "#f44336", "#2196f3"]

        for idx, item in enumerate(raw_recommendations[:3]):
            # 获取知识点名称（字段名是 knowledge_point）
            kp_name = item.get("knowledge_point", "")

            # 如果知识点名称为空，使用默认值
            if not kp_name or kp_name.strip() == "":
                kp_name = "重点知识"

            recommendations.append(
                {
                    "id": f"rec_{date.today().isoformat()}_{idx}",
                    "title": f"{kp_name} 复习",
                    "content": item.get("reason", "建议巩固此知识点，提升掌握度"),
                    "icon": icon_map[idx] if idx < len(icon_map) else "star-o",
                    "color": color_map[idx] if idx < len(color_map) else "#666666",
                    "knowledge_point_id": item.get("knowledge_point_id"),
                    "priority": item.get("priority", 0.5),
                }
            )

        # 4. 如果知识图谱没有推荐，降级到基于错题本的推荐
        if not recommendations:
            # 4.1 查询最近的错题（按创建时间倒序）
            mistake_stmt = (
                select(MistakeRecord)
                .where(MistakeRecord.user_id == current_user_id)
                .order_by(desc(MistakeRecord.created_at))
                .limit(3)
            )
            mistake_result = await db.execute(mistake_stmt)
            recent_mistakes = mistake_result.scalars().all()

            # 4.2 基于错题生成推荐
            for idx, mistake in enumerate(recent_mistakes):
                # 获取学科和知识点
                subject_name = getattr(mistake, "subject", "学科")
                knowledge_points = getattr(mistake, "knowledge_points", [])

                # 构建推荐标题
                if knowledge_points and len(knowledge_points) > 0:
                    kp_name = knowledge_points[0]
                    title = f"{kp_name} 复习"
                    content = f"你在{subject_name}的{kp_name}知识点有错题，建议及时复习"
                else:
                    title = f"{subject_name}错题复习"
                    content = f"你有{subject_name}错题待复习，建议巩固相关知识点"

                recommendations.append(
                    {
                        "id": f"rec_mistake_{date.today().isoformat()}_{idx}",
                        "title": title,
                        "content": content,
                        "icon": icon_map[idx] if idx < len(icon_map) else "star-o",
                        "color": color_map[idx] if idx < len(color_map) else "#666666",
                        "mistake_id": str(getattr(mistake, "id", "")),
                        "priority": 0.8 - (idx * 0.1),  # 最近的优先级更高
                    }
                )

        # 5. 如果仍然没有推荐数据，返回默认提示
        if not recommendations:
            recommendations = [
                {
                    "id": "default_1",
                    "title": "AI学习建议",
                    "content": "根据你的学习习惯，建议每天定时复习",
                    "icon": "star-o",
                    "color": "#ff9800",
                },
                {
                    "id": "default_2",
                    "title": "薄弱科目提升",
                    "content": "物理学科建议加强基础概念的理解",
                    "icon": "fire-o",
                    "color": "#f44336",
                },
                {
                    "id": "default_3",
                    "title": "错题复习计划",
                    "content": "建议每周复习一次错题本，巩固知识点",
                    "icon": "like-o",
                    "color": "#2196f3",
                },
            ]

        return DataResponse(
            success=True, data=recommendations, message="获取首页推荐成功"
        )

    except Exception as e:
        import logging

        logging.error(f"获取首页推荐失败: {e}", exc_info=True)

        # 降级：返回默认推荐
        default_recommendations = [
            {
                "id": "fallback_1",
                "title": "AI学习建议",
                "content": "根据你的学习习惯，建议每天定时复习",
                "icon": "star-o",
                "color": "#ff9800",
            },
            {
                "id": "fallback_2",
                "title": "薄弱科目提升",
                "content": "物理学科建议加强基础概念的理解",
                "icon": "fire-o",
                "color": "#f44336",
            },
            {
                "id": "fallback_3",
                "title": "错题复习计划",
                "content": "建议每周复习一次错题本，巩固知识点",
                "icon": "like-o",
                "color": "#2196f3",
            },
        ]

        return DataResponse(
            success=True, data=default_recommendations, message="使用默认推荐"
        )
