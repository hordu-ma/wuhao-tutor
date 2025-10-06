"""
用户相关API端点
包含用户信息、活动记录等接口
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.endpoints.auth import get_current_user_id
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.homework import HomeworkSubmission
from src.schemas.common import DataResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/activities",
    summary="获取用户最近活动",
    description="获取当前用户的最近活动记录",
    response_model=DataResponse[List[Dict[str, Any]]],
)
async def get_user_activities(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户最近活动

    **查询参数:**
    - **limit**: 返回记录数量限制，默认10条    **返回数据:**
    - **id**: 活动ID
    - **type**: 活动类型 (question/homework/study)
    - **title**: 活动标题
    - **time**: 活动时间
    - **status**: 活动状态
    """
    try:
        import uuid

        # 开发环境使用固定的测试用户ID
        current_user_id = "3cf7dbd5-bafc-42f8-9f3d-1493cab87a93"
        user_uuid = uuid.UUID(current_user_id)

        activities = []

        # 获取最近的作业提交记录
        homework_result = await db.execute(
            select(HomeworkSubmission)
            .where(HomeworkSubmission.student_id == user_uuid)
            .order_by(desc(HomeworkSubmission.created_at))
            .limit(limit // 2)
        )
        homework_submissions = homework_result.scalars().all()

        for submission in homework_submissions:
            activities.append(
                {
                    "id": f"homework_{submission.id}",
                    "type": "homework",
                    "title": f"作业提交：{submission.submission_title or '未命名作业'}",
                    "time": (
                        submission.created_at.isoformat()
                        if submission.created_at is not None
                        else datetime.now().isoformat()
                    ),
                    "status": get_submission_status_text(str(submission.status)),
                }
            )

        # 获取最近的学习会话记录（暂时禁用，因为模型不存在）
        # try:
        #     learning_result = await db.execute(
        #         select(LearningSession)
        #         .where(LearningSession.user_id == user_uuid)
        #         .order_by(desc(LearningSession.created_at))
        #         .limit(limit // 2)
        #     )
        #     learning_sessions = learning_result.scalars().all()
        #
        #     for session in learning_sessions:
        #         activities.append({
        #             "id": f"learning_{session.id}",
        #             "type": "study",
        #             "title": f"学习会话：{session.session_name or '学习记录'}",
        #             "time": session.created_at.isoformat() if session.created_at else datetime.now().isoformat(),
        #             "status": "已完成" if session.completed_at else "进行中",
        #         })
        # except Exception as e:
        #     # 如果学习会话表不存在，继续使用作业数据
        #     logger.warning(f"学习会话表不存在或查询失败: {e}")

        # 如果没有真实数据，添加一些示例数据
        if not activities:
            now = datetime.now()
            activities = [
                {
                    "id": "demo_1",
                    "type": "question",
                    "title": "提问：三角函数的应用",
                    "time": (now - timedelta(hours=2)).isoformat(),
                    "status": "已解答",
                },
                {
                    "id": "demo_2",
                    "type": "homework",
                    "title": "数学作业：二次函数练习",
                    "time": (now - timedelta(hours=5)).isoformat(),
                    "status": "已批改",
                },
                {
                    "id": "demo_3",
                    "type": "study",
                    "title": "完成英语单词学习",
                    "time": (now - timedelta(days=1)).isoformat(),
                    "status": "已完成",
                },
            ]

        # 按时间排序并限制数量
        activities.sort(key=lambda x: x["time"], reverse=True)
        activities = activities[:limit]

        return DataResponse[List[Dict[str, Any]]](
            success=True, data=activities, message="获取用户活动成功"
        )

    except Exception as e:
        logger.error(f"获取用户活动失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户活动失败: {str(e)}",
        )


def get_submission_status_text(status: str) -> str:
    """转换提交状态为中文"""
    status_map = {
        "uploaded": "已上传",
        "processing": "处理中",
        "reviewed": "已批改",
        "failed": "失败",
        "archived": "已归档",
    }
    return status_map.get(status, status)


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
    - **pendingHomework**: 待批改作业数
    """
    try:
        import uuid

        # 开发环境使用固定的测试用户ID
        current_user_id = "3cf7dbd5-bafc-42f8-9f3d-1493cab87a93"
        user_uuid = uuid.UUID(current_user_id)

        # 查询用户作业统计
        today = datetime.now().date()

        # 总作业数
        total_homework_result = await db.execute(
            select(HomeworkSubmission).where(HomeworkSubmission.student_id == user_uuid)
        )
        total_homework = len(total_homework_result.scalars().all())

        # 待批改作业数
        pending_homework_result = await db.execute(
            select(HomeworkSubmission).where(
                and_(
                    HomeworkSubmission.student_id == user_uuid,
                    or_(
                        HomeworkSubmission.status == "uploaded",
                        HomeworkSubmission.status == "processing",
                    ),
                )
            )
        )
        pending_homework = len(pending_homework_result.scalars().all())

        # 生成基本统计数据
        stats = {
            "totalPoints": 1250,  # 示例积分
            "studyDays": 45,  # 示例学习天数
            "questions": 3,  # 示例今日提问数
            "pendingHomework": pending_homework,
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
