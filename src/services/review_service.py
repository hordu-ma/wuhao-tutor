"""
复习服务层
提供错题复习会话管理、状态推进、答案提交等业务逻辑

三阶段复习逻辑：
1. 原题复习：显示原错题，验证基础掌握
2. 变体题挑战：通过 AI 生成相似题目，测试知识迁移
3. 知识点巩固：推荐相关知识点题目，深化理解
"""

import json
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ServiceError
from src.core.logging import get_logger
from src.repositories.mistake_repository import MistakeRepository
from src.repositories.review_repository import ReviewRepository
from src.services.bailian_service import BailianService

logger = get_logger(__name__)


class ReviewService:
    """复习服务类"""

    # 复习阶段常量
    STAGE_ORIGINAL = 1  # 原题复习
    STAGE_VARIANT = 2  # 变体题
    STAGE_KNOWLEDGE = 3  # 知识点巩固

    # 会话状态常量
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED_SUCCESS = "completed_success"
    STATUS_COMPLETED_FAIL = "completed_fail"

    def __init__(
        self,
        db: AsyncSession,
        review_repo: ReviewRepository,
        mistake_repo: MistakeRepository,
        bailian_service: BailianService,
    ):
        self.db = db
        self.review_repo = review_repo
        self.mistake_repo = mistake_repo
        self.bailian_service = bailian_service

    async def start_review_session(
        self, user_id: UUID, mistake_id: UUID
    ) -> Dict[str, Any]:
        """
        开始新的复习会话

        Args:
            user_id: 用户ID
            mistake_id: 错题ID

        Returns:
            包含会话ID、阶段、题目内容的字典

        Raises:
            NotFoundError: 错题不存在或不属于该用户
            ServiceError: 错题缺少必要内容
        """
        # 验证错题存在且属于该用户
        mistake = await self.mistake_repo.find_by_id(mistake_id)
        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"Mistake {mistake_id} not found for user {user_id}")

        # 创建复习会话（初始阶段为1）
        session_data = {
            "user_id": str(user_id),
            "mistake_id": str(mistake_id),
            "status": self.STATUS_IN_PROGRESS,
            "current_stage": self.STAGE_ORIGINAL,
            "attempts": 0,
        }
        review_session = await self.review_repo.create(session_data)

        logger.info(
            f"Started review session {review_session.id} "
            f"for user {user_id} mistake {mistake_id}"
        )

        # 返回原题内容（如果没有OCR文本，使用占位提示）
        question_content = mistake.ocr_text or "暂无题目内容，请先上传并识别题目图片"

        return {
            "session_id": str(review_session.id),
            "stage": self.STAGE_ORIGINAL,
            "stage_name": "原题复习",
            "question_content": question_content,
            "correct_answer": mistake.correct_answer or "",
            "knowledge_points": mistake.knowledge_points or [],
            "has_ocr_text": bool(mistake.ocr_text),  # 标记是否有OCR文本
        }

    async def get_review_session(
        self, session_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        """
        获取复习会话当前状态

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            包含会话状态和当前题目的字典

        Raises:
            NotFoundError: 会话不存在或不属于该用户
        """
        session = await self.review_repo.find_by_id(session_id)
        if not session or str(session.user_id) != str(user_id):
            raise NotFoundError(
                f"Review session {session_id} not found for user {user_id}"
            )

        mistake = await self.mistake_repo.find_by_id(session.mistake_id)
        if not mistake:
            raise NotFoundError(f"Associated mistake {session.mistake_id} not found")

        # 根据当前阶段返回对应内容
        stage_name = self._get_stage_name(session.current_stage)

        # 使用占位文本处理无OCR内容的情况
        question_content = mistake.ocr_text or "暂无题目内容，请先上传并识别题目图片"

        return {
            "session_id": str(session.id),
            "stage": session.current_stage,
            "stage_name": stage_name,
            "status": session.status,
            "attempts": session.attempts,
            "question_content": question_content,
            "correct_answer": mistake.correct_answer or "",
            "knowledge_points": mistake.knowledge_points or [],
            "has_ocr_text": bool(mistake.ocr_text),
        }

    async def submit_review_answer(
        self, session_id: UUID, user_id: UUID, answer: str = "", skip: bool = False
    ) -> Dict[str, Any]:
        """
        提交复习答案并推进会话状态（AI判断版本）

        Args:
            session_id: 会话ID
            user_id: 用户ID
            answer: 用户提交的答案
            skip: 是否跳过（不会做，查看答案）

        Returns:
            包含结果和下一阶段信息的字典

        Raises:
            NotFoundError: 会话不存在
            ServiceError: 会话已结束
        """
        # 获取会话和错题
        session = await self.review_repo.find_by_id(session_id)
        if not session or str(session.user_id) != str(user_id):
            raise NotFoundError(
                f"Review session {session_id} not found for user {user_id}"
            )

        if session.status != self.STATUS_IN_PROGRESS:
            raise ServiceError(f"Review session {session_id} is already completed")

        mistake = await self.mistake_repo.find_by_id(session.mistake_id)
        if not mistake:
            raise NotFoundError(f"Associated mistake {session.mistake_id} not found")

        # 更新尝试次数
        session.attempts += 1

        # 场景1: 用户点"不会做，查看答案" → 直接失败
        if skip:
            session.status = self.STATUS_COMPLETED_FAIL
            await self.review_repo.update(
                session.id,
                {
                    "status": session.status,
                    "current_stage": session.current_stage,
                    "attempts": session.attempts,
                },
            )
            await self.db.commit()

            logger.info(
                f"Review session {session_id} skipped at stage {session.current_stage}"
            )

            return {
                "session_id": str(session.id),
                "correct": False,
                "skip": True,
                "status": self.STATUS_COMPLETED_FAIL,
                "standard_answer": mistake.correct_answer or "暂无标准答案",
                "analysis": "",
                "knowledge_points": mistake.knowledge_points,
                "message": "建议重新学习后再复习",
            }

        # 场景2: 用户提交答案 → AI判断
        if not answer or not answer.strip():
            raise ServiceError("答案不能为空")

        # 调用AI判断答案正确性
        try:
            judge_result = await self.bailian_service.judge_answer(
                question=mistake.ocr_text or mistake.title or "",
                standard_answer=mistake.correct_answer or "",
                user_answer=answer,
            )
            is_correct = judge_result["is_correct"]
            ai_feedback = judge_result["feedback"]
            score = judge_result["score"]
        except Exception as e:
            logger.error(f"AI判断答案失败: {e}")
            # 降级：简单匹配
            is_correct = answer.strip() == (mistake.correct_answer or "").strip()
            ai_feedback = "AI判断服务暂时不可用"
            score = 100 if is_correct else 0

        # 答案错误 → 会话失败结束
        if not is_correct:
            session.status = self.STATUS_COMPLETED_FAIL
            await self.review_repo.update(
                session.id,
                {
                    "status": session.status,
                    "current_stage": session.current_stage,
                    "attempts": session.attempts,
                },
            )
            await self.db.commit()

            logger.info(
                f"Review session {session_id} failed at stage {session.current_stage}, score: {score}"
            )

            return {
                "session_id": str(session.id),
                "correct": False,
                "skip": False,
                "status": self.STATUS_COMPLETED_FAIL,
                "user_answer": answer,
                "standard_answer": mistake.correct_answer or "暂无标准答案",
                "ai_feedback": ai_feedback,
                "score": score,
                "knowledge_points": mistake.knowledge_points,
                "message": "答案需要改进",
            }

        # 答案正确 → 推进到下一阶段或完成
        current_stage = session.current_stage

        if current_stage == self.STAGE_KNOWLEDGE:
            # 第三阶段完成 → 会话成功结束
            session.status = self.STATUS_COMPLETED_SUCCESS
            await self.review_repo.update(
                session.id,
                {
                    "status": session.status,
                    "attempts": session.attempts,
                },
            )
            await self.db.commit()

            # 更新错题的复习统计
            await self._update_mistake_stats(mistake, success=True)

            logger.info(f"Review session {session_id} completed successfully")

            return {
                "session_id": str(session.id),
                "correct": True,
                "status": self.STATUS_COMPLETED_SUCCESS,
                "ai_feedback": ai_feedback,
                "score": score,
                "message": "恭喜！完成三阶段复习，知识点已掌握",
            }

        # 推进到下一阶段
        next_stage = current_stage + 1
        session.current_stage = next_stage
        await self.review_repo.update(
            session.id,
            {
                "current_stage": session.current_stage,
                "attempts": session.attempts,
            },
        )
        await self.db.commit()

        # 生成下一阶段题目
        next_question = await self._generate_question_for_stage(mistake, next_stage)

        logger.info(f"Review session {session_id} progressed to stage {next_stage}")

        return {
            "session_id": str(session.id),
            "correct": True,
            "next_stage": next_stage,
            "stage_name": self._get_stage_name(next_stage),
            "next_question": next_question,
            "ai_feedback": ai_feedback,
            "score": score,
        }

    async def _generate_question_for_stage(self, mistake, stage: int) -> Dict[str, Any]:
        """
        为指定阶段生成题目

        Args:
            mistake: 错题记录
            stage: 阶段编号

        Returns:
            包含题目内容的字典
        """
        if stage == self.STAGE_VARIANT:
            # 阶段2：调用百炼生成变体题
            return await self._generate_variant_question(mistake)
        elif stage == self.STAGE_KNOWLEDGE:
            # 阶段3：推荐知识点巩固题
            return await self._generate_knowledge_question(mistake)
        else:
            raise ServiceError(f"Invalid stage {stage}")

    async def _generate_variant_question(self, mistake) -> Dict[str, Any]:
        """
        调用百炼 AI 生成变体题

        Args:
            mistake: 错题记录

        Returns:
            包含变体题内容的字典
        """
        try:
            prompt = f"""请基于以下错题生成一道相似的变体题目，保持知识点和难度一致，但改变题目场景和数据。

原题内容：
{mistake.ocr_text}

知识点：
{json.dumps(mistake.knowledge_points, ensure_ascii=False)}

要求：
1. 保持考察的知识点不变
2. 改变题目的具体数据和场景
3. 难度与原题相当
4. 返回格式：题目内容 + 标准答案

请直接返回生成的题目和答案，不要额外解释。"""

            response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # 适当创造性
            )

            variant_content = response.get("content", "")
            if not variant_content:
                raise ServiceError("AI failed to generate variant question")

            logger.info(f"Generated variant question for mistake {mistake.id}")

            return {
                "question_content": variant_content,
                "source": "ai_generated",
            }

        except Exception as e:
            logger.error(f"Failed to generate variant question: {e}")
            # 降级：返回原题的简化版本
            return {
                "question_content": f"【变体题】{mistake.ocr_text}",
                "source": "fallback",
                "error": str(e),
            }

    async def _generate_knowledge_question(self, mistake) -> Dict[str, Any]:
        """
        推荐知识点巩固题（简化版：使用AI生成）

        Args:
            mistake: 错题记录

        Returns:
            包含巩固题内容的字典
        """
        try:
            knowledge_points = mistake.knowledge_points or []
            if not knowledge_points:
                knowledge_points = ["基础知识"]

            prompt = f"""请针对以下知识点生成一道巩固练习题。

知识点：
{json.dumps(knowledge_points, ensure_ascii=False)}

要求：
1. 综合考察这些知识点
2. 难度适中，注重理解和应用
3. 返回格式：题目内容 + 标准答案

请直接返回生成的题目和答案，不要额外解释。"""

            response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )

            knowledge_content = response.get("content", "")
            if not knowledge_content:
                raise ServiceError("AI failed to generate knowledge question")

            logger.info(f"Generated knowledge question for mistake {mistake.id}")

            return {
                "question_content": knowledge_content,
                "knowledge_points": knowledge_points,
                "source": "ai_generated",
            }

        except Exception as e:
            logger.error(f"Failed to generate knowledge question: {e}")
            return {
                "question_content": f"【知识点巩固】请总结 {knowledge_points} 的核心要点",
                "source": "fallback",
                "error": str(e),
            }

    async def _update_mistake_stats(self, mistake, success: bool):
        """
        更新错题的复习统计信息

        Args:
            mistake: 错题记录
            success: 是否成功完成复习
        """
        try:
            mistake.review_count = (mistake.review_count or 0) + 1
            if success:
                mistake.correct_count = (mistake.correct_count or 0) + 1
                if mistake.correct_count >= 3:  # 连续3次正确视为掌握
                    mistake.mastery_status = "mastered"

            from datetime import datetime

            mistake.last_review_at = datetime.utcnow()

            await self.mistake_repo.update(mistake.id, mistake.__dict__)
            logger.info(f"Updated mistake {mistake.id} stats: success={success}")

        except Exception as e:
            logger.error(f"Failed to update mistake stats: {e}")
            # 不抛出异常，避免影响主流程

    @staticmethod
    def _get_stage_name(stage: int) -> str:
        """获取阶段名称"""
        stage_names = {
            1: "原题复习",
            2: "变体题挑战",
            3: "知识点巩固",
        }
        return stage_names.get(stage, "未知阶段")
