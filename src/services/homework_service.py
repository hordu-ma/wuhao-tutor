"""
作业管理服务业务逻辑层
处理作业相关的核心业务逻辑，包括作业提交、OCR处理、AI批改等
"""

import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.exceptions import AIServiceError, DatabaseError, ValidationError
from src.core.logging import get_logger
from src.models.homework import (
    Homework,
    HomeworkImage,
    HomeworkReview,
    HomeworkSubmission,
    ReviewStatus,
    SubmissionStatus,
)
from src.models.user import User
from src.schemas.common import PaginatedResponse, PaginationInfo
from src.schemas.homework import (
    HomeworkCreate,
    HomeworkQuery,
    HomeworkResponse,
    HomeworkReviewCreate,
    HomeworkReviewResponse,
    HomeworkSubmissionCreate,
    HomeworkSubmissionResponse,
    HomeworkSubmissionUpdate,
    HomeworkUpdate,
    ImprovementSuggestion,
    KnowledgePointAnalysis,
    PaginationParams,
    QuestionReview,
    SubmissionQuery,
)
from src.services.bailian_service import BailianService, ChatMessage, MessageRole
from src.utils.cache import cache, cache_manager
from src.utils.file_upload import FileUploadService
from src.utils.ocr import AliCloudOCRService, OCRType

logger = get_logger(__name__)


