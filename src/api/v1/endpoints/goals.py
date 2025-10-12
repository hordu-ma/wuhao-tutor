"""
目标相关的API端点
"""

from datetime import date, datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.schemas.common import DataResponse
from src.schemas.goal import DailyGoal

logger = get_logger(__name__)

router = APIRouter(prefix="/goals", tags=["目标"])


@router.get(
    "/daily-goals",
    summary="获取每日目标",
    description="获取用户的每日学习目标，包括错题复习、提问、学习时长等",
    response_model=DataResponse[List[DailyGoal]],
)
async def get_daily_goals(
    db: AsyncSession = Depends(get_db),
):
    """
    获取每日目标

    **目标类型:**
    - **review_mistakes**: 错题复习目标
    - **questions**: 提问目标
    - **study_time**: 学习时长目标
    - **record_mistakes**: 记录错题目标

    **返回数据:**
    - 每个目标包含：id, title, type, target, current, completed, progress
    """
    try:
        import uuid

        # 开发环境使用固定的测试用户ID
        current_user_id = "3cf7dbd5-bafc-42f8-9f3d-1493cab87a93"
        user_uuid = uuid.UUID(current_user_id)

        today = datetime.now().date()
        goals = []

        # ========== 1. 错题复习目标 ==========
        # 查询今日需要复习的错题数（这里先用固定值，后续集成 MistakeService）
        try:
            # TODO: 后续替换为 await MistakeService.get_today_review_count(user_uuid)
            review_target = 5  # 固定目标：5 道错题
            review_current = 0  # 暂时设为 0，后续读取实际复习记录

            goals.append(
                {
                    "id": 1,
                    "title": f"复习 {review_target} 道错题",
                    "type": "review_mistakes",
                    "target": review_target,
                    "current": review_current,
                    "completed": review_current >= review_target,
                    "progress": (
                        min(100, int(review_current / review_target * 100))
                        if review_target > 0
                        else 0
                    ),
                    "action_link": "/mistakes/today-review",
                    "description": "基于遗忘曲线的智能复习",
                }
            )
        except Exception as e:
            logger.warning(f"获取错题复习目标失败: {e}")

        # ========== 2. 提问目标 ==========
        try:
            # 查询今日提问数（这里查询真实数据）
            from src.models.learning import LearningQuestion

            question_result = await db.execute(
                select(LearningQuestion).where(
                    and_(
                        LearningQuestion.user_id == user_uuid,
                        LearningQuestion.created_at
                        >= datetime.combine(today, datetime.min.time()),
                    )
                )
            )
            today_questions = len(question_result.scalars().all())

            question_target = 3  # 固定目标：3 次提问
            goals.append(
                {
                    "id": 2,
                    "title": f"完成 {question_target} 次提问",
                    "type": "questions",
                    "target": question_target,
                    "current": today_questions,
                    "completed": today_questions >= question_target,
                    "progress": min(100, int(today_questions / question_target * 100)),
                    "action_link": "/learning",
                    "description": "AI 智能答疑，解决学习难题",
                }
            )
        except Exception as e:
            logger.warning(f"获取提问目标失败: {e}")
            # 查询失败时使用默认值
            goals.append(
                {
                    "id": 2,
                    "title": "完成 3 次提问",
                    "type": "questions",
                    "target": 3,
                    "current": 0,
                    "completed": False,
                    "progress": 0,
                    "action_link": "/learning",
                    "description": "AI 智能答疑，解决学习难题",
                }
            )

        # ========== 3. 学习时长目标 ==========
        # 暂时使用模拟数据，后续可以通过前端埋点统计实际学习时长
        study_target = 30  # 固定目标：30 分钟
        study_current = 0  # 暂时设为 0，后续可通过活动日志计算

        goals.append(
            {
                "id": 3,
                "title": f"学习 {study_target} 分钟",
                "type": "study_time",
                "target": study_target,
                "current": study_current,
                "completed": study_current >= study_target,
                "progress": (
                    min(100, int(study_current / study_target * 100))
                    if study_target > 0
                    else 0
                ),
                "description": "保持每日学习习惯",
            }
        )

        return DataResponse[List[DailyGoal]](
            success=True, data=goals, message="获取每日目标成功"
        )

    except Exception as e:
        logger.error(f"获取每日目标失败 - user_id: {current_user_id}, error: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取每日目标失败: {str(e)}",
        )
