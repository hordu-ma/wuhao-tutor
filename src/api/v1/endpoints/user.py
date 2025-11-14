"""
用户相关API端点
包含用户信息、活动记录等接口
"""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.learning import Question
from src.schemas.common import DataResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/activities",
    summary="获取用户最近活动",
    description="获取当前用户的最近活动记录(作业问答)",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_user_activities(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户最近活动 - 仅作业问答记录

    **查询参数:**
    - **limit**: 返回记录数量限制，默认10条

    **返回数据:**
    - **id**: 活动ID
    - **type**: 活动类型 (question)
    - **title**: 活动标题
    - **time**: 活动时间
    - **status**: 活动状态 (answered/pending)
    """
    try:
        import uuid

        # 开发环境使用固定的测试用户ID
        current_user_id = "3cf7dbd5-bafc-42f8-9f3d-1493cab87a93"
        user_uuid = uuid.UUID(current_user_id)

        activities = []

        # 查询最近的作业问答记录
        try:
            question_result = await db.execute(
                select(Question)
                .where(Question.user_id == user_uuid)
                .order_by(desc(Question.created_at))
                .limit(limit)
            )
            questions = question_result.scalars().all()

            for question in questions:
                # 截取问题内容前30个字符作为标题
                title_content = (
                    question.content[:30] if question.content else "未知问题"
                )
                if len(question.content or "") > 30:
                    title_content += "..."

                activities.append(
                    {
                        "id": str(question.id),
                        "type": "question",
                        "title": f"提问：{title_content}",
                        "time": (
                            question.created_at.isoformat()
                            if question.created_at is not None
                            else datetime.now().isoformat()
                        ),
                        "status": "answered" if question.answer else "pending",
                    }
                )
        except Exception as e:
            logger.warning(f"查询作业问答记录失败: {e}")

        # 按时间排序(已经在查询中排序,这里保留以防万一)
        activities.sort(key=lambda x: x["time"], reverse=True)

        return DataResponse[List[Dict[str, Any]]](
            success=True, data=activities, message="获取用户活动成功"
        )

    except Exception as e:
        logger.error(f"获取用户活动失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动失败: {str(e)}",
        )


@router.get(
    "/stats",
    summary="获取用户统计信息",
    description="获取当前用户的基本统计数据",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户统计信息

    **返回数据:**
    - **totalPoints**: 总积分
    - **studyDays**: 学习天数
    - **questions**: 今日提问数
    - **pendingHomework**: 待解答问题数(兼容前端字段名)
    """
    try:
        import uuid

        from sqlalchemy import func

        # 开发环境使用固定的测试用户ID
        current_user_id = "3cf7dbd5-bafc-42f8-9f3d-1493cab87a93"
        user_uuid = uuid.UUID(current_user_id)

        # 查询今日提问数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_questions_count = 0
        pending_questions_count = 0

        try:
            # 今日提问数
            today_result = await db.execute(
                select(func.count(Question.id)).where(
                    and_(
                        Question.user_id == user_uuid,
                        Question.created_at >= today_start,
                    )
                )
            )
            today_questions_count = today_result.scalar() or 0

            # 待解答问题数(没有answer的问题)
            pending_result = await db.execute(
                select(func.count(Question.id)).where(
                    and_(
                        Question.user_id == user_uuid,
                        Question.answer == None,  # noqa: E711
                    )
                )
            )
            pending_questions_count = pending_result.scalar() or 0
        except Exception as e:
            logger.warning(f"查询问题统计失败，使用默认值: {e}")
            today_questions_count = 0
            pending_questions_count = 0

        # 生成基本统计数据
        stats = {
            "totalPoints": 1250,  # 示例积分
            "studyDays": 45,  # 示例学习天数
            "questions": today_questions_count,  # 真实的今日提问数
            "pendingHomework": pending_questions_count,  # 待解答问题数(兼容前端字段名)
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=stats, message="获取用户统计成功"
        )

    except Exception as e:
        logger.error(f"获取用户统计失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}",
        )


@router.get(
    "/preferences",
    summary="获取用户偏好设置",
    description="获取当前用户的学习偏好配置",
    response_model=DataResponse[Dict[str, Any]],
)
async def get_user_preferences(
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    获取用户偏好设置

    **返回数据:**
    - **preferred_subjects**: 偏好学科列表
    - **preferred_input**: 偏好输入方式 (text/image/voice)
    - **difficulty_level**: 偏好难度 (easy/medium/hard)
    """
    try:
        # TODO: 从数据库获取用户偏好，当前返回默认值
        default_preferences = {
            "preferred_subjects": ["math", "chinese", "english"],
            "preferred_input": "text",
            "difficulty_level": "medium",
            "learning_style": "balanced",
        }

        return DataResponse[Dict[str, Any]](
            success=True, data=default_preferences, message="获取用户偏好成功"
        )

    except Exception as e:
        logger.error(f"获取用户偏好失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户偏好失败: {str(e)}",
        )


@router.put(
    "/preferences",
    summary="更新用户偏好设置",
    description="更新当前用户的学习偏好配置",
    response_model=DataResponse[Dict[str, Any]],
)
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    更新用户偏好设置

    **请求参数:**
    - **preferred_subjects**: 偏好学科列表
    - **preferred_input**: 偏好输入方式
    - **difficulty_level**: 偏好难度
    """
    try:
        # TODO: 保存用户偏好到数据库
        logger.info(
            f"用户偏好更新 - user_id: {current_user_id}, preferences: {preferences}"
        )

        return DataResponse[Dict[str, Any]](
            success=True, data=preferences, message="更新用户偏好成功"
        )

    except Exception as e:
        logger.error(f"更新用户偏好失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户偏好失败: {str(e)}",
        )
