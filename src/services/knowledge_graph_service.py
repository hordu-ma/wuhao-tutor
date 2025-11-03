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

            response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )

            # 解析响应（ChatCompletionResponse.content）
            result = self._parse_ai_response(response.content)
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

        改进逻辑：
        1. 尝试在 knowledge_nodes 表中查找标准化的知识点
        2. 如果找到，使用标准名称和编码
        3. 查询或创建 knowledge_mastery 记录

        Args:
            user_id: 用户ID
            subject: 学科
            knowledge_point: 知识点名称

        Returns:
            知识点掌握度记录
        """
        from sqlalchemy import and_, or_, select

        from src.models.knowledge import KnowledgeNode

        # 1. 尝试标准化知识点名称（查找 knowledge_nodes）
        standardized_name = knowledge_point
        knowledge_point_code = None

        # 查找匹配的知识点节点（名称精确匹配或模糊匹配）
        node_stmt = (
            select(KnowledgeNode)
            .where(
                and_(
                    KnowledgeNode.subject == subject,
                    or_(
                        KnowledgeNode.name == knowledge_point,
                        KnowledgeNode.name.ilike(f"%{knowledge_point}%"),
                    ),
                )
            )
            .limit(1)
        )

        node_result = await self.db.execute(node_stmt)
        knowledge_node = node_result.scalar_one_or_none()

        if knowledge_node:
            standardized_name = knowledge_node.name
            knowledge_point_code = knowledge_node.code
            logger.debug(
                f"找到标准化知识点: {standardized_name} (code: {knowledge_point_code})"
            )

        # 2. 查询是否已存在掌握度记录
        conditions = [
            KnowledgeMastery.user_id == str(user_id),
            KnowledgeMastery.subject == subject,
        ]

        # 优先按编码查找，其次按名称
        if knowledge_point_code:
            conditions.append(
                KnowledgeMastery.knowledge_point_code == knowledge_point_code
            )
        else:
            conditions.append(KnowledgeMastery.knowledge_point == standardized_name)

        stmt = select(KnowledgeMastery).where(and_(*conditions))
        result = await self.db.execute(stmt)
        km = result.scalar_one_or_none()

        if km:
            return km

        # 3. 创建新记录
        km = KnowledgeMastery(
            user_id=str(user_id),
            subject=subject,
            knowledge_point=standardized_name,
            knowledge_point_code=knowledge_point_code,
            mastery_level=0.0,
            confidence_level=0.5,
            mistake_count=0,
            correct_count=0,
            total_attempts=0,
        )
        self.db.add(km)
        await self.db.flush()

        logger.info(
            f"创建新知识点掌握度记录: {standardized_name} (code: {knowledge_point_code})"
        )
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
                assoc_id_str = getattr(assoc, "id", None)
                if assoc_id_str:
                    await self.mkp_repo.update_review_result(
                        UUID(str(assoc_id_str)), review_result, mastered
                    )

                # 6. 记录学习轨迹
                km_user_id_str = getattr(km, "user_id", None)
                km_id_str = getattr(km, "id", None)
                if km_user_id_str and km_id_str:
                    await self._record_learning_track(
                        user_id=UUID(str(km_user_id_str)),
                        knowledge_point_id=UUID(str(km_id_str)),
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
            kp_id_str = getattr(assoc, "knowledge_point_id", None)
            if not kp_id_str:
                continue

            km = await self._get_knowledge_mastery_by_id(UUID(str(kp_id_str)))
            if not km:
                continue

            # 安全地转换掌握度为float
            mastery_value = getattr(km, "mastery_level", None)
            mastery_level = float(str(mastery_value)) if mastery_value else 0.0

            mistake_count = getattr(km, "mistake_count", 0)
            review_count = getattr(assoc, "review_count", 0)
            error_type = getattr(assoc, "error_type", "")
            suggestions = getattr(assoc, "improvement_suggestions", None) or []

            chains.append(
                {
                    "knowledge_point": km.knowledge_point,
                    "mastery_level": mastery_level,
                    "mistake_count": int(mistake_count) if mistake_count else 0,
                    "review_count": int(review_count) if review_count else 0,
                    "error_type": str(error_type),
                    "suggestions": suggestions,
                }
            )

        return chains

    async def build_learning_context(self, user_id: UUID, subject: str) -> str:
        """
        构建学情上下文提示词（供AI分析时使用）

        生成一段自然语言描述，包含用户的知识掌握情况、薄弱知识链等信息

        Args:
            user_id: 用户ID
            subject: 学科

        Returns:
            学情上下文提示词
        """
        try:
            from sqlalchemy import and_, select

            # 1. 获取最新快照(如果有)
            latest_snapshot = await self.snapshot_repo.find_latest_by_user(
                user_id=user_id, subject=subject
            )

            # 2. 查询知识点掌握度
            stmt = select(KnowledgeMastery).where(
                and_(
                    KnowledgeMastery.user_id == str(user_id),
                    KnowledgeMastery.subject == subject,
                )
            )
            result = await self.db.execute(stmt)
            kms = result.scalars().all()

            if not kms:
                return "学生是初次使用系统，尚无历史学情数据。"

            # 3. 分析掌握度分布
            weak_points = []  # 掌握度 < 0.4
            learning_points = []  # 掌握度 0.4-0.7
            mastered_points = []  # 掌握度 >= 0.7

            for km in kms:
                mastery_value = getattr(km, "mastery_level", None)
                mastery = float(str(mastery_value)) if mastery_value else 0.0
                kp_name = getattr(km, "knowledge_point", "")
                mistake_cnt = getattr(km, "mistake_count", 0)

                if mastery < 0.4:
                    weak_points.append(
                        {
                            "name": kp_name,
                            "mastery": mastery,
                            "mistakes": int(mistake_cnt) if mistake_cnt else 0,
                        }
                    )
                elif mastery < 0.7:
                    learning_points.append({"name": kp_name, "mastery": mastery})
                else:
                    mastered_points.append({"name": kp_name, "mastery": mastery})

            # 4. 构建上下文提示词
            context_parts = []

            # 总体概况
            context_parts.append(f"【{subject}学科学情概况】")
            context_parts.append(
                f"学生已学习 {len(kms)} 个知识点，"
                f"其中已掌握 {len(mastered_points)} 个，"
                f"学习中 {len(learning_points)} 个，"
                f"薄弱 {len(weak_points)} 个。"
            )

            # 薄弱知识点（前5个）
            if weak_points:
                context_parts.append("\n【薄弱知识点】")
                # 按错题数量排序
                weak_sorted = sorted(
                    weak_points, key=lambda x: x["mistakes"], reverse=True
                )
                for idx, point in enumerate(weak_sorted[:5], 1):
                    context_parts.append(
                        f"{idx}. {point['name']} - "
                        f"掌握度 {point['mastery']:.1%}，错题 {point['mistakes']} 次"
                    )

            # 学习中的知识点（前3个）
            if learning_points:
                context_parts.append("\n【正在学习】")
                for idx, point in enumerate(learning_points[:3], 1):
                    context_parts.append(
                        f"{idx}. {point['name']} - 掌握度 {point['mastery']:.1%}"
                    )

            # 已掌握的知识点（前3个，仅展示名称）
            if mastered_points:
                mastered_names = [p["name"] for p in mastered_points[:3]]
                context_parts.append(
                    f"\n【已掌握】{', '.join(mastered_names)}"
                    + (
                        f" 等{len(mastered_points)}个"
                        if len(mastered_points) > 3
                        else ""
                    )
                )

            # 薄弱知识链（如果有快照）
            if latest_snapshot:
                # 使用生产环境表字段名
                weak_chains_data = getattr(latest_snapshot, "weak_chains", None)
                if weak_chains_data and isinstance(weak_chains_data, list):
                    context_parts.append("\n【薄弱知识链】")
                    for idx, chain in enumerate(weak_chains_data[:3], 1):
                        if isinstance(chain, dict):
                            kp_name = chain.get("knowledge_point", "未知知识点")
                            error_type = chain.get("error_type", "")
                            context_parts.append(
                                f"{idx}. {kp_name}"
                                + (f" (常见错误: {error_type})" if error_type else "")
                            )

            # 个性化建议方向
            context_parts.append("\n【分析建议】")
            if weak_points:
                context_parts.append(
                    "学生在上述薄弱知识点上需要重点辅导，"
                    "分析错题时请结合这些薄弱环节，给出针对性建议。"
                )
            elif learning_points:
                context_parts.append(
                    "学生整体学习进展良好，可适当提升题目难度，"
                    "巩固正在学习的知识点。"
                )
            else:
                context_parts.append(
                    "学生掌握情况优秀，可引导其进行知识拓展和综合应用训练。"
                )

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"构建学情上下文失败: {e}", exc_info=True)
            # 返回降级提示
            return "无法获取学生历史学情，请根据当前错题进行分析。"

    async def recommend_review_path(
        self, user_id: UUID, subject: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        推荐复习路径

        优先级算法：
        priority = (
            (1 - mastery_level) * 0.4 +      # 掌握度低的优先
            prerequisite_weight * 0.3 +      # 前置知识点优先
            forgetting_risk * 0.2 +          # 遗忘风险高的优先
            related_chain_weak * 0.1         # 关联链薄弱的优先
        )

        Args:
            user_id: 用户ID
            subject: 学科
            limit: 推荐数量

        Returns:
            推荐复习路径列表
        """
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import and_, select

            # 1. 获取用户所有知识点掌握度
            stmt = select(KnowledgeMastery).where(
                and_(
                    KnowledgeMastery.user_id == str(user_id),
                    KnowledgeMastery.subject == subject,
                )
            )
            result = await self.db.execute(stmt)
            kms = result.scalars().all()

            if not kms:
                return []

            # 2. 计算每个知识点的夏习优先级
            recommendations = []
            now = datetime.now()

            for km in kms:
                # 安全提取值
                mastery_value = getattr(km, "mastery_level", None)
                mastery_level = float(str(mastery_value)) if mastery_value else 0.0

                mistake_count = getattr(km, "mistake_count", 0)
                total_attempts = getattr(km, "total_attempts", 0)
                last_practiced = getattr(km, "last_practiced_at", None)

                # 跳过已经完全掌握的知识点
                if mastery_level >= 0.9:
                    continue

                # 2.1 计算掌握度因子 (0-1, 掌握度越低分数越高)
                mastery_factor = 1.0 - mastery_level

                # 2.2 计算遗忘风险因子 (0-1, 基于艾宾浩斯遗忘曲线)
                forgetting_risk = self._calculate_forgetting_risk(
                    mastery_level, last_practiced, now
                )

                # 2.3 计算前置知识点权重 (0-1)
                # 如果有较多错误且掌握度低，可能是前置知识不牢固
                prerequisite_weight = 0.0
                if mistake_count > 0 and total_attempts > 0:
                    error_rate = mistake_count / total_attempts
                    if error_rate > 0.5 and mastery_level < 0.5:
                        prerequisite_weight = 0.8  # 高优先级
                    elif error_rate > 0.3:
                        prerequisite_weight = 0.5  # 中优先级

                # 2.4 计算关联链薄弱因子 (0-1)
                # 查询该知识点的错题关联
                km_id = getattr(km, "id", None)
                related_chain_weak = 0.0
                related_mistakes = []
                if km_id:
                    related_mistakes = await self.mkp_repo.find_by_knowledge_point(
                        UUID(str(km_id))
                    )
                    if related_mistakes:
                        # 如果有多个错题关联，说明该知识点薄弱
                        related_chain_weak = min(len(related_mistakes) * 0.1, 1.0)

                # 2.5 计算总优先级
                priority = (
                    mastery_factor * 0.4
                    + prerequisite_weight * 0.3
                    + forgetting_risk * 0.2
                    + related_chain_weak * 0.1
                )

                # 2.6 构建推荐项
                kp_name = getattr(km, "knowledge_point", "")
                recommendations.append(
                    {
                        "knowledge_point_id": str(km_id) if km_id else "",
                        "knowledge_point": str(kp_name),
                        "priority": priority,
                        "mastery_level": mastery_level,
                        "mistake_count": int(mistake_count) if mistake_count else 0,
                        "forgetting_risk": forgetting_risk,
                        "reason": self._generate_review_reason(
                            mastery_level,
                            mistake_count,
                            forgetting_risk,
                            prerequisite_weight,
                        ),
                        "estimated_time": self._estimate_review_time(
                            mastery_level, mistake_count
                        ),
                        "related_mistakes_count": (
                            len(related_mistakes) if km_id and related_mistakes else 0
                        ),
                    }
                )

            # 3. 按优先级排序
            recommendations.sort(key=lambda x: x["priority"], reverse=True)

            # 4. 返回前 N 个推荐
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"生成复习推荐失败: {e}", exc_info=True)
            return []

    def _calculate_forgetting_risk(
        self,
        mastery_level: float,
        last_practiced: Optional[datetime],
        now: datetime,
    ) -> float:
        """
        计算遗忘风险

        基于艾宾浩斯遗忘曲线：
        - 1天内：遗忘56%
        - 1周内：遗忘77%
        - 1个月：遗忘79%

        掌握度越高，遗忘速度越慢

        Args:
            mastery_level: 掌握度
            last_practiced: 上次练习时间
            now: 当前时间

        Returns:
            遗忘风险 (0.0-1.0)
        """
        if not last_practiced:
            # 从未练习过，风险较低
            return 0.3

        from datetime import timedelta

        # 计算距离上次练习的天数
        days_since_practice = (now - last_practiced).days

        # 根据掌握度调整遗忘速度
        # 掌握度高的知识点遗忘较慢
        mastery_factor = 1.0 - mastery_level * 0.5

        # 基于艾宾浩斯曲线计算遗忘率
        if days_since_practice <= 1:
            forgetting_rate = 0.56
        elif days_since_practice <= 2:
            forgetting_rate = 0.66
        elif days_since_practice <= 7:
            forgetting_rate = 0.77
        elif days_since_practice <= 14:
            forgetting_rate = 0.85
        elif days_since_practice <= 30:
            forgetting_rate = 0.79
        else:
            forgetting_rate = 0.90

        # 结合掌握度因子
        risk = forgetting_rate * mastery_factor

        return min(risk, 1.0)

    def _generate_review_reason(
        self,
        mastery_level: float,
        mistake_count: int,
        forgetting_risk: float,
        prerequisite_weight: float,
    ) -> str:
        """
        生成复习理由

        Args:
            mastery_level: 掌握度
            mistake_count: 错误次数
            forgetting_risk: 遗忘风险
            prerequisite_weight: 前置知识点权重

        Returns:
            复习理由
        """
        reasons = []

        if mastery_level < 0.4:
            reasons.append("掌握度较低，需要重点复习")
        elif mastery_level < 0.7:
            reasons.append("正在学习中，需要巩固")

        if mistake_count > 5:
            reasons.append(f"已出现{mistake_count}次错误")
        elif mistake_count > 0:
            reasons.append("有错误记录")

        if forgetting_risk > 0.7:
            reasons.append("遗忘风险高")
        elif forgetting_risk > 0.5:
            reasons.append("有遗忘风险")

        if prerequisite_weight > 0.5:
            reasons.append("前置知识可能不牢固")

        return "，".join(reasons) if reasons else "建议定期复习"

    def _estimate_review_time(self, mastery_level: float, mistake_count: int) -> int:
        """
        估算复习时间（分钟）

        Args:
            mastery_level: 掌握度
            mistake_count: 错误次数

        Returns:
            估计复习时间（分钟）
        """
        # 基础时间：10分钟
        base_time = 10

        # 掌握度越低，需要的时间越多
        mastery_time = int((1.0 - mastery_level) * 20)

        # 错误次数越多，需要的时间越多
        mistake_time = min(mistake_count * 2, 20)

        total_time = base_time + mastery_time + mistake_time

        # 限制在 5-60 分钟范围内
        return max(5, min(total_time, 60))

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
                # 安全地转换掌握度为float
                mastery_value = getattr(km, "mastery_level", None)
                mastery = float(str(mastery_value)) if mastery_value else 0.0

                km_id = getattr(km, "id", "")
                kp_name = getattr(km, "knowledge_point", "")
                mistake_cnt = getattr(km, "mistake_count", 0)
                correct_cnt = getattr(km, "correct_count", 0)

                graph_data["nodes"].append(
                    {
                        "id": str(km_id),
                        "name": str(kp_name),
                        "mastery": mastery,
                        "mistake_count": int(mistake_cnt) if mistake_cnt else 0,
                        "correct_count": int(correct_cnt) if correct_cnt else 0,
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
