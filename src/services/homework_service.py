"""
作业管理服务业务逻辑层
处理作业相关的核心业务逻辑，包括作业提交、OCR处理、AI批改等
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import tempfile
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from src.models.homework import (
    Homework, HomeworkSubmission, HomeworkImage, HomeworkReview,
    SubmissionStatus, ReviewStatus
)
from src.models.user import User
from src.schemas.homework import (
    HomeworkCreate, HomeworkUpdate, HomeworkResponse,
    HomeworkSubmissionCreate, HomeworkSubmissionUpdate, HomeworkSubmissionResponse,
    HomeworkReviewCreate, HomeworkReviewResponse,
    HomeworkQuery, SubmissionQuery, PaginationParams, PaginatedResponse,
    KnowledgePointAnalysis, ImprovementSuggestion, QuestionReview
)
from src.services.bailian_service import BailianService
from src.utils.ocr import OCRService, OCRType
from src.utils.file_upload import FileUploadService
from src.utils.cache import cache, cache_manager
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import AIServiceError, DatabaseError, ValidationError

logger = get_logger(__name__)


class HomeworkService:
    """作业管理服务"""

    def __init__(
        self,
        bailian_service: Optional[BailianService] = None,
        ocr_service: Optional[OCRService] = None,
        file_service: Optional[FileUploadService] = None
    ):
        """
        初始化作业服务

        Args:
            bailian_service: 百炼AI服务实例
            ocr_service: OCR服务实例
            file_service: 文件上传服务实例
        """
        from src.services.bailian_service import get_bailian_service
        from src.utils.ocr import get_ocr_service
        from src.utils.file_upload import get_file_upload_service

        self.bailian_service = bailian_service or get_bailian_service()
        self.ocr_service = ocr_service or get_ocr_service()
        self.file_service = file_service or get_file_upload_service()

    # ============================================================================
    # 作业模板管理
    # ============================================================================

    async def create_homework(
        self,
        session: AsyncSession,
        homework_data: HomeworkCreate,
        creator_id: Optional[uuid.UUID] = None,
        creator_name: Optional[str] = None
    ) -> Homework:
        """
        创建作业模板

        Args:
            session: 数据库会话
            homework_data: 作业创建数据
            creator_id: 创建者ID
            creator_name: 创建者姓名

        Returns:
            创建的作业对象
        """
        try:
            # 创建作业对象
            homework = Homework(
                title=homework_data.title,
                description=homework_data.description,
                subject=homework_data.subject,
                homework_type=homework_data.homework_type,
                difficulty_level=homework_data.difficulty_level,
                grade_level=homework_data.grade_level,
                chapter=homework_data.chapter,
                knowledge_points=homework_data.knowledge_points,
                estimated_duration=homework_data.estimated_duration,
                deadline=homework_data.deadline,
                creator_id=creator_id,
                creator_name=creator_name,
                is_active=True,
                is_template=True
            )

            session.add(homework)
            await session.commit()
            await session.refresh(homework)

            # 清理相关缓存
            await cache_manager.clear_namespace("homework")

            logger.info(f"作业模板创建成功: {homework.id} - {homework.title}")
            return homework

        except Exception as e:
            await session.rollback()
            logger.error(f"创建作业模板失败: {e}")
            raise DatabaseError(f"创建作业模板失败: {e}")

    async def get_homework(
        self,
        session: AsyncSession,
        homework_id: uuid.UUID
    ) -> Optional[Homework]:
        """
        获取作业模板

        Args:
            session: 数据库会话
            homework_id: 作业ID

        Returns:
            作业对象或None
        """
        try:
            stmt = select(Homework).where(Homework.id == homework_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取作业模板失败: {e}")
            raise DatabaseError(f"获取作业模板失败: {e}")

    @cache(ttl=300, namespace="homework_list")
    async def list_homeworks(
        self,
        session: AsyncSession,
        query_params: HomeworkQuery,
        pagination: PaginationParams
    ) -> PaginatedResponse:
        """
        查询作业列表

        Args:
            session: 数据库会话
            query_params: 查询参数
            pagination: 分页参数

        Returns:
            分页响应
        """
        try:
            # 构建查询条件
            conditions = []

            if query_params.subject:
                conditions.append(Homework.subject == query_params.subject)
            if query_params.homework_type:
                conditions.append(Homework.homework_type == query_params.homework_type)
            if query_params.difficulty_level:
                conditions.append(Homework.difficulty_level == query_params.difficulty_level)
            if query_params.grade_level:
                conditions.append(Homework.grade_level == query_params.grade_level)
            if query_params.creator_id:
                conditions.append(Homework.creator_id == query_params.creator_id)
            if query_params.is_active is not None:
                conditions.append(Homework.is_active == query_params.is_active)
            if query_params.keyword:
                conditions.append(
                    or_(
                        Homework.title.contains(query_params.keyword),
                        Homework.description.contains(query_params.keyword)
                    )
                )

            # 计算总数
            count_stmt = select(func.count(Homework.id)).where(and_(*conditions))
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # 查询数据
            offset = (pagination.page - 1) * pagination.size

            order_column = getattr(Homework, pagination.sort_by, Homework.created_at)
            order_clause = order_column.desc() if pagination.sort_order == "desc" else order_column.asc()

            stmt = (
                select(Homework)
                .where(and_(*conditions))
                .order_by(order_clause)
                .offset(offset)
                .limit(pagination.size)
            )

            result = await session.execute(stmt)
            homeworks = result.scalars().all()

            # 计算分页信息
            pages = (total + pagination.size - 1) // pagination.size
            has_next = pagination.page < pages
            has_prev = pagination.page > 1

            return PaginatedResponse(
                items=[HomeworkResponse.from_orm(hw) for hw in homeworks],
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pages,
                has_next=has_next,
                has_prev=has_prev
            )

        except Exception as e:
            logger.error(f"查询作业列表失败: {e}")
            raise DatabaseError(f"查询作业列表失败: {e}")

    # ============================================================================
    # 作业提交管理
    # ============================================================================

    async def create_submission(
        self,
        session: AsyncSession,
        submission_data: HomeworkSubmissionCreate,
        student_id: uuid.UUID,
        student_name: str
    ) -> HomeworkSubmission:
        """
        创建作业提交

        Args:
            session: 数据库会话
            submission_data: 提交数据
            student_id: 学生ID
            student_name: 学生姓名

        Returns:
            提交对象
        """
        try:
            # 检查作业是否存在
            homework = await self.get_homework(session, submission_data.homework_id)
            if not homework:
                raise ValidationError("作业不存在")

            if not homework.is_active:
                raise ValidationError("作业已停用")

            # 检查是否已经提交过
            existing_stmt = select(HomeworkSubmission).where(
                and_(
                    HomeworkSubmission.homework_id == submission_data.homework_id,
                    HomeworkSubmission.student_id == student_id
                )
            )
            existing_result = await session.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                raise ValidationError("该作业已经提交过了")

            # 创建提交对象
            submission = HomeworkSubmission(
                homework_id=submission_data.homework_id,
                student_id=student_id,
                student_name=student_name,
                submission_title=submission_data.submission_title,
                submission_note=submission_data.submission_note,
                completion_time=submission_data.completion_time,
                status=SubmissionStatus.UPLOADED,
                submitted_at=datetime.now()
            )

            session.add(submission)
            await session.commit()
            await session.refresh(submission)

            # 更新作业提交统计
            await self._update_homework_stats(session, homework.id)

            logger.info(f"作业提交创建成功: {submission.id}")
            return submission

        except Exception as e:
            await session.rollback()
            logger.error(f"创建作业提交失败: {e}")
            if isinstance(e, (ValidationError, AIServiceError)):
                raise
            raise DatabaseError(f"创建作业提交失败: {e}")

    async def upload_homework_images(
        self,
        session: AsyncSession,
        submission_id: uuid.UUID,
        image_files: List[UploadFile]
    ) -> List[HomeworkImage]:
        """
        上传作业图片

        Args:
            session: 数据库会话
            submission_id: 提交ID
            image_files: 图片文件列表

        Returns:
            上传的图片对象列表
        """
        try:
            # 检查提交是否存在
            submission = await self.get_submission(session, submission_id)
            if not submission:
                raise ValidationError("作业提交不存在")

            # 上传文件并创建图片记录
            uploaded_images = []

            for i, image_file in enumerate(image_files):
                # 上传文件
                file_info = await self.file_service.save_upload_file(
                    image_file,
                    subfolder="homework"
                )

                # 创建图片记录
                homework_image = HomeworkImage(
                    submission_id=submission_id,
                    original_filename=file_info.filename,
                    file_path=file_info.file_path,
                    file_url=file_info.file_url,
                    file_size=file_info.file_size,
                    mime_type=file_info.mime_type,
                    image_width=file_info.width,
                    image_height=file_info.height,
                    display_order=i,
                    is_primary=(i == 0),  # 第一张图片设为主图
                    is_processed=False
                )

                session.add(homework_image)
                uploaded_images.append(homework_image)

            await session.commit()

            # 异步处理OCR
            asyncio.create_task(self._process_images_ocr(submission_id, uploaded_images))

            logger.info(f"作业图片上传成功: {len(uploaded_images)}张")
            return uploaded_images

        except Exception as e:
            await session.rollback()
            logger.error(f"上传作业图片失败: {e}")
            if isinstance(e, (ValidationError, AIServiceError)):
                raise
            raise DatabaseError(f"上传作业图片失败: {e}")

    async def _process_images_ocr(
        self,
        submission_id: uuid.UUID,
        images: List[HomeworkImage]
    ):
        """
        异步处理图片OCR识别

        Args:
            submission_id: 提交ID
            images: 图片列表
        """
        from src.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                for image in images:
                    await self._process_single_image_ocr(session, image)

                # OCR完成后开始AI批改
                await self._trigger_ai_review(session, submission_id)

            except Exception as e:
                logger.error(f"OCR处理失败: {e}")

    async def _process_single_image_ocr(
        self,
        session: AsyncSession,
        image: HomeworkImage
    ):
        """
        处理单张图片的OCR识别

        Args:
            session: 数据库会话
            image: 图片对象
        """
        try:
            if not self.ocr_service.is_service_available():
                logger.warning("OCR服务不可用，跳过OCR处理")
                return

            # 确定图片路径
            image_path = image.file_path
            if not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return

            # 执行OCR识别
            ocr_result = await self.ocr_service.auto_recognize(
                image_path=image_path,
                ocr_type=OCRType.GENERAL,  # 可以根据作业类型选择
                enhance=True
            )

            # 更新图片记录
            stmt = (
                update(HomeworkImage)
                .where(HomeworkImage.id == image.id)
                .values(
                    ocr_text=ocr_result.text,
                    ocr_confidence=ocr_result.confidence,
                    ocr_data=ocr_result.to_dict(),
                    ocr_processed_at=datetime.now(),
                    is_processed=True
                )
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(f"图片OCR处理完成: {image.id}, 置信度: {ocr_result.confidence:.2f}")

        except Exception as e:
            logger.error(f"图片OCR处理失败: {e}")

            # 记录错误信息
            stmt = (
                update(HomeworkImage)
                .where(HomeworkImage.id == image.id)
                .values(
                    processing_error=str(e),
                    is_processed=True  # 标记为已处理，避免重复处理
                )
            )

            await session.execute(stmt)
            await session.commit()

    async def _trigger_ai_review(
        self,
        session: AsyncSession,
        submission_id: uuid.UUID
    ):
        """
        触发AI批改

        Args:
            session: 数据库会话
            submission_id: 提交ID
        """
        try:
            # 检查是否所有图片都已处理完成
            stmt = select(HomeworkImage).where(
                and_(
                    HomeworkImage.submission_id == submission_id,
                    HomeworkImage.is_processed == False
                )
            )
            result = await session.execute(stmt)
            unprocessed_images = result.scalars().all()

            if unprocessed_images:
                logger.info(f"还有{len(unprocessed_images)}张图片未处理完成，稍后重试")
                # 5分钟后重试
                await asyncio.sleep(300)
                await self._trigger_ai_review(session, submission_id)
                return

            # 更新提交状态为处理中
            stmt = (
                update(HomeworkSubmission)
                .where(HomeworkSubmission.id == submission_id)
                .values(status=SubmissionStatus.PROCESSING)
            )
            await session.execute(stmt)
            await session.commit()

            # 开始AI批改
            await self.start_ai_review(session, submission_id)

        except Exception as e:
            logger.error(f"触发AI批改失败: {e}")

    # ============================================================================
    # AI批改功能
    # ============================================================================

    async def start_ai_review(
        self,
        session: AsyncSession,
        submission_id: uuid.UUID,
        max_score: float = 100.0
    ) -> HomeworkReview:
        """
        开始AI批改

        Args:
            session: 数据库会话
            submission_id: 提交ID
            max_score: 满分

        Returns:
            批改结果对象
        """
        try:
            # 获取提交信息和相关数据
            submission = await self.get_submission_with_details(session, submission_id)
            if not submission:
                raise ValidationError("作业提交不存在")

            # 创建批改记录
            review = HomeworkReview(
                submission_id=submission_id,
                review_type="ai_auto",
                status=ReviewStatus.IN_PROGRESS,
                started_at=datetime.now(),
                max_score=max_score
            )

            session.add(review)
            await session.commit()
            await session.refresh(review)

            # 准备AI批改的数据
            review_data = await self._prepare_ai_review_data(session, submission)

            # 调用百炼AI进行批改
            ai_result = await self.bailian_service.review_homework(
                homework_data=review_data,
                max_score=max_score
            )

            # 处理AI批改结果
            await self._process_ai_review_result(session, review.id, ai_result)

            logger.info(f"AI批改完成: {review.id}")
            return review

        except Exception as e:
            await session.rollback()
            logger.error(f"AI批改失败: {e}")

            # 更新批改状态为失败
            if 'review' in locals():
                await self._mark_review_failed(session, review.id, str(e))

            raise AIServiceError(f"AI批改失败: {e}")

    async def _prepare_ai_review_data(
        self,
        session: AsyncSession,
        submission: HomeworkSubmission
    ) -> Dict[str, Any]:
        """
        准备AI批改所需的数据

        Args:
            session: 数据库会话
            submission: 提交对象

        Returns:
            批改数据字典
        """
        try:
            # 获取作业信息
            homework = submission.homework

            # 获取图片和OCR文本
            images_stmt = select(HomeworkImage).where(
                HomeworkImage.submission_id == submission.id
            ).order_by(HomeworkImage.display_order)
            images_result = await session.execute(images_stmt)
            images = images_result.scalars().all()

            # 合并OCR文本
            ocr_texts = []
            for image in images:
                if image.ocr_text and image.ocr_text.strip():
                    ocr_texts.append(image.ocr_text.strip())

            combined_text = "\n\n".join(ocr_texts) if ocr_texts else ""

            return {
                "homework_title": homework.title,
                "homework_description": homework.description,
                "subject": homework.subject,
                "grade_level": homework.grade_level,
                "knowledge_points": homework.knowledge_points or [],
                "difficulty_level": homework.difficulty_level,
                "student_work_text": combined_text,
                "submission_note": submission.submission_note,
                "completion_time": submission.completion_time,
                "image_count": len(images)
            }

        except Exception as e:
            logger.error(f"准备AI批改数据失败: {e}")
            raise

    async def _process_ai_review_result(
        self,
        session: AsyncSession,
        review_id: uuid.UUID,
        ai_result: Dict[str, Any]
    ):
        """
        处理AI批改结果

        Args:
            session: 数据库会话
            review_id: 批改ID
            ai_result: AI批改结果
        """
        try:
            # 解析AI返回的结果
            total_score = float(ai_result.get("total_score", 0))
            accuracy_rate = float(ai_result.get("accuracy_rate", 0))
            overall_comment = ai_result.get("overall_comment", "")
            strengths = ai_result.get("strengths", [])
            weaknesses = ai_result.get("weaknesses", [])
            suggestions = ai_result.get("suggestions", [])
            knowledge_point_analysis = ai_result.get("knowledge_point_analysis", [])
            question_reviews = ai_result.get("question_reviews", [])

            # 质量控制评分
            quality_score = self._calculate_quality_score(ai_result)
            needs_manual_review = quality_score < 0.7  # 质量分数低于0.7需要人工复核

            # 更新批改记录
            completed_at = datetime.now()
            processing_duration = int((completed_at - datetime.now()).total_seconds())

            stmt = (
                update(HomeworkReview)
                .where(HomeworkReview.id == review_id)
                .values(
                    status=ReviewStatus.COMPLETED,
                    completed_at=completed_at,
                    processing_duration=processing_duration,
                    total_score=total_score,
                    accuracy_rate=accuracy_rate,
                    overall_comment=overall_comment,
                    strengths=strengths,
                    weaknesses=weaknesses,
                    suggestions=suggestions,
                    knowledge_point_analysis=knowledge_point_analysis,
                    question_reviews=question_reviews,
                    ai_model_version=ai_result.get("model_version"),
                    ai_confidence_score=ai_result.get("confidence_score"),
                    ai_processing_tokens=ai_result.get("tokens_used"),
                    quality_score=quality_score,
                    needs_manual_review=needs_manual_review
                )
            )

            await session.execute(stmt)

            # 更新提交记录
            submission_stmt = (
                update(HomeworkSubmission)
                .where(HomeworkSubmission.id == review_id)
                .values(
                    status=SubmissionStatus.REVIEWED,
                    total_score=total_score,
                    accuracy_rate=accuracy_rate,
                    ai_review_data=ai_result,
                    weak_knowledge_points=knowledge_point_analysis,
                    improvement_suggestions=suggestions
                )
            )

            await session.execute(submission_stmt)
            await session.commit()

            logger.info(f"AI批改结果处理完成: 分数={total_score}, 质量分={quality_score:.2f}")

        except Exception as e:
            await session.rollback()
            logger.error(f"处理AI批改结果失败: {e}")
            await self._mark_review_failed(session, review_id, str(e))
            raise

    def _calculate_quality_score(self, ai_result: Dict[str, Any]) -> float:
        """
        计算批改质量分数

        Args:
            ai_result: AI批改结果

        Returns:
            质量分数(0-1)
        """
        try:
            score = 0.0

            # AI置信度权重：30%
            confidence = ai_result.get("confidence_score", 0)
            score += confidence * 0.3

            # 内容完整性权重：40%
            completeness = 0.0
            if ai_result.get("overall_comment"):
                completeness += 0.3
            if ai_result.get("strengths"):
                completeness += 0.2
            if ai_result.get("weaknesses"):
                completeness += 0.2
            if ai_result.get("suggestions"):
                completeness += 0.3

            score += completeness * 0.4

            # 数据一致性权重：30%
            consistency = 1.0
            total_score = ai_result.get("total_score", 0)
            accuracy_rate = ai_result.get("accuracy_rate", 0)

            # 分数和正确率应该相关
            if total_score > 0 and accuracy_rate > 0:
                score_rate = total_score / 100.0
                if abs(score_rate - accuracy_rate) > 0.3:  # 差异超过30%
                    consistency -= 0.5

            score += consistency * 0.3

            return min(max(score, 0.0), 1.0)  # 限制在0-1范围内

        except Exception as e:
            logger.error(f"计算质量分数失败: {e}")
            return 0.5  # 返回中等质量分数

    async def _mark_review_failed(
        self,
        session: AsyncSession,
        review_id: uuid.UUID,
        error_message: str
    ):
        """
        标记批改失败

        Args:
            session: 数据库会话
            review_id: 批改ID
            error_message: 错误消息
        """
        try:
            stmt = (
                update(HomeworkReview)
                .where(HomeworkReview.id == review_id)
                .values(
                    status=ReviewStatus.FAILED,
                    completed_at=datetime.now(),
                    error_message=error_message
                )
            )

            await session.execute(stmt)
            await session.commit()

        except Exception as e:
            logger.error(f"标记批改失败状态失败: {e}")

    # ============================================================================
    # 查询功能
    # ============================================================================

    async def get_submission(
        self,
        session: AsyncSession,
        submission_id: uuid.UUID
    ) -> Optional[HomeworkSubmission]:
        """
        获取作业提交

        Args:
            session: 数据库会话
            submission_id: 提交ID

        Returns:
            提交对象或None
        """
        try:
            stmt = select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取作业提交失败: {e}")
            raise DatabaseError(f"获取作业提交失败: {e}")

    async def get_submission_with_details(
        self,
        session: AsyncSession,
        submission_id: uuid.UUID
    ) -> Optional[HomeworkSubmission]:
        """
        获取带详情的作业提交

        Args:
            session: 数据库会话
            submission_id: 提交ID

        Returns:
            包含关联数据的提交对象或None
        """
        try:
            stmt = (
                select(HomeworkSubmission)
                .options(
                    selectinload(HomeworkSubmission.homework),
                    selectinload(HomeworkSubmission.images),
                    selectinload(HomeworkSubmission.reviews)
                )
                .where(HomeworkSubmission.id == submission_id)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取作业提交详情失败: {e}")
            raise DatabaseError(f"获取作业提交详情失败: {e}")

    async def _update_homework_stats(
        self,
        session: AsyncSession,
        homework_id: uuid.UUID
    ):
        """
        更新作业统计信息

        Args:
            session: 数据库会话
            homework_id: 作业ID
        """
        try:
            # 计算提交统计
            stats_stmt = (
                select(
                    func.count(HomeworkSubmission.id).label('total_submissions'),
                    func.avg(HomeworkSubmission.total_score).label('avg_score')
                )
                .where(HomeworkSubmission.homework_id == homework_id)
            )

            result = await session.execute(stats_stmt)
            stats = result.first()

            # 更新作业记录
            update_stmt = (
                update(Homework)
                .where(Homework.id == homework_id)
                .values(
                    total_submissions=stats.total_submissions or 0,
                    avg_score=stats.avg_score
                )
            )

            await session.execute(update_stmt)
            await session.commit()

        except Exception as e:
            logger.error(f"更新作业统计失败: {e}")
