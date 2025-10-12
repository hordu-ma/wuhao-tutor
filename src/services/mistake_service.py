"""
错题手册服务层
提供错题管理、复习计划、统计分析等业务逻辑

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ServiceError, ValidationError
from src.models.study import MistakeRecord, MistakeReview
from src.repositories.mistake_repository import MistakeRepository
from src.repositories.mistake_review_repository import MistakeReviewRepository
from src.schemas.mistake import (
    CreateMistakeRequest,
    MasteryProgressResponse,
    MistakeDetailResponse,
    MistakeListItem,
    MistakeListResponse,
    MistakeStatisticsResponse,
    ReviewCompleteRequest,
    ReviewCompleteResponse,
    ReviewHistoryResponse,
    TodayReviewResponse,
    TodayReviewTask,
    UpdateMistakeRequest,
)
from src.services.algorithms.spaced_repetition import SpacedRepetitionAlgorithm

logger = logging.getLogger(__name__)


class MistakeService:
    """错题服务"""

    def __init__(self, db: AsyncSession, bailian_service=None):
        self.db = db
        self.mistake_repo = MistakeRepository(MistakeRecord, db)
        self.review_repo = MistakeReviewRepository(MistakeReview, db)
        self.algorithm = SpacedRepetitionAlgorithm()
        self.bailian_service = bailian_service

    def _to_list_item(self, mistake: MistakeRecord) -> MistakeListItem:
        """转换为列表项"""
        return MistakeListItem(
            id=mistake.id,
            title=mistake.title or "未命名错题",
            subject=mistake.subject,
            difficulty_level=mistake.difficulty_level,
            source=mistake.source,
            source_id=None,
            mastery_status=mistake.mastery_status,
            correct_count=mistake.correct_count,
            total_reviews=mistake.review_count,
            next_review_date=(
                mistake.next_review_at.isoformat() if mistake.next_review_at else None
            ),
            created_at=mistake.created_at.isoformat(),
            knowledge_points=mistake.knowledge_points or [],
        )

    def _to_detail_response(self, mistake: MistakeRecord) -> MistakeDetailResponse:
        """转换为详情响应"""
        return MistakeDetailResponse(
            id=mistake.id,
            title=mistake.title or "未命名错题",
            description=None,
            subject=mistake.subject,
            difficulty_level=mistake.difficulty_level,
            source=mistake.source,
            source_id=None,
            question_content=mistake.ocr_text or "",
            student_answer=None,
            correct_answer=None,
            explanation=None,
            knowledge_points=mistake.knowledge_points or [],
            mastery_status=mistake.mastery_status,
            correct_count=mistake.correct_count,
            total_reviews=mistake.review_count,
            next_review_date=(
                mistake.next_review_at.isoformat() if mistake.next_review_at else None
            ),
            created_at=mistake.created_at.isoformat(),
            updated_at=mistake.updated_at.isoformat(),
            image_urls=mistake.image_urls or [],
        )

    async def get_mistake_list(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        filters: Optional[Dict] = None,
    ) -> MistakeListResponse:
        """
        获取错题列表

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            filters: 筛选条件（subject, mastery_status等）

        Returns:
            错题列表响应
        """
        subject = filters.get("subject") if filters else None
        mastery_status = filters.get("mastery_status") if filters else None

        items, total = await self.mistake_repo.find_by_user(
            user_id=user_id,
            subject=subject,
            mastery_status=mastery_status,
            page=page,
            page_size=page_size,
        )

        return MistakeListResponse(
            items=[self._to_list_item(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_mistake_detail(
        self, mistake_id: UUID, user_id: UUID
    ) -> MistakeDetailResponse:
        """
        获取错题详情

        Args:
            mistake_id: 错题ID
            user_id: 用户ID

        Returns:
            错题详情响应
        """
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))

        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        return self._to_detail_response(mistake)

    async def create_mistake(
        self, user_id: UUID, request: CreateMistakeRequest
    ) -> MistakeDetailResponse:
        """
        创建错题

        Args:
            user_id: 用户ID
            request: 创建请求

        Returns:
            错题详情响应
        """
        # 构造数据
        data = {
            "user_id": str(user_id),
            "subject": request.subject,
            "title": request.title,
            "ocr_text": request.question_content,
            "image_urls": request.image_urls,
            "difficulty_level": request.difficulty_level or 2,
            "knowledge_points": request.knowledge_points,
            "mastery_status": "learning",
            "next_review_at": datetime.now() + timedelta(days=1),
            "source": "manual",
        }

        # 创建记录
        mistake = await self.mistake_repo.create(data)

        logger.info(f"Created mistake {mistake.id} for user {user_id}")

        return self._to_detail_response(mistake)

    async def update_mistake(
        self, mistake_id: UUID, user_id: UUID, request: UpdateMistakeRequest
    ) -> MistakeDetailResponse:
        """
        更新错题

        Args:
            mistake_id: 错题ID
            user_id: 用户ID
            request: 更新请求

        Returns:
            更新后的错题详情
        """
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))

        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.notes is not None:
            update_data["notes"] = request.notes
        if request.tags is not None:
            update_data["tags"] = request.tags

        if update_data:
            mistake = await self.mistake_repo.update(str(mistake_id), update_data)

        logger.info(f"Updated mistake {mistake_id}")

        return self._to_detail_response(mistake)

    async def delete_mistake(self, mistake_id: UUID, user_id: UUID) -> None:
        """
        删除错题

        Args:
            mistake_id: 错题ID
            user_id: 用户ID
        """
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))

        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        await self.mistake_repo.delete(str(mistake_id))

        logger.info(f"Deleted mistake {mistake_id}")

    async def get_today_review_tasks(self, user_id: UUID) -> TodayReviewResponse:
        """
        获取今日复习任务

        Args:
            user_id: 用户ID

        Returns:
            今日复习任务响应
        """
        mistakes = await self.mistake_repo.find_due_for_review(user_id=user_id, limit=50)

        tasks = []
        total_minutes = 0

        for mistake in mistakes:
            tasks.append(
                TodayReviewTask(
                    id=mistake.id,
                    mistake_id=mistake.id,
                    title=mistake.title or "未命名错题",
                    subject=mistake.subject,
                    review_round=mistake.review_count + 1,
                    due_date=mistake.next_review_at.isoformat()
                    if mistake.next_review_at
                    else datetime.now().isoformat(),
                    question_content=mistake.ocr_text or "",
                    image_urls=mistake.image_urls or [],
                )
            )
            total_minutes += mistake.estimated_time or 5

        logger.info(
            f"Retrieved {len(tasks)} review tasks for user {user_id}, estimated {total_minutes} minutes"
        )

        return TodayReviewResponse(
            tasks=tasks,
            total_count=len(tasks),
            completed_count=0,
            estimated_minutes=total_minutes,
        )

    async def complete_review(
        self, mistake_id: UUID, user_id: UUID, request: ReviewCompleteRequest
    ) -> ReviewCompleteResponse:
        """
        完成复习

        Args:
            mistake_id: 错题ID
            user_id: 用户ID
            request: 复习完成请求

        Returns:
            复习完成响应
        """
        # 1. 获取错题并验证归属
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))
        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        # 2. 创建复习记录数据
        review_data = {
            "mistake_id": str(mistake_id),
            "user_id": str(user_id),
            "review_date": datetime.now(),
            "review_result": request.review_result,
            "time_spent": request.time_spent,
            "confidence_level": request.confidence_level,
            "user_answer": request.user_answer,
            "notes": request.notes,
            "review_method": "manual",
        }

        # 3. 获取复习历史并计算掌握度
        review_history = await self.review_repo.find_by_mistake(mistake_id)
        current_mastery = self.algorithm.calculate_mastery_level(review_history)

        # 4. 计算下次复习时间
        next_review, interval = self.algorithm.calculate_next_review(
            review_count=mistake.review_count,
            review_result=request.review_result,
            current_mastery=current_mastery,
            last_review_date=datetime.now(),
        )

        # 5. 更新复习记录数据
        review_data["mastery_level"] = current_mastery
        review_data["next_review_date"] = next_review
        review_data["interval_days"] = interval

        # 6. 保存复习记录
        review = await self.review_repo.create(review_data)

        # 7. 更新错题状态
        update_data = {
            "review_count": mistake.review_count + 1,
            "last_review_at": datetime.now(),
            "next_review_at": next_review,
        }

        if request.review_result == "correct":
            update_data["correct_count"] = mistake.correct_count + 1

        # 8. 判断是否已掌握
        consecutive_correct = (
            update_data.get("correct_count", mistake.correct_count)
        )
        is_mastered = self.algorithm.is_mastered(
            mastery_level=current_mastery,
            consecutive_correct=consecutive_correct,
            min_reviews=3,
        )

        if is_mastered:
            update_data["mastery_status"] = "mastered"
        elif current_mastery >= 0.5:
            update_data["mastery_status"] = "reviewing"

        await self.mistake_repo.update(str(mistake_id), update_data)

        logger.info(
            f"Completed review for mistake {mistake_id}, mastery: {current_mastery}, next review: {next_review}"
        )

        return ReviewCompleteResponse(
            review_id=review.id,
            mastery_level=current_mastery,
            next_review_date=next_review,
            is_mastered=is_mastered,
        )

    async def get_review_history(
        self, mistake_id: UUID, user_id: UUID
    ) -> ReviewHistoryResponse:
        """
        获取复习历史

        Args:
            mistake_id: 错题ID
            user_id: 用户ID

        Returns:
            复习历史响应
        """
        # 验证权限
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))
        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        # 获取复习历史
        reviews = await self.review_repo.find_by_mistake(mistake_id, limit=50)

        # 计算平均掌握度
        avg_mastery = await self.review_repo.calculate_average_mastery(mistake_id)

        # 最新掌握度
        latest_mastery = reviews[0].mastery_level if reviews else 0.0

        from src.schemas.mistake import ReviewHistoryItem

        items = [
            ReviewHistoryItem(
                id=r.id,
                review_date=r.review_date,
                review_result=r.review_result,
                mastery_level=float(r.mastery_level),
                time_spent=r.time_spent,
                confidence_level=r.confidence_level,
                notes=r.notes,
            )
            for r in reviews
        ]

        return ReviewHistoryResponse(
            items=items,
            total=len(reviews),
            average_mastery=avg_mastery,
            latest_mastery=float(latest_mastery),
        )

    async def get_statistics(self, user_id: UUID) -> MistakeStatisticsResponse:
        """
        获取错题统计

        Args:
            user_id: 用户ID

        Returns:
            统计响应
        """
        stats = await self.mistake_repo.get_statistics(user_id)

        # 获取连续复习天数
        streak_days = await self.review_repo.get_review_streak(user_id)

        # 本周复习次数
        week_start = datetime.now() - timedelta(days=7)
        week_reviews = await self.review_repo.count_reviews_by_date_range(
            user_id, week_start, datetime.now()
        )

        return MistakeStatisticsResponse(
            total_mistakes=stats["total"],
            not_mastered=stats["learning"],
            reviewing=stats["reviewing"],
            mastered=stats["mastered"],
            by_subject=stats["by_subject"],
            by_difficulty=stats["by_difficulty"],
            review_streak_days=streak_days,
            this_week_reviews=week_reviews,
        )

    async def get_mastery_progress(
        self, user_id: UUID, days: int = 7
    ) -> MasteryProgressResponse:
        """
        获取掌握度进度

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            掌握度进度响应
        """
        # 获取最近N天的复习记录
        reviews = await self.review_repo.get_recent_reviews(user_id, days)

        # 按日期分组统计
        from collections import defaultdict

        daily_stats = defaultdict(lambda: {"sum": 0.0, "count": 0})

        for review in reviews:
            date_str = review.review_date.date().isoformat()
            daily_stats[date_str]["sum"] += float(review.mastery_level)
            daily_stats[date_str]["count"] += 1

        # 构建进度项
        from src.schemas.mistake import MasteryProgressItem

        items = []
        for date_str in sorted(daily_stats.keys()):
            stats = daily_stats[date_str]
            avg_mastery = stats["sum"] / stats["count"] if stats["count"] > 0 else 0.0
            items.append(
                MasteryProgressItem(
                    date=date_str,
                    mastery_level=round(avg_mastery, 2),
                    review_count=stats["count"],
                )
            )

        # 计算趋势
        trend = "stable"
        improvement = 0.0
        if len(items) >= 2:
            first_mastery = items[0].mastery_level
            last_mastery = items[-1].mastery_level
            improvement = last_mastery - first_mastery

            if improvement > 0.1:
                trend = "up"
            elif improvement < -0.1:
                trend = "down"

        return MasteryProgressResponse(
            items=items, trend=trend, improvement=round(improvement, 2)
        )

    async def analyze_mistake_with_ai(
        self, mistake_id: UUID, user_id: UUID
    ) -> Dict:
        """
        使用AI分析错题

        Args:
            mistake_id: 错题ID
            user_id: 用户ID

        Returns:
            AI分析结果
        """
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))
        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        if not self.bailian_service:
            raise ServiceError("AI服务未配置")

        # TODO: 集成百炼AI服务分析知识点和错误原因
        logger.warning("AI analysis not fully implemented")

        return {
            "knowledge_points": mistake.knowledge_points or [],
            "error_reasons": mistake.error_reasons or [],
            "suggestions": [],
        }
