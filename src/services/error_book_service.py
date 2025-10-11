"""
错题本业务逻辑服务
提供错题管理、分析和复习推荐的核心业务功能
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.error_book import ErrorQuestion, ReviewRecord, ErrorType, MasteryStatus, SourceType
from src.repositories.error_book_repository import ErrorBookRepository
from src.schemas.error_book import (
    ErrorQuestionCreate, ErrorQuestionUpdate, ErrorQuestionResponse,
    ReviewRecordCreate, ReviewRecordResponse, ErrorQuestionListQuery,
    ErrorQuestionListResponse, ErrorBookStats, ReviewRecommendations,
    ReviewRecommendation, WeakAreaRecommendation, DailyReviewPlan,
    ErrorAnalysisRequest, ErrorAnalysisResponse
)
from src.services.bailian_service import BailianService, ChatMessage, MessageRole, AIContext

logger = logging.getLogger(__name__)


class ErrorBookService:
    """错题本业务服务"""

    def __init__(self, session: AsyncSession, bailian_service: BailianService):
        self.session = session
        self.repository = ErrorBookRepository(session)
        self.bailian_service = bailian_service

    async def create_error_question(
        self, user_id: str, error_data: ErrorQuestionCreate
    ) -> ErrorQuestionResponse:
        """
        创建错题记录
        
        Args:
            user_id: 用户ID
            error_data: 错题数据
            
        Returns:
            创建的错题记录
        """
        try:
            # 如果是手动添加，进行AI分析
            if error_data.source_type == SourceType.MANUAL:
                ai_analysis = await self._analyze_error_with_ai(
                    error_data.question_content,
                    error_data.student_answer or "",
                    error_data.correct_answer or "",
                    error_data.subject
                )
                
                # 更新错误类型和知识点
                if ai_analysis:
                    error_data.error_type = ai_analysis.get("error_type", error_data.error_type)
                    error_data.knowledge_points = ai_analysis.get("knowledge_points", error_data.knowledge_points)

            # 创建错题记录
            error_question_data = error_data.model_dump()
            error_question_data["user_id"] = user_id
            error_question_data["mastery_status"] = MasteryStatus.LEARNING
            
            # 设置初始复习时间
            if not error_question_data.get("next_review_at"):
                error_question_data["next_review_at"] = datetime.utcnow() + timedelta(days=1)

            error_question = await self.repository.create(error_question_data)
            await self.session.commit()

            logger.info(f"创建错题记录成功: {error_question.id} for user {user_id}")
            return ErrorQuestionResponse.model_validate(error_question)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"创建错题记录失败: {e}")
            raise

    async def get_user_error_questions(
        self, user_id: str, query: ErrorQuestionListQuery
    ) -> ErrorQuestionListResponse:
        """
        获取用户错题列表
        
        Args:
            user_id: 用户ID
            query: 查询参数
            
        Returns:
            错题列表响应
        """
        try:
            error_questions, total = await self.repository.get_user_error_questions(
                user_id=user_id,
                subject=query.subject,
                status=query.status,
                category=query.category,
                difficulty=query.difficulty,
                sort=query.sort,
                order=query.order,
                page=query.page,
                limit=query.limit
            )

            items = [ErrorQuestionResponse.model_validate(eq) for eq in error_questions]
            pages = (total + query.limit - 1) // query.limit if total > 0 else 0

            return ErrorQuestionListResponse(
                items=items,
                total=total,
                page=query.page,
                limit=query.limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"获取错题列表失败: {e}")
            raise

    async def get_error_question_detail(
        self, user_id: str, error_question_id: str
    ) -> Optional[ErrorQuestionResponse]:
        """
        获取错题详情
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            
        Returns:
            错题详情或None
        """
        try:
            error_question = await self.repository.get_by_id(error_question_id)
            
            if not error_question or error_question.user_id != user_id:
                return None

            return ErrorQuestionResponse.model_validate(error_question)

        except Exception as e:
            logger.error(f"获取错题详情失败: {e}")
            raise

    async def update_error_question(
        self, user_id: str, error_question_id: str, update_data: ErrorQuestionUpdate
    ) -> Optional[ErrorQuestionResponse]:
        """
        更新错题记录
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            update_data: 更新数据
            
        Returns:
            更新后的错题记录或None
        """
        try:
            error_question = await self.repository.get_by_id(error_question_id)
            
            if not error_question or error_question.user_id != user_id:
                return None

            # 更新字段
            update_dict = update_data.model_dump(exclude_unset=True)
            error_question = await self.repository.update(error_question_id, update_dict)
            await self.session.commit()

            logger.info(f"更新错题记录成功: {error_question_id}")
            return ErrorQuestionResponse.model_validate(error_question)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"更新错题记录失败: {e}")
            raise

    async def delete_error_question(self, user_id: str, error_question_id: str) -> bool:
        """
        删除错题记录
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            
        Returns:
            删除是否成功
        """
        try:
            count = await self.repository.delete_user_error_questions(user_id, [error_question_id])
            await self.session.commit()

            success = count > 0
            if success:
                logger.info(f"删除错题记录成功: {error_question_id}")
            else:
                logger.warning(f"错题记录不存在或无权限: {error_question_id}")
            
            return success

        except Exception as e:
            await self.session.rollback()
            logger.error(f"删除错题记录失败: {e}")
            raise

    async def create_review_record(
        self, user_id: str, review_data: ReviewRecordCreate
    ) -> ReviewRecordResponse:
        """
        创建复习记录
        
        Args:
            user_id: 用户ID
            review_data: 复习数据
            
        Returns:
            创建的复习记录
        """
        try:
            # 验证错题是否属于用户
            error_question = await self.repository.get_by_id(review_data.error_question_id)
            if not error_question or error_question.user_id != user_id:
                raise ValueError("错题不存在或无权限访问")

            # 创建复习记录
            record_data = review_data.model_dump()
            record_data["user_id"] = user_id
            record_data["reviewed_at"] = datetime.utcnow()

            review_record = await self.repository.create_review_record(record_data)
            await self.session.commit()

            logger.info(f"创建复习记录成功: {review_record.id} for error {review_data.error_question_id}")
            return ReviewRecordResponse.model_validate(review_record)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"创建复习记录失败: {e}")
            raise

    async def get_error_book_stats(self, user_id: str) -> ErrorBookStats:
        """
        获取错题本统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            stats = await self.repository.get_user_error_stats(user_id)
            return ErrorBookStats(**stats)

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

    async def get_review_recommendations(
        self, user_id: str, limit: int = 10
    ) -> ReviewRecommendations:
        """
        获取复习推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            
        Returns:
            复习推荐
        """
        try:
            # 获取推荐复习的错题
            recommended_errors = await self.repository.get_review_recommendations(user_id, limit)
            
            # 构建紧急复习列表
            urgent_reviews = []
            for error in recommended_errors:
                urgent_reviews.append(ReviewRecommendation(
                    error_question_id=str(error.id),
                    question_preview=error.question_content[:100] + "..." if len(error.question_content) > 100 else error.question_content,
                    subject=error.subject,
                    overdue_days=error.overdue_days,
                    importance_score=self._calculate_importance_score(error),
                    difficulty_level=error.difficulty_level
                ))

            # 获取薄弱区域
            weak_areas = await self.repository.get_weak_knowledge_points(user_id, 5)
            weak_area_recommendations = [
                WeakAreaRecommendation(**area) for area in weak_areas
            ]

            # 生成每日复习计划
            daily_plan = self._generate_daily_plan(recommended_errors)

            return ReviewRecommendations(
                urgent_reviews=urgent_reviews,
                daily_plan=daily_plan,
                weak_areas=weak_area_recommendations
            )

        except Exception as e:
            logger.error(f"获取复习推荐失败: {e}")
            raise

    async def batch_update_mastery_status(
        self, user_id: str, error_question_ids: List[str], new_status: str
    ) -> int:
        """
        批量更新掌握状态
        
        Args:
            user_id: 用户ID
            error_question_ids: 错题ID列表
            new_status: 新状态
            
        Returns:
            更新数量
        """
        try:
            # 验证状态值
            if new_status not in [s.value for s in MasteryStatus]:
                raise ValueError(f"无效的掌握状态: {new_status}")

            count = await self.repository.batch_update_mastery_status(error_question_ids, new_status)
            await self.session.commit()

            logger.info(f"批量更新掌握状态成功: {count}条记录")
            return count

        except Exception as e:
            await self.session.rollback()
            logger.error(f"批量更新掌握状态失败: {e}")
            raise

    async def collect_error_from_homework(
        self, user_id: str, homework_submission_id: str, questions_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        从作业批改结果收集错题
        
        Args:
            user_id: 用户ID
            homework_submission_id: 作业提交ID
            questions_data: 题目数据列表
            
        Returns:
            创建的错题ID列表
        """
        try:
            created_ids = []
            
            for i, question in enumerate(questions_data):
                # 只收集得分低于70分的题目
                if question.get("score", 100) < 70:
                    error_data = {
                        "user_id": user_id,
                        "subject": question.get("subject", "通用"),
                        "question_content": question.get("question", f"第{i+1}题"),
                        "student_answer": question.get("student_answer", ""),
                        "correct_answer": question.get("correct_answer", ""),
                        "error_type": await self._determine_error_type(question),
                        "knowledge_points": question.get("knowledge_points", []),
                        "difficulty_level": self._estimate_difficulty(question),
                        "source_type": SourceType.HOMEWORK,
                        "source_id": homework_submission_id,
                        "next_review_at": datetime.utcnow() + timedelta(days=1)
                    }
                    
                    error_question = await self.repository.create(error_data)
                    created_ids.append(str(error_question.id))

            await self.session.commit()
            logger.info(f"从作业收集错题{len(created_ids)}道")
            return created_ids

        except Exception as e:
            await self.session.rollback()
            logger.error(f"从作业收集错题失败: {e}")
            raise

    async def _analyze_error_with_ai(
        self, question: str, student_answer: str, correct_answer: str, subject: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI分析错题类型和原因
        
        Args:
            question: 题目内容
            student_answer: 学生答案
            correct_answer: 正确答案
            subject: 学科
            
        Returns:
            分析结果字典
        """
        try:
            prompt = f"""
请分析以下错题，判断错误类型并提取相关知识点：

题目：{question}
学生答案：{student_answer}
正确答案：{correct_answer}
学科：{subject or '通用'}

请从以下四个维度分析错误类型：
1. 理解错误：对基本概念或原理理解不清
2. 方法错误：解题方法或步骤错误
3. 计算错误：基本运算或单位换算错误
4. 表达错误：答案格式或语言表达不规范

请以JSON格式返回分析结果：
{{
    "error_type": "错误类型（从上述四个中选择）",
    "error_subcategory": "具体错误子分类",
    "analysis": "详细分析",
    "knowledge_points": ["相关知识点1", "相关知识点2"],
    "suggestions": ["改进建议1", "改进建议2"]
}}
"""

            messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
            context = AIContext(subject=subject)
            
            response = await self.bailian_service.chat_completion(messages, context)
            
            if response.success:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    logger.warning("AI返回的错题分析结果不是有效JSON")
                    return None
            else:
                logger.warning(f"AI错题分析失败: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"AI错题分析异常: {e}")
            return None

    def _calculate_importance_score(self, error_question: ErrorQuestion) -> float:
        """
        计算错题重要性得分
        
        Args:
            error_question: 错题对象
            
        Returns:
            重要性得分 (0.0-1.0)
        """
        score = 0.0
        
        # 逾期时间权重 (40%)
        if error_question.is_overdue:
            overdue_factor = min(error_question.overdue_days / 7.0, 1.0)
            score += overdue_factor * 0.4
        
        # 难度权重 (30%)
        difficulty_factor = error_question.difficulty_level / 5.0
        score += difficulty_factor * 0.3
        
        # 复习次数权重 (20%) - 次数少的更重要
        review_factor = max(0, 1.0 - error_question.review_count / 10.0)
        score += review_factor * 0.2
        
        # 知识点覆盖权重 (10%)
        knowledge_factor = min(len(error_question.knowledge_points) / 5.0, 1.0)
        score += knowledge_factor * 0.1
        
        return min(score, 1.0)

    def _generate_daily_plan(self, recommended_errors: List[ErrorQuestion]) -> DailyReviewPlan:
        """
        生成每日复习计划
        
        Args:
            recommended_errors: 推荐复习的错题列表
            
        Returns:
            每日复习计划
        """
        target_count = min(len(recommended_errors), 10)  # 每日最多10题
        estimated_time = target_count * 3  # 每题预估3分钟
        
        subjects = list(set(error.subject for error in recommended_errors))
        priority_items = [str(error.id) for error in recommended_errors[:target_count]]
        
        return DailyReviewPlan(
            target_count=target_count,
            estimated_time=estimated_time,
            subjects=subjects,
            priority_items=priority_items
        )

    async def _determine_error_type(self, question_data: Dict[str, Any]) -> str:
        """
        根据题目数据确定错误类型
        
        Args:
            question_data: 题目数据
            
        Returns:
            错误类型
        """
        score = question_data.get("score", 0)
        
        # 简单的错误类型判断逻辑
        if score < 30:
            return ErrorType.CONCEPT_ERROR
        elif score < 50:
            return ErrorType.METHOD_ERROR
        elif score < 70:
            return ErrorType.CALCULATION_ERROR
        else:
            return ErrorType.EXPRESSION_ERROR

    def _estimate_difficulty(self, question_data: Dict[str, Any]) -> int:
        """
        估算题目难度
        
        Args:
            question_data: 题目数据
            
        Returns:
            难度等级 (1-5)
        """
        score = question_data.get("score", 100)
        
        # 根据得分反推难度
        if score >= 80:
            return 2  # 简单
        elif score >= 60:
            return 3  # 中等
        elif score >= 40:
            return 4  # 困难
        else:
            return 5  # 非常困难