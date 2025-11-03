"""
知识图谱服务层
提供知识点关联、图谱构建、学习轨迹追踪等业务逻辑

作者: AI Agent
创建时间: 2025-11-03
版本: v1.0
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ServiceError, ValidationError
from src.models.knowledge_graph import (
    ErrorType,
    KnowledgePointLearningTrack,
    MistakeKnowledgePoint,
    UserKnowledgeGraphSnapshot,
)
from src.models.study import KnowledgeMastery, MistakeRecord
from src.repositories.knowledge_graph_repository import (
    KnowledgePointLearningTrackRepository,
    MistakeKnowledgePointRepository,
    UserKnowledgeGraphSnapshotRepository,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self, db: AsyncSession, bailian_service=None):
        self.db = db
        self.mkp_repo = MistakeKnowledgePointRepository(MistakeKnowledgePoint, db)
        self.snapshot_repo = UserKnowledgeGraphSnapshotRepository(
            UserKnowledgeGraphSnapshot, db
        )
        self.track_repo = KnowledgePointLearningTrackRepository(
            KnowledgePointLearningTrack, db
        )
        self.bailian_service = bailian_service

    async def analyze_and_associate_knowledge_points(
        self,
        mistake_id: UUID,
        user_id: UUID,
        subject: str,
        ocr_text: Optional[str] = None,
        ai_feedback: Optional[Dict[str, Any]] = None,
    ) -> List[MistakeKnowledgePoint]:
        """
        分析错题并关联知识点

        Args:
            mistake_id: 错题ID
            user_id: 用户ID
            subject: 学科
            ocr_text: OCR识别文本
            ai_feedback: AI反馈结果

        Returns:
            创建的知识点关联列表
        """
        try:
            # 1. 从AI反馈中提取知识点列表
            knowledge_points = self._extract_knowledge_points(ai_feedback)

            if not knowledge_points:
                # 如果AI反馈中没有，尝试使用百炼AI分析
                if self.bailian_service and ocr_text:
                    knowledge_points = await self._ai_analyze_knowledge_points(
                        ocr_text, subject
                    )

            if not knowledge_points:
                logger.warning(f"无法为错题 {mistake_id} 提取知识点，跳过关联")
                return []

            # 2. 查询或创建知识点掌握度记录
            associations = []
            for idx, kp_data in enumerate(knowledge_points):
                kp_name = kp_data.get("name") or kp_data.get("knowledge_point")
                if not kp_name:
                    continue

                # 查询知识点掌握度记录
                km = await self._get_or_create_knowledge_mastery(
                    user_id, subject, kp_name
                )

                # 创建关联记录
                assoc_data = {
                    "mistake_id": str(mistake_id),
                    "knowledge_point_id": str(km.id),
                    "relevance_score": kp_data.get("relevance", 0.8),
                    "is_primary": idx == 0,  # 第一个知识点为主要知识点
                    "error_type": kp_data.get("error_type", ErrorType.OTHER.value),
                    "error_reason": kp_data.get("error_reason"),
                    "ai_diagnosis": kp_data.get("diagnosis"),
                    "improvement_suggestions": kp_data.get("suggestions", []),
                }

                associations.append(assoc_data)

            # 3. 批量创建关联
            created = await self.mkp_repo.batch_create_associations(associations)
            await self.db.commit()

            logger.info(f"为错题 {mistake_id} 创建了 {len(created)} 个知识点关联")

            # 4. 记录学习轨迹
            for assoc in created:
                kp_id_str = getattr(assoc, "knowledge_point_id", None)
                if kp_id_str:
                    await self._record_learning_track(
                        user_id=user_id,
                        knowledge_point_id=UUID(str(kp_id_str)),
                        mistake_id=mistake_id,
                        activity_type="mistake_creation",
                        result="incorrect",
                    )

            return created

        except Exception as e:
            await self.db.rollback()
            logger.error(f"分析并关联知识点失败: {e}", exc_info=True)
            raise ServiceError(f"知识点关联失败: {str(e)}")

    def _extract_knowledge_points(
        self, ai_feedback: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从AI反馈中提取知识点列表

        Args:
            ai_feedback: AI反馈结果

        Returns:
            知识点列表
        """
        if not ai_feedback:
            return []

        # 尝试多种可能的字段名
        knowledge_points = (
            ai_feedback.get("knowledge_points")
            or ai_feedback.get("涉及知识点")
            or ai_feedback.get("知识点")
            or []
        )

        # 如果是字符串列表，转换为字典列表
        if knowledge_points and isinstance(knowledge_points[0], str):
            knowledge_points = [{"name": kp} for kp in knowledge_points]

        return knowledge_points

    async def _ai_analyze_knowledge_points(
        self, ocr_text: str, subject: str
    ) -> List[Dict[str, Any]]:
        """
        使用AI分析题目涉及的知识点

        Args:
            ocr_text: 题目文本
            subject: 学科

        Returns:
            知识点列表
        """
        if not self.bailian_service:
            return []

        try:
            prompt = f"""请分析以下{subject}题目，提取涉及的知识点：

题目：
{ocr_text}

请按照以下格式返回JSON：
{{
    "knowledge_points": [
        {{
            "name": "知识点名称",
            "relevance": 0.9,
            "error_type": "concept_misunderstanding",
            "error_reason": "错误原因分析",
            "diagnosis": {{"key": "value"}},
            "suggestions": ["建议1", "建议2"]
        }}
    ]
}}

错误类型可选值：
- concept_misunderstanding: 概念理解错误
- calculation_error: 计算错误
- formula_misuse: 公式使用错误
- logic_error: 逻辑推理错误
- knowledge_gap: 知识盲区
- method_confusion: 方法混淆
- other: 其他
"""

            response = await self.bailian_service.chat(
                user_input=prompt,
                user_id="system",
                session_id="kg_analysis",
            )

            # 解析响应
            result = self._parse_ai_response(response.get("content", ""))
            return result.get("knowledge_points", [])

        except Exception as e:
            logger.error(f"AI分析知识点失败: {e}")
            return []

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """解析AI响应中的JSON"""
        try:
            # 尝试提取JSON部分
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # 尝试直接解析
            return json.loads(content)
        except Exception as e:
            logger.warning(f"解析AI响应失败: {e}")
            return {}

    async def _get_or_create_knowledge_mastery(
        self, user_id: UUID, subject: str, knowledge_point: str
    ) -> KnowledgeMastery:
        """
        查询或创建知识点掌握度记录

        Args:
            user_id: 用户ID
            subject: 学科
            knowledge_point: 知识点名称

        Returns:
            知识点掌握度记录
        """
        from sqlalchemy import and_, select

        # 查询是否已存在
        stmt = select(KnowledgeMastery).where(
            and_(
                KnowledgeMastery.user_id == str(user_id),
                KnowledgeMastery.subject == subject,
                KnowledgeMastery.knowledge_point == knowledge_point,
            )
        )
        result = await self.db.execute(stmt)
        km = result.scalar_one_or_none()

        if km:
            return km

        # 创建新记录
        km = KnowledgeMastery(
            user_id=str(user_id),
            subject=subject,
            knowledge_point=knowledge_point,
            mastery_level=0.0,
            confidence_level=0.5,
            mistake_count=0,
            correct_count=0,
            total_attempts=0,
        )
        self.db.add(km)
        await self.db.flush()

        logger.info(f"创建新知识点掌握度记录: {knowledge_point}")
        return km

    async def _record_learning_track(
        self,
        user_id: UUID,
        knowledge_point_id: UUID,
        mistake_id: Optional[UUID],
        activity_type: str,
        result: str,
        mastery_before: Optional[float] = None,
        mastery_after: Optional[float] = None,
        **kwargs,
    ) -> KnowledgePointLearningTrack:
        """
        记录学习轨迹

        Args:
            user_id: 用户ID
            knowledge_point_id: 知识点ID
            mistake_id: 错题ID
            activity_type: 活动类型
            result: 结果
            mastery_before: 活动前掌握度
            mastery_after: 活动后掌握度
            **kwargs: 其他参数

        Returns:
            学习轨迹记录
        """
        track_data = {
            "user_id": str(user_id),
            "knowledge_point_id": str(knowledge_point_id),
            "mistake_id": str(mistake_id) if mistake_id else None,
            "activity_type": activity_type,
            "result": result,
            "mastery_before": mastery_before,
            "mastery_after": mastery_after,
            **kwargs,
        }

        track = await self.track_repo.record_activity(track_data)
        await self.db.commit()

        return track

    async def update_knowledge_mastery_after_review(
        self,
        mistake_id: UUID,
        review_result: str,
        confidence_level: int = 3,
    ) -> None:
        """
        复习后更新知识点掌握度

        Args:
            mistake_id: 错题ID
            review_result: 复习结果 (correct/incorrect/partial)
            confidence_level: 信心等级 (1-5)
        """
        try:
            # 1. 获取错题关联的知识点
            associations = await self.mkp_repo.find_by_mistake(mistake_id)

            if not associations:
                logger.warning(f"错题 {mistake_id} 没有关联知识点，跳过更新")
                return

            # 2. 更新每个知识点的掌握度
            for assoc in associations:
                kp_id_str = getattr(assoc, "knowledge_point_id", None)
                if not kp_id_str:
                    continue

                km = await self._get_knowledge_mastery_by_id(UUID(str(kp_id_str)))

                if not km:
                    continue

                # 记录更新前的掌握度（安全转换）
                mastery_before_value = getattr(km, "mastery_level", None)
                mastery_before = (
                    float(str(mastery_before_value)) if mastery_before_value else 0.0
                )

                # 3. 计算新的掌握度
                total_attempts_value = getattr(km, "total_attempts", 0)
                total_attempts = (
                    int(total_attempts_value) if total_attempts_value else 0
                )

                mastery_after = self._calculate_mastery_level(
                    current_mastery=mastery_before,
                    review_result=review_result,
                    confidence_level=confidence_level,
                    total_attempts=total_attempts,
                )

                # 4. 更新知识点掌握度（使用setattr避免类型检查问题）
                setattr(km, "total_attempts", total_attempts + 1)
                if review_result == "correct":
                    correct_count = getattr(km, "correct_count", 0)
                    setattr(km, "correct_count", int(correct_count) + 1)
                else:
                    mistake_count = getattr(km, "mistake_count", 0)
                    setattr(km, "mistake_count", int(mistake_count) + 1)

                setattr(km, "mastery_level", mastery_after)
                setattr(km, "confidence_level", confidence_level / 5.0)
                setattr(km, "last_practiced_at", datetime.now())

                # 如果首次掌握（mastery >= 0.8）
                first_mastered = getattr(km, "first_mastered_at", None)
                if mastery_after >= 0.8 and not first_mastered:
                    setattr(km, "first_mastered_at", datetime.now())

                # 5. 更新关联记录
                mastered = review_result == "correct" and mastery_after >= 0.8
                await self.mkp_repo.update_review_result(
                    UUID(assoc.id), review_result, mastered
                )

                # 6. 记录学习轨迹
                await self._record_learning_track(
                    user_id=UUID(km.user_id),
                    knowledge_point_id=UUID(km.id),
                    mistake_id=mistake_id,
                    activity_type="review",
                    result=review_result,
                    mastery_before=mastery_before,
                    mastery_after=mastery_after,
                    confidence_level=confidence_level,
                )

            await self.db.commit()
            logger.info(
                f"已更新错题 {mistake_id} 关联的 {len(associations)} 个知识点掌握度"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新知识点掌握度失败: {e}", exc_info=True)
            raise ServiceError(f"更新知识点掌握度失败: {str(e)}")

    async def _get_knowledge_mastery_by_id(
        self, km_id: UUID
    ) -> Optional[KnowledgeMastery]:
        """根据ID查询知识点掌握度"""
        from sqlalchemy import select

        stmt = select(KnowledgeMastery).where(KnowledgeMastery.id == str(km_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _calculate_mastery_level(
        self,
        current_mastery: float,
        review_result: str,
        confidence_level: int,
        total_attempts: int,
    ) -> float:
        """
        计算新的掌握度

        使用简化的学习曲线算法：
        - correct: +0.1 * confidence_factor
        - incorrect: -0.15
        - partial: +0.05

        Args:
            current_mastery: 当前掌握度
            review_result: 复习结果
            confidence_level: 信心等级 (1-5)
            total_attempts: 总尝试次数

        Returns:
            新的掌握度 (0.0-1.0)
        """
        # 信心系数 (0.2 - 1.0)
        confidence_factor = confidence_level / 5.0

        # 根据结果调整
        if review_result == "correct":
            delta = 0.1 * confidence_factor
        elif review_result == "incorrect":
            delta = -0.15
        elif review_result == "partial":
            delta = 0.05
        else:
            delta = 0.0

        # 学习次数衰减（前几次学习效果更明显）
        attempt_factor = 1.0 / (1.0 + total_attempts * 0.1)
        delta *= attempt_factor

        new_mastery = current_mastery + delta

        # 限制在 [0.0, 1.0] 范围内
        return max(0.0, min(1.0, new_mastery))

    async def get_weak_knowledge_chains(
        self, user_id: UUID, subject: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        识别薄弱知识链

        Args:
            user_id: 用户ID
            subject: 学科
            limit: 返回数量

        Returns:
            薄弱知识链列表
        """
        # 获取薄弱知识点关联
        weak_assocs = await self.mkp_repo.get_weak_associations(user_id, subject, limit)

        chains = []
        for assoc in weak_assocs:
            km = await self._get_knowledge_mastery_by_id(UUID(assoc.knowledge_point_id))
            if not km:
                continue

            chains.append(
                {
                    "knowledge_point": km.knowledge_point,
                    "mastery_level": float(km.mastery_level or 0),
                    "mistake_count": km.mistake_count,
                    "review_count": assoc.review_count,
                    "error_type": assoc.error_type,
                    "suggestions": assoc.improvement_suggestions or [],
                }
            )

        return chains

    async def create_knowledge_graph_snapshot(
        self, user_id: UUID, subject: str, period_type: str = "manual"
    ) -> UserKnowledgeGraphSnapshot:
        """
        创建知识图谱快照

        Args:
            user_id: 用户ID
            subject: 学科
            period_type: 周期类型

        Returns:
            创建的快照
        """
        from sqlalchemy import and_, select

        try:
            # 1. 查询用户该学科的所有知识点掌握度
            stmt = select(KnowledgeMastery).where(
                and_(
                    KnowledgeMastery.user_id == str(user_id),
                    KnowledgeMastery.subject == subject,
                )
            )
            result = await self.db.execute(stmt)
            kms = result.scalars().all()

            # 2. 构建图谱数据
            graph_data = {"nodes": [], "edges": []}
            mastery_distribution = {
                "weak": 0,  # < 0.4
                "learning": 0,  # 0.4-0.7
                "mastered": 0,  # >= 0.7
            }

            for km in kms:
                mastery = float(km.mastery_level or 0)
                graph_data["nodes"].append(
                    {
                        "id": str(km.id),
                        "name": km.knowledge_point,
                        "mastery": mastery,
                        "mistake_count": km.mistake_count,
                        "correct_count": km.correct_count,
                    }
                )

                # 统计分布
                if mastery < 0.4:
                    mastery_distribution["weak"] += 1
                elif mastery < 0.7:
                    mastery_distribution["learning"] += 1
                else:
                    mastery_distribution["mastered"] += 1

            # 3. 识别薄弱知识链
            weak_chains = await self.get_weak_knowledge_chains(user_id, subject)

            # 4. 创建快照
            snapshot_data = {
                "user_id": str(user_id),
                "subject": subject,
                "period_type": period_type,
                "graph_data": graph_data,
                "mastery_distribution": mastery_distribution,
                "weak_knowledge_chains": weak_chains,
                "total_knowledge_points": len(kms),
                "mastered_count": mastery_distribution["mastered"],
                "learning_count": mastery_distribution["learning"],
                "weak_count": mastery_distribution["weak"],
            }

            snapshot = await self.snapshot_repo.create_snapshot(snapshot_data)
            await self.db.commit()

            logger.info(f"为用户 {user_id} 创建了 {subject} 知识图谱快照")
            return snapshot

        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建知识图谱快照失败: {e}", exc_info=True)
            raise ServiceError(f"创建快照失败: {str(e)}")
