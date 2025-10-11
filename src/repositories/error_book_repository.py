"""
错题本数据访问层
提供错题和复习记录的数据库操作接口
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.models.error_book import ErrorQuestion, ReviewRecord, ErrorClassification, MasteryStatus
from src.repositories.base_repository import BaseRepository


class ErrorBookRepository(BaseRepository[ErrorQuestion]):
    """错题本数据访问层"""

    def __init__(self, session: AsyncSession):
        super().__init__(ErrorQuestion, session)

    async def get_user_error_questions(
        self,
        user_id: str,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[int] = None,
        sort: str = "created_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[ErrorQuestion], int]:
        """
        获取用户的错题列表（分页）
        
        Args:
            user_id: 用户ID
            subject: 学科筛选
            status: 掌握状态筛选
            category: 错误分类筛选
            difficulty: 难度筛选
            sort: 排序字段
            order: 排序顺序
            page: 页码
            limit: 每页数量
            
        Returns:
            (错题列表, 总数)
        """
        # 构建查询条件
        conditions = [ErrorQuestion.user_id == user_id]
        
        if subject:
            conditions.append(ErrorQuestion.subject == subject)
        if status:
            conditions.append(ErrorQuestion.mastery_status == status)
        if category:
            conditions.append(ErrorQuestion.error_type == category)
        if difficulty:
            conditions.append(ErrorQuestion.difficulty_level == difficulty)

        # 构建排序
        sort_column = getattr(ErrorQuestion, sort, ErrorQuestion.created_at)
        if order.lower() == "desc":
            sort_column = desc(sort_column)

        # 查询总数
        count_stmt = select(func.count()).select_from(ErrorQuestion).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询数据
        stmt = (
            select(ErrorQuestion)
            .where(and_(*conditions))
            .order_by(sort_column)
            .offset((page - 1) * limit)
            .limit(limit)
            .options(selectinload(ErrorQuestion.review_records))
        )

        result = await self.session.execute(stmt)
        error_questions = result.scalars().all()

        return list(error_questions), total

    async def get_user_error_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户错题统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        # 基础统计
        total_stmt = select(func.count()).select_from(ErrorQuestion).where(ErrorQuestion.user_id == user_id)
        total_result = await self.session.execute(total_stmt)
        total_errors = total_result.scalar() or 0

        # 按状态统计
        status_stmt = (
            select(ErrorQuestion.mastery_status, func.count())
            .where(ErrorQuestion.user_id == user_id)
            .group_by(ErrorQuestion.mastery_status)
        )
        status_result = await self.session.execute(status_stmt)
        status_counts = dict(status_result.all())

        # 按学科统计
        subject_stmt = (
            select(ErrorQuestion.subject, func.count())
            .where(ErrorQuestion.user_id == user_id)
            .group_by(ErrorQuestion.subject)
        )
        subject_result = await self.session.execute(subject_stmt)
        subject_counts = dict(subject_result.all())

        # 按错误类型统计
        category_stmt = (
            select(ErrorQuestion.error_type, func.count())
            .where(ErrorQuestion.user_id == user_id)
            .group_by(ErrorQuestion.error_type)
        )
        category_result = await self.session.execute(category_stmt)
        category_counts = dict(category_result.all())

        # 本周新增
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_stmt = (
            select(func.count())
            .select_from(ErrorQuestion)
            .where(
                and_(
                    ErrorQuestion.user_id == user_id,
                    ErrorQuestion.created_at >= week_ago.isoformat()
                )
            )
        )
        weekly_result = await self.session.execute(weekly_stmt)
        weekly_new = weekly_result.scalar() or 0

        # 掌握率计算
        mastered = status_counts.get(MasteryStatus.MASTERED, 0)
        mastery_rate = round(mastered / total_errors, 2) if total_errors > 0 else 0.0

        return {
            "overview": {
                "total_errors": total_errors,
                "weekly_new": weekly_new,
                "mastery_rate": mastery_rate,
                "mastered": mastered,
                "reviewing": status_counts.get(MasteryStatus.REVIEWING, 0),
                "learning": status_counts.get(MasteryStatus.LEARNING, 0),
            },
            "by_subject": [
                {"subject": subject, "count": count, "percentage": round(count / total_errors, 2)}
                for subject, count in subject_counts.items()
            ] if total_errors > 0 else [],
            "by_category": [
                {"category": category, "count": count, "percentage": round(count / total_errors, 2)}
                for category, count in category_counts.items()
            ] if total_errors > 0 else [],
        }

    async def get_review_recommendations(
        self, user_id: str, limit: int = 10
    ) -> List[ErrorQuestion]:
        """
        获取复习推荐
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            推荐复习的错题列表
        """
        now = datetime.utcnow()
        
        # 构建复杂查询：逾期复习 + 优先级排序
        stmt = (
            select(ErrorQuestion)
            .where(
                and_(
                    ErrorQuestion.user_id == user_id,
                    ErrorQuestion.mastery_status != MasteryStatus.MASTERED,
                    or_(
                        ErrorQuestion.next_review_at.is_(None),
                        ErrorQuestion.next_review_at <= now
                    )
                )
            )
            .order_by(
                # 逾期天数越多越优先
                desc(
                    func.coalesce(
                        func.extract('epoch', text(f"'{now.isoformat()}'::timestamp") - ErrorQuestion.next_review_at) / 86400,
                        0
                    )
                ),
                # 难度越高越优先
                desc(ErrorQuestion.difficulty_level),
                # 错误次数越多越优先（通过review_count倒推）
                desc(ErrorQuestion.review_count)
            )
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_errors(
        self, user_id: str, days: int = 30, subject: Optional[str] = None
    ) -> List[ErrorQuestion]:
        """
        获取最近的错题记录
        
        Args:
            user_id: 用户ID
            days: 天数范围
            subject: 学科筛选
            
        Returns:
            最近错题列表
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        conditions = [
            ErrorQuestion.user_id == user_id,
            ErrorQuestion.created_at >= since_date.isoformat()
        ]
        
        if subject:
            conditions.append(ErrorQuestion.subject == subject)
        
        stmt = (
            select(ErrorQuestion)
            .where(and_(*conditions))
            .order_by(desc(ErrorQuestion.review_count), desc(ErrorQuestion.created_at))
            .limit(10)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_weak_knowledge_points(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取薄弱知识点分析
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            薄弱知识点列表
        """
        # 这里需要更复杂的查询来分析知识点
        # 由于knowledge_points是JSON字段，需要特殊处理
        stmt = text("""
            SELECT 
                jsonb_array_elements_text(knowledge_points) as knowledge_point,
                COUNT(*) as error_count,
                AVG(CASE WHEN mastery_status = 'mastered' THEN 1.0 ELSE 0.0 END) as mastery_rate
            FROM error_questions 
            WHERE user_id = :user_id 
                AND knowledge_points IS NOT NULL 
                AND jsonb_array_length(knowledge_points) > 0
            GROUP BY jsonb_array_elements_text(knowledge_points)
            HAVING COUNT(*) >= 2
            ORDER BY error_count DESC, mastery_rate ASC
            LIMIT :limit
        """)
        
        result = await self.session.execute(stmt, {"user_id": user_id, "limit": limit})
        
        return [
            {
                "knowledge_point": row[0],
                "error_count": row[1],
                "mastery_rate": float(row[2]) if row[2] else 0.0,
                "suggestion": f"建议重点复习{row[0]}相关内容"
            }
            for row in result.all()
        ]

    async def create_review_record(self, review_data: Dict[str, Any]) -> ReviewRecord:
        """
        创建复习记录
        
        Args:
            review_data: 复习数据
            
        Returns:
            创建的复习记录
        """
        review_record = ReviewRecord(**review_data)
        self.session.add(review_record)
        await self.session.flush()
        
        # 更新错题的复习统计
        error_question = await self.get_by_id(review_data["error_question_id"])
        if error_question:
            error_question.review_count += 1
            error_question.last_review_at = review_record.reviewed_at
            
            if review_record.review_result == "correct":
                error_question.correct_count += 1
            
            # 更新复习计划
            performance = review_record.performance_score
            error_question.update_review_schedule(performance)
            
            await self.session.flush()
        
        return review_record

    async def get_user_review_records(
        self, user_id: str, error_question_id: Optional[str] = None, limit: int = 50
    ) -> List[ReviewRecord]:
        """
        获取用户的复习记录
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID（可选）
            limit: 返回数量限制
            
        Returns:
            复习记录列表
        """
        conditions = [ReviewRecord.user_id == user_id]
        
        if error_question_id:
            conditions.append(ReviewRecord.error_question_id == error_question_id)
        
        stmt = (
            select(ReviewRecord)
            .where(and_(*conditions))
            .order_by(desc(ReviewRecord.reviewed_at))
            .limit(limit)
            .options(joinedload(ReviewRecord.error_question))
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue_reviews(self, user_id: str) -> List[ErrorQuestion]:
        """
        获取逾期复习的错题
        
        Args:
            user_id: 用户ID
            
        Returns:
            逾期错题列表
        """
        now = datetime.utcnow()
        
        stmt = (
            select(ErrorQuestion)
            .where(
                and_(
                    ErrorQuestion.user_id == user_id,
                    ErrorQuestion.mastery_status != MasteryStatus.MASTERED,
                    ErrorQuestion.next_review_at < now
                )
            )
            .order_by(ErrorQuestion.next_review_at)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def batch_update_mastery_status(
        self, error_question_ids: List[str], new_status: str
    ) -> int:
        """
        批量更新掌握状态
        
        Args:
            error_question_ids: 错题ID列表
            new_status: 新状态
            
        Returns:
            更新数量
        """
        stmt = text("""
            UPDATE error_questions 
            SET mastery_status = :new_status, updated_at = :now
            WHERE id = ANY(:ids)
        """)
        
        result = await self.session.execute(
            stmt,
            {
                "new_status": new_status,
                "now": datetime.utcnow().isoformat(),
                "ids": error_question_ids
            }
        )
        
        return result.rowcount or 0

    async def delete_user_error_questions(self, user_id: str, error_question_ids: List[str]) -> int:
        """
        删除用户的错题记录
        
        Args:
            user_id: 用户ID
            error_question_ids: 错题ID列表
            
        Returns:
            删除数量
        """
        stmt = text("""
            DELETE FROM error_questions 
            WHERE user_id = :user_id AND id = ANY(:ids)
        """)
        
        result = await self.session.execute(
            stmt,
            {"user_id": user_id, "ids": error_question_ids}
        )
        
        return result.rowcount or 0