class HomeworkService:
    """作业管理服务"""

    def __init__(
        self,
        bailian_service: Optional[BailianService] = None,
        ocr_service: Optional[AliCloudOCRService] = None,
        file_service: Optional[FileUploadService] = None,
    ):
        """
        初始化作业服务

        Args:
            bailian_service: 百炼AI服务实例
            ocr_service: OCR服务实例
            file_service: 文件上传服务实例
        """
        from src.services.bailian_service import get_bailian_service
        from src.utils.file_upload import get_file_upload_service
        from src.utils.ocr import get_ocr_service

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
        creator_name: Optional[str] = None,
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
                is_template=True,
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
        self, session: AsyncSession, homework_id: uuid.UUID
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
        pagination: PaginationParams,
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
                conditions.append(
                    Homework.difficulty_level == query_params.difficulty_level
                )
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
                        Homework.description.contains(query_params.keyword),
                    )
                )

            # 计算总数
            count_stmt = select(func.count(Homework.id)).where(and_(*conditions))
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # 查询数据
            offset = (pagination.page - 1) * pagination.size

            # 安全获取排序列
            sort_column = getattr(
                Homework, pagination.sort_by or "created_at", Homework.created_at
            )
            order_clause = (
                sort_column.desc()
                if pagination.sort_order == "desc"
                else sort_column.asc()
            )

            stmt = (
                select(Homework)
                .where(and_(*conditions))
                .order_by(order_clause)
                .offset(offset)
                .limit(pagination.size)
            )

            result = await session.execute(stmt)
            homeworks = result.scalars().all()

            # 创建分页信息
            pagination_info = PaginationInfo.create(
                total=total or 0, page=pagination.page, size=pagination.size
            )

            return PaginatedResponse(
                data=[HomeworkResponse.from_orm(hw) for hw in homeworks],
                pagination=pagination_info,
                success=True,
                message="查询作业列表成功",
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
        student_name: str,
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

            if not getattr(homework, "is_active", True):
                raise ValidationError("作业已停用")

            # 检查是否已经提交过
            existing_stmt = select(HomeworkSubmission).where(
                and_(
                    HomeworkSubmission.homework_id == submission_data.homework_id,
                    HomeworkSubmission.student_id == student_id,
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
                submitted_at=datetime.now(),
            )

            session.add(submission)
            await session.commit()
            await session.refresh(submission)

            # 更新作业提交统计
            await self._update_homework_stats(session, getattr(homework, "id"))

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
        image_files: List[UploadFile],
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
                    image_file, subfolder="homework"
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
                    is_processed=False,
                )

                session.add(homework_image)
                uploaded_images.append(homework_image)

            await session.commit()

            # 异步处理OCR
            asyncio.create_task(
                self._process_images_ocr(submission_id, uploaded_images)
            )

            logger.info(f"作业图片上传成功: {len(uploaded_images)}张")
            return uploaded_images

        except Exception as e:
            await session.rollback()
            logger.error(f"上传作业图片失败: {e}")
            if isinstance(e, (ValidationError, AIServiceError)):
                raise
            raise DatabaseError(f"上传作业图片失败: {e}")

    async def _process_images_ocr(
        self, submission_id: uuid.UUID, images: List[HomeworkImage]
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
        self, session: AsyncSession, image: HomeworkImage, retry_count: int = 0
    ):
        """
        处理单张图片的OCR识别（增强版，支持重试和质量评估）

        Args:
            session: 数据库会话
            image: 图片对象
            retry_count: 当前重试次数
        """
        max_retries = 3
        min_confidence = 0.6  # 最低置信度阈值

        try:
            if not self.ocr_service.is_service_available():
                logger.warning("OCR服务不可用，跳过OCR处理")
                await self._mark_ocr_failed(session, image, "OCR服务不可用")
                return

            # 确定图片路径
            file_path = str(image.file_path)
            if not os.path.exists(file_path):
                logger.warning(f"图片文件不存在: {file_path}")
                await self._mark_ocr_failed(session, image, "图片文件不存在")
                return

            # 新增: 图片质量预评估
            quality_check = await self._assess_image_quality(file_path)
            if not quality_check["is_valid"]:
                logger.warning(
                    f"图片质量不合格: {quality_check['reason']}, 路径: {file_path}"
                )
                await self._mark_ocr_failed(
                    session, image, f"图片质量问题: {quality_check['reason']}"
                )
                return

            # 执行OCR识别
            logger.info(
                f"开始OCR识别 (尝试 {retry_count + 1}/{max_retries + 1}): {image.id}"
            )

            ocr_result = await self.ocr_service.auto_recognize(
                image_path=file_path,
                ocr_type=OCRType.GENERAL,  # 可以根据作业类型选择
                enhance=True,
            )

            # 新增: 检查OCR结果质量
            if ocr_result.confidence < min_confidence:
                if retry_count < max_retries:
                    # 低置信度，尝试使用不同的OCR类型重试
                    logger.warning(
                        f"OCR置信度过低 ({ocr_result.confidence:.2f}), "
                        f"尝试手写体识别重试..."
                    )
                    await asyncio.sleep(1 * (retry_count + 1))  # 指数退避

                    # 尝试手写体识别
                    ocr_result_handwritten = await self.ocr_service.auto_recognize(
                        image_path=file_path,
                        ocr_type=OCRType.HANDWRITTEN,
                        enhance=True,
                    )

                    # 选择置信度更高的结果
                    if ocr_result_handwritten.confidence > ocr_result.confidence:
                        ocr_result = ocr_result_handwritten
                        logger.info(f"手写体识别效果更好，使用手写体结果")

            # 检查是否需要重试
            if ocr_result.confidence < min_confidence and retry_count < max_retries:
                logger.warning(
                    f"OCR置信度仍然过低 ({ocr_result.confidence:.2f}), "
                    f"将在 {2 ** retry_count} 秒后重试..."
                )
                await asyncio.sleep(2**retry_count)  # 指数退避: 1s, 2s, 4s
                return await self._process_single_image_ocr(
                    session, image, retry_count + 1
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
                    is_processed=True,
                    retry_count=retry_count,
                    quality_score=quality_check.get("score", 0),
                )
            )

            await session.execute(stmt)
            await session.commit()

            logger.info(
                f"图片OCR处理完成: {image.id}, "
                f"置信度: {ocr_result.confidence:.2f}, "
                f"重试次数: {retry_count}"
            )

        except Exception as e:
            logger.error(f"图片OCR处理失败: {e}, 重试次数: {retry_count}")

            # 是否应该重试
            if retry_count < max_retries:
                logger.info(f"将在 {2 ** retry_count} 秒后重试...")
                await asyncio.sleep(2**retry_count)
                return await self._process_single_image_ocr(
                    session, image, retry_count + 1
                )

            # 达到最大重试次数，记录错误
            await self._mark_ocr_failed(session, image, str(e), retry_count)

    async def _assess_image_quality(self, file_path: str) -> Dict[str, Any]:
        """
        评估图片质量

        Args:
            file_path: 图片文件路径

        Returns:
            质量评估结果，包含 is_valid, reason, score
        """
        try:
            import cv2
            import numpy as np

            # 读取图片
            img = cv2.imread(file_path)
            if img is None:
                return {"is_valid": False, "reason": "无法读取图片", "score": 0}

            # 检查图片尺寸
            height, width = img.shape[:2]
            if width < 100 or height < 100:
                return {
                    "is_valid": False,
                    "reason": f"图片尺寸过小 ({width}x{height})",
                    "score": 0,
                }

            # 检查图片是否过大（可能导致OCR失败）
            if width > 4096 or height > 4096:
                return {
                    "is_valid": False,
                    "reason": f"图片尺寸过大 ({width}x{height})",
                    "score": 0,
                }

            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 计算清晰度（Laplacian方差）
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # 清晰度阈值
            blur_threshold = 100
            if laplacian_var < blur_threshold:
                return {
                    "is_valid": False,
                    "reason": f"图片模糊 (清晰度: {laplacian_var:.2f})",
                    "score": min(laplacian_var / blur_threshold * 100, 100),
                }

            # 计算亮度
            brightness = np.mean(gray)

            # 亮度检查（太暗或太亮）
            if brightness < 50:
                return {
                    "is_valid": False,
                    "reason": f"图片过暗 (亮度: {brightness:.1f})",
                    "score": 50,
                }
            elif brightness > 205:
                return {
                    "is_valid": False,
                    "reason": f"图片过亮 (亮度: {brightness:.1f})",
                    "score": 50,
                }

            # 计算对比度
            contrast = gray.std()
            if contrast < 20:
                return {
                    "is_valid": False,
                    "reason": f"对比度过低 ({contrast:.1f})",
                    "score": 60,
                }

            # 质量分数计算（0-100）
            sharpness_score = min(laplacian_var / 500 * 100, 100)
            brightness_score = 100 - abs(brightness - 127.5) / 127.5 * 100
            contrast_score = min(contrast / 80 * 100, 100)

            overall_score = (
                sharpness_score * 0.5 + brightness_score * 0.3 + contrast_score * 0.2
            )

            return {
                "is_valid": True,
                "reason": "图片质量良好",
                "score": round(overall_score, 2),
                "details": {
                    "sharpness": round(laplacian_var, 2),
                    "brightness": round(brightness, 2),
                    "contrast": round(contrast, 2),
                    "size": f"{width}x{height}",
                },
            }

        except Exception as e:
            logger.error(f"图片质量评估失败: {e}")
            # 评估失败时，默认允许继续处理
            return {"is_valid": True, "reason": "质量评估失败，允许继续", "score": 50}

    async def _mark_ocr_failed(
        self,
        session: AsyncSession,
        image: HomeworkImage,
        error_message: str,
        retry_count: int = 0,
    ):
        """
        标记OCR处理失败

        Args:
            session: 数据库会话
            image: 图片对象
            error_message: 错误信息
            retry_count: 重试次数
        """
        stmt = (
            update(HomeworkImage)
            .where(HomeworkImage.id == image.id)
            .values(
                processing_error=error_message,
                is_processed=True,  # 标记为已处理，避免无限重试
                retry_count=retry_count,
                ocr_processed_at=datetime.now(),
            )
        )

        await session.execute(stmt)
        await session.commit()

        logger.error(
            f"OCR处理最终失败: {image.id}, "
            f"错误: {error_message}, "
            f"重试次数: {retry_count}"
        )

    async def _trigger_ai_review(self, session: AsyncSession, submission_id: uuid.UUID):
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
                    HomeworkImage.is_processed == False,
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
        self, session: AsyncSession, submission_id: uuid.UUID, max_score: float = 100.0
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
                max_score=max_score,
            )

            session.add(review)
            await session.commit()
            await session.refresh(review)

            # 准备AI批改的数据
            review_data = await self._prepare_ai_review_data(session, submission)

            # 调用百炼AI进行批改
            from dataclasses import asdict
            from typing import Any, Dict, List, Union

            # 构建专业的K12批改System Prompt
            system_prompt = """你是一位经验丰富的K12教育专家,负责批改学生作业。

# 批改标准
1. 答案正确性: 准确判断答案是否正确
2. 解题过程: 评估解题步骤的完整性和逻辑性
3. 知识点掌握: 分析学生对相关知识点的理解程度
4. 常见错误: 识别典型错误并给出纠正建议

# 输出格式
请以JSON格式输出批改结果(不要包含markdown代码块标记):
{
  "total_score": 85,
  "accuracy_rate": 0.85,
  "overall_comment": "整体完成较好,但部分知识点需加强",
  "strengths": ["计算准确", "步骤完整"],
  "weaknesses": ["概念理解有偏差", "书写不够规范"],
  "suggestions": ["多做类似题目巩固", "注意答题格式"],
  "knowledge_point_analysis": [
    {
      "name": "一元二次方程",
      "mastery_level": "good",
      "score": 8,
      "max_score": 10
    }
  ],
  "question_reviews": [
    {
      "question_number": 1,
      "score": 10,
      "max_score": 10,
      "is_correct": true,
      "comment": "解答正确,步骤清晰"
    }
  ],
  "confidence_score": 0.9,
  "model_version": "bailian-v1"
}

# 字段说明
- total_score: 总分(0-满分)
- accuracy_rate: 正确率(0-1小数)
- mastery_level: 掌握程度,可选值: "excellent"(优秀) | "good"(良好) | "fair"(一般) | "poor"(较差)
- confidence_score: AI置信度(0-1)

# 批改原则
- 鼓励为主,指出问题同时给予肯定
- 建议具体可操作,避免空泛评价
- 关注学习过程,不仅关注结果
- 语言简洁友好,适合学生理解

请严格按照JSON格式输出,不要添加任何额外说明文字。"""

            messages: List[Union[Dict[str, str], ChatMessage]] = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(
                    role=MessageRole.USER,
                    content=f"请批改以下作业，满分为{max_score}分：\n{json.dumps(review_data, ensure_ascii=False)}",
                ),
            ]
            ai_result = await self.bailian_service.chat_completion(messages=messages)

            # 处理AI批改结果
            review_id = getattr(review, "id")
            # 将AI响应转换为字典格式
            ai_result_dict = asdict(ai_result)

            await self._process_ai_review_result(session, review_id, ai_result_dict)

            logger.info(f"AI批改完成: {review.id}")
            return review

        except Exception as e:
            await session.rollback()
            logger.error(f"AI批改失败: {e}")

            # 更新批改状态为失败
            try:
                # 检查review是否已定义并且不为None
                review_var = locals().get("review")
                if review_var is not None:
                    review_id = getattr(review_var, "id")
                    await self._mark_review_failed(session, review_id, str(e))
            except Exception as mark_error:
                logger.error(f"标记批改失败时发生错误: {mark_error}")

            raise AIServiceError(f"AI批改失败: {e}")

    async def _prepare_ai_review_data(
        self, session: AsyncSession, submission: HomeworkSubmission
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
            images_stmt = (
                select(HomeworkImage)
                .where(HomeworkImage.submission_id == submission.id)
                .order_by(HomeworkImage.display_order)
            )
            images_result = await session.execute(images_stmt)
            images = images_result.scalars().all()

            # 合并OCR文本
            ocr_texts = []
            for image in images:
                ocr_text = getattr(image, "ocr_text", None)
                if ocr_text and str(ocr_text).strip():
                    ocr_texts.append(str(ocr_text).strip())

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
                "image_count": len(images),
            }

        except Exception as e:
            logger.error(f"准备AI批改数据失败: {e}")
            raise

    async def _process_ai_review_result(
        self, session: AsyncSession, review_id: uuid.UUID, ai_result: Dict[str, Any]
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
                    needs_manual_review=needs_manual_review,
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
                    improvement_suggestions=suggestions,
                )
            )

            await session.execute(submission_stmt)
            await session.commit()

            logger.info(
                f"AI批改结果处理完成: 分数={total_score}, 质量分={quality_score:.2f}"
            )

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
        self, session: AsyncSession, review_id: uuid.UUID, error_message: str
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
                    error_message=error_message,
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
        self, session: AsyncSession, submission_id: uuid.UUID
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
            stmt = select(HomeworkSubmission).where(
                HomeworkSubmission.id == submission_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取作业提交失败: {e}")
            raise DatabaseError(f"获取作业提交失败: {e}")

    async def get_submission_with_details(
        self, session: AsyncSession, submission_id: uuid.UUID
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
                    selectinload(HomeworkSubmission.reviews),
                )
                .where(HomeworkSubmission.id == submission_id)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取作业提交详情失败: {e}")
            raise DatabaseError(f"获取作业提交详情失败: {e}")

    async def _update_homework_stats(
        self, session: AsyncSession, homework_id: uuid.UUID
    ):
        """
        更新作业统计信息

        Args:
            session: 数据库会话
            homework_id: 作业ID
        """
        try:
            # 计算提交统计
            stats_stmt = select(
                func.count(HomeworkSubmission.id).label("total_submissions"),
                func.avg(HomeworkSubmission.total_score).label("avg_score"),
            ).where(HomeworkSubmission.homework_id == homework_id)

            result = await session.execute(stats_stmt)
            stats = result.first()

            # 更新作业记录
            if stats:
                update_stmt = (
                    update(Homework)
                    .where(Homework.id == homework_id)
                    .values(
                        total_submissions=stats.total_submissions or 0,
                        avg_score=stats.avg_score,
                    )
                )
                await session.execute(update_stmt)

            await session.commit()

        except Exception as e:
            logger.error(f"更新作业统计失败: {e}")

    # ============================================================================
    # API所需的附加方法
    # ============================================================================

    async def update_homework(
        self, session: AsyncSession, homework_id: str, update_data: Dict[str, Any]
    ) -> Homework:
        """
        更新作业模板

        Args:
            session: 数据库会话
            homework_id: 作业ID
            update_data: 更新数据

        Returns:
            更新后的作业对象
        """
        try:
            # 获取作业对象
            homework = await session.get(Homework, homework_id)
            if not homework:
                raise ValidationError("作业不存在")

            # 更新字段
            for field, value in update_data.items():
                if hasattr(homework, field):
                    setattr(homework, field, value)

            # updated_at will be automatically updated by SQLAlchemy
            await session.commit()
            await session.refresh(homework)

            logger.info(f"作业更新成功: {homework_id}")
            return homework

        except Exception as e:
            await session.rollback()
            logger.error(f"更新作业失败: {e}")
            raise DatabaseError(f"更新作业失败: {e}")

    async def list_submissions(
        self,
        session: AsyncSession,
        student_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse:
        """
        获取学生的作业提交列表

        Args:
            session: 数据库会话
            student_id: 学生ID
            filters: 过滤条件
            page: 页码
            size: 每页大小

        Returns:
            分页的提交列表
        """
        try:
            # 构建查询
            query = (
                select(HomeworkSubmission)
                .where(HomeworkSubmission.student_id == student_id)
                .options(selectinload(HomeworkSubmission.homework))
            )

            # 应用过滤条件
            if filters:
                if filters.get("status"):
                    query = query.where(HomeworkSubmission.status == filters["status"])
                if filters.get("subject"):
                    query = query.join(Homework).where(
                        Homework.subject == filters["subject"]
                    )
                if filters.get("homework_type"):
                    query = query.join(Homework).where(
                        Homework.homework_type == filters["homework_type"]
                    )

            # 计算总数
            count_query = select(func.count(HomeworkSubmission.id)).where(
                HomeworkSubmission.student_id == student_id
            )
            if filters:
                if filters.get("status"):
                    count_query = count_query.where(
                        HomeworkSubmission.status == filters["status"]
                    )
                if filters.get("subject"):
                    count_query = count_query.join(Homework).where(
                        Homework.subject == filters["subject"]
                    )
                if filters.get("homework_type"):
                    count_query = count_query.join(Homework).where(
                        Homework.homework_type == filters["homework_type"]
                    )

            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # 分页
            offset = (page - 1) * size
            query = (
                query.order_by(HomeworkSubmission.created_at.desc())
                .offset(offset)
                .limit(size)
            )

            result = await session.execute(query)
            submissions = result.scalars().all()

            # 转换为响应格式
            items = [HomeworkSubmissionResponse.from_orm(sub) for sub in submissions]

            # 创建分页信息
            pagination_info = PaginationInfo.create(
                total=total or 0, page=page, size=size
            )

            return PaginatedResponse(
                data=items,
                pagination=pagination_info,
                success=True,
                message="获取提交列表成功",
            )

        except Exception as e:
            logger.error(f"获取提交列表失败: {e}")
            raise DatabaseError(f"获取提交列表失败: {e}")

    async def get_homework_statistics(
        self,
        session: AsyncSession,
        student_id: str,
        subject: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        获取作业统计信息

        Args:
            session: 数据库会话
            student_id: 学生ID
            subject: 学科过滤
            days: 统计天数

        Returns:
            统计信息
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 基础统计查询
            query = select(
                func.count(HomeworkSubmission.id).label("total_submissions"),
                func.count(
                    func.case((HomeworkSubmission.status == "reviewed", 1))
                ).label("completed_submissions"),
                func.avg(HomeworkSubmission.total_score).label("avg_score"),
                func.avg(HomeworkSubmission.accuracy_rate).label("avg_accuracy"),
            ).where(
                and_(
                    HomeworkSubmission.student_id == student_id,
                    HomeworkSubmission.created_at >= cutoff_date,
                )
            )

            if subject:
                query = query.join(Homework).where(Homework.subject == subject)

            result = await session.execute(query)
            stats = result.first()

            # 学科分布统计
            subject_query = (
                select(
                    Homework.subject,
                    func.count(HomeworkSubmission.id).label("count"),
                    func.avg(HomeworkSubmission.total_score).label("avg_score"),
                )
                .select_from(HomeworkSubmission.join(Homework))
                .where(
                    and_(
                        HomeworkSubmission.student_id == student_id,
                        HomeworkSubmission.created_at >= cutoff_date,
                    )
                )
                .group_by(Homework.subject)
            )

            subject_result = await session.execute(subject_query)
            subject_stats = [
                {
                    "subject": row.subject,
                    "count": row.count,
                    "avg_score": round(row.avg_score, 2) if row.avg_score else None,
                }
                for row in subject_result
            ]

            # 安全处理统计结果
            if not stats:
                return {
                    "period_days": days,
                    "total_submissions": 0,
                    "completed_submissions": 0,
                    "completion_rate": 0.0,
                    "avg_score": None,
                    "avg_accuracy": None,
                    "subject_stats": [],
                    "recent_trends": [],
                }

            total_submissions = stats.total_submissions or 0
            completed_submissions = stats.completed_submissions or 0

            return {
                "period_days": days,
                "total_submissions": total_submissions,
                "completed_submissions": completed_submissions,
                "completion_rate": round(
                    (
                        (completed_submissions / total_submissions * 100)
                        if total_submissions
                        else 0
                    ),
                    2,
                ),
                "avg_score": round(stats.avg_score, 2) if stats.avg_score else None,
                "avg_accuracy": (
                    round(stats.avg_accuracy, 2) if stats.avg_accuracy else None
                ),
                "subject_distribution": subject_stats,
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise DatabaseError(f"获取统计信息失败: {e}")

    async def health_check(self, session: AsyncSession) -> bool:
        """
        健康检查 - 检查数据库连接

        Args:
            session: 数据库会话

        Returns:
            是否健康
        """
        try:
            # 简单的数据库查询测试
            await session.execute(select(func.count(Homework.id)).limit(1))
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False

    async def check_ai_service_status(self) -> bool:
        """
        检查AI服务状态

        Returns:
            AI服务是否可用
        """
        try:
            # 这里可以添加对百炼服务的健康检查
            # 目前返回True，实际项目中应该调用百炼服务的健康检查接口
            return True
        except Exception as e:
            logger.error(f"AI服务状态检查失败: {e}")
            return False


def get_homework_service() -> HomeworkService:
    """
    获取作业服务实例

    Returns:
        作业服务实例
    """
    return HomeworkService()
