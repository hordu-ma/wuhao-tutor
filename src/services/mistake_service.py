"""
错题手册服务层
提供错题管理、复习计划、统计分析等业务逻辑

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ServiceError, ValidationError
from src.models.base import is_sqlite
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

    @staticmethod
    def _safe_extract_orm(obj: Any, attr: str, default: Any = None) -> Any:
        """安全地从ORM对象提取属性值"""
        try:
            value = getattr(obj, attr, default)
            # 如果是Column对象，返回默认值
            if hasattr(value, "__class__") and "Column" in str(type(value)):
                return default
            return value if value is not None else default
        except Exception:
            return default

    async def _to_list_item(self, mistake: MistakeRecord) -> MistakeListItem:
        """转换为列表项（包含知识点关联信息）"""
        from uuid import UUID as UUIDType

        from src.utils.type_converters import (
            extract_orm_int,
            extract_orm_str,
            extract_orm_uuid_str,
        )

        # 在SQLite中，日期字段是字符串；在PostgreSQL中是datetime对象
        # 需要处理两种情况
        def to_iso_string(value):
            """将日期字段转换为ISO格式字符串"""
            if value is None:
                return None
            if isinstance(value, str):
                return value  # SQLite中已经是字符串
            return value.isoformat()  # PostgreSQL中是datetime对象

        def parse_json_field(value):
            """解析JSON字段，兼容字符串和已解析的对象"""
            if value is None:
                return []
            if isinstance(value, list):
                return value  # 已经是列表
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else []
                except (json.JSONDecodeError, ValueError):
                    return []
            return []

        # 🎯 查询知识点关联信息（用于列表页显示掌握度）
        knowledge_point_associations = []
        try:
            from src.models.knowledge_graph import MistakeKnowledgePoint
            from src.models.study import KnowledgeMastery
            from src.repositories.base_repository import BaseRepository
            from src.repositories.knowledge_graph_repository import (
                MistakeKnowledgePointRepository,
            )

            mkp_repo = MistakeKnowledgePointRepository(MistakeKnowledgePoint, self.db)
            km_repo = BaseRepository(KnowledgeMastery, self.db)

            # 查询错题的知识点关联
            mistake_id = UUID(extract_orm_uuid_str(mistake, "id"))
            associations = await mkp_repo.find_by_mistake(mistake_id)

            # 只取前3个知识点（列表页不需要全部显示）
            for assoc in associations[:3]:
                kp_id = UUID(str(getattr(assoc, "knowledge_point_id")))
                mastery = await km_repo.get_by_id(str(kp_id))

                knowledge_point_associations.append(
                    {
                        "association_id": str(getattr(assoc, "id")),
                        "knowledge_point_id": str(kp_id),
                        "knowledge_point_name": (
                            getattr(mastery, "knowledge_point", "未知知识点")
                            if mastery
                            else "未知知识点"
                        ),
                        "relevance_score": float(
                            str(getattr(assoc, "relevance_score", 0.0))
                        ),
                        "is_primary": getattr(assoc, "is_primary", False),
                        "mastery_level": (
                            float(str(getattr(mastery, "mastery_level", 0.0)))
                            if mastery
                            else 0.0
                        ),
                    }
                )

        except Exception as e:
            # 知识点关联查询失败不影响列表返回
            logger.warning(f"查询错题 {mistake.id} 的知识点关联失败: {e}")

        return MistakeListItem(
            id=UUID(extract_orm_uuid_str(mistake, "id")),
            title=extract_orm_str(mistake, "title") or "未命名错题",
            subject=extract_orm_str(mistake, "subject"),
            difficulty_level=extract_orm_int(mistake, "difficulty_level"),
            source=extract_orm_str(mistake, "source"),
            source_id=None,
            mastery_status=extract_orm_str(mistake, "mastery_status"),
            correct_count=extract_orm_int(mistake, "correct_count") or 0,
            total_reviews=extract_orm_int(mistake, "review_count") or 0,
            next_review_date=to_iso_string(getattr(mistake, "next_review_at", None)),
            created_at=to_iso_string(getattr(mistake, "created_at", None)) or "",
            updated_at=to_iso_string(
                getattr(mistake, "updated_at", None)
            ),  # ✅ 添加updated_at
            knowledge_points=parse_json_field(
                getattr(mistake, "knowledge_points", None)
            ),
            knowledge_point_associations=knowledge_point_associations,  # 🎯 添加关联信息
        )

    async def _to_detail_response(
        self, mistake: MistakeRecord
    ) -> MistakeDetailResponse:
        """转换为详情响应"""
        from src.utils.type_converters import (
            extract_orm_int,
            extract_orm_str,
            extract_orm_uuid_str,
        )

        # 在SQLite中，日期字段是字符串；在PostgreSQL中是datetime对象
        # 需要处理两种情况
        def to_iso_string(value):
            """将日期字段转换为ISO格式字符串"""
            if value is None:
                return None
            if isinstance(value, str):
                return value  # SQLite中已经是字符串
            return value.isoformat()  # PostgreSQL中是datetime对象

        def parse_json_field(value):
            """解析JSON字段，兼容字符串和已解析的对象"""
            if value is None:
                return []
            if isinstance(value, list):
                return value  # 已经是列表
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else []
                except (json.JSONDecodeError, ValueError):
                    return []
            return []

        # 🔧 [修复] 解析AI反馈获取题目内容和解析
        ai_feedback = getattr(mistake, "ai_feedback", None)
        ai_feedback_dict = {}
        ai_full_answer = None  # 完整的AI回答文本（来自answers表）

        if ai_feedback:
            if isinstance(ai_feedback, dict):
                ai_feedback_dict = ai_feedback
            elif isinstance(ai_feedback, str):
                try:
                    parsed = json.loads(ai_feedback)
                    ai_feedback_dict = parsed if isinstance(parsed, dict) else {}
                except (json.JSONDecodeError, ValueError):
                    pass

        # 🆕 [方案A优化] 如果来自learning模块，尝试从answers表获取完整AI回答
        source = extract_orm_str(mistake, "source")
        source_question_id = extract_orm_str(mistake, "source_question_id")

        if source == "learning" and source_question_id:
            try:
                from sqlalchemy import select

                from src.models.learning import Answer

                # 查询answers表获取AI的完整回答
                stmt = select(Answer.content).where(
                    Answer.question_id == source_question_id
                )
                result = await self.db.execute(stmt)
                answer_row = result.scalar_one_or_none()

                if answer_row:
                    ai_full_answer = answer_row
                    logger.info(
                        f"从answers表获取到完整AI回答，长度: {len(ai_full_answer)} 字符"
                    )
            except Exception as e:
                logger.warning(f"获取answers表数据失败: {e}")
                # 降级处理，继续使用ai_feedback

        # 提取题目内容(优先OCR,其次AI分析)
        question_content = extract_orm_str(mistake, "ocr_text") or ""
        if not question_content and ai_feedback_dict:
            question_content = (
                ai_feedback_dict.get("question", "")
                or ai_feedback_dict.get("content", "")
                or ai_feedback_dict.get("题目", "")
            )

        # 提取解析/答案说明（优先使用完整AI回答）
        explanation = ai_full_answer if ai_full_answer else None

        if not explanation and ai_feedback_dict:
            explanation = (
                ai_feedback_dict.get("analysis", "")
                or ai_feedback_dict.get("explanation", "")
                or ai_feedback_dict.get("解析", "")
                or ai_feedback_dict.get("feedback", "")
            )

        # 提取正确答案(优先数据库,其次AI反馈)
        correct_answer = extract_orm_str(mistake, "correct_answer")
        if not correct_answer and ai_feedback_dict:
            # 尝试从多个可能的字段提取答案
            correct_answer = (
                ai_feedback_dict.get("correct_answer", "")
                or ai_feedback_dict.get("answer", "")
                or ai_feedback_dict.get("正确答案", "")
                or ai_feedback_dict.get("参考答案", "")
                or ai_feedback_dict.get("标准答案", "")
                or ai_feedback_dict.get("solution", "")
                or ai_feedback_dict.get("解答", "")
            )

        # 🔧 [方案A] 智能答案提取与验证
        if correct_answer:
            correct_answer = correct_answer.strip()

            # 检查是否为无效占位符
            is_invalid = (
                not correct_answer  # 空字符串
                or correct_answer
                in ["**", "*", "小**", "***", "？", "?", "-", "--"]  # 无意义符号
                or (
                    len(correct_answer) <= 3
                    and all(c in "*_-?？" for c in correct_answer)
                )  # 纯符号
            )

            if is_invalid and (explanation or ai_full_answer):
                # 🆕 优先从完整AI回答中提取答案
                text_to_extract = ai_full_answer if ai_full_answer else explanation

                # 尝试从文本中提取答案(使用正则匹配)
                if text_to_extract:
                    # 🔍 先检测是否为多小题题目
                    multi_answer_pattern = r"✅\s*\*\*答案[：:]\s*"
                    multi_answer_matches = re.findall(
                        multi_answer_pattern, text_to_extract, re.MULTILINE
                    )

                    # 如果有多个答案标记（≥2个），说明是多小题，不提取单个答案
                    if len(multi_answer_matches) >= 2:
                        correct_answer = "📖 本题包含多个小题，答案请参考解析"
                        is_invalid = False
                    else:
                        # 单小题，尝试提取答案
                        patterns = [
                            r"✅\s*\*\*答案[：:]\s*(.+?)\*\*",  # Markdown格式
                            r"✅\s*答案[：:]\s*(.+?)(?:\n|$)",  # 带勾格式
                            r"正确答案[：:是为]\s*[：:]?\s*(.+?)(?:[。\n；;]|$)",
                            r"标准答案[：:是为]\s*[：:]?\s*(.+?)(?:[。\n；;]|$)",
                            r"参考答案[：:是为]\s*[：:]?\s*(.+?)(?:[。\n；;]|$)",
                            r"答案[：:是为]\s*[：:]?\s*(.+?)(?:[。\n；;]|$)",
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, text_to_extract, re.MULTILINE)
                            if matches:
                                # 取第一个匹配
                                extracted = matches[0].strip()
                                if extracted and len(extracted) > 0:
                                    correct_answer = extracted
                                    is_invalid = False
                                    break

            # 如果仍然无效,根据题目类型决定提示文本
            if is_invalid:
                if ai_feedback_dict:
                    category = ai_feedback_dict.get("category", "")
                    # 对于空题目或主观题,给出友好提示
                    if category == "empty_question":
                        correct_answer = "📝 此题目暂无答案记录,请查看题目图片自行理解"
                    elif category in ["subjective", "essay", "discussion"]:
                        correct_answer = (
                            "💡 本题为主观题,无固定答案,请参考解析理解答题思路"
                        )
                    else:
                        correct_answer = "⚠️ 答案识别失败,建议查看解析或咨询老师"
                else:
                    correct_answer = "⚠️ 答案识别失败,建议查看解析或咨询老师"

        # 【新增】查询知识点关联信息
        knowledge_point_associations = []
        try:
            from src.models.knowledge_graph import MistakeKnowledgePoint
            from src.models.study import KnowledgeMastery
            from src.repositories.base_repository import BaseRepository
            from src.repositories.knowledge_graph_repository import (
                MistakeKnowledgePointRepository,
            )

            mkp_repo = MistakeKnowledgePointRepository(MistakeKnowledgePoint, self.db)
            km_repo = BaseRepository(KnowledgeMastery, self.db)

            # 查询错题的知识点关联
            mistake_id = UUID(extract_orm_uuid_str(mistake, "id"))
            associations = await mkp_repo.find_by_mistake(mistake_id)

            # 构建知识点关联详情
            for assoc in associations:
                # 查询对应的知识点掌握度信息
                kp_id = UUID(str(getattr(assoc, "knowledge_point_id")))
                mastery = await km_repo.get_by_id(str(kp_id))

                knowledge_point_associations.append(
                    {
                        "association_id": str(getattr(assoc, "id")),
                        "knowledge_point_id": str(kp_id),
                        "knowledge_point_name": (
                            getattr(mastery, "knowledge_point", "未知知识点")
                            if mastery
                            else "未知知识点"
                        ),
                        "relevance_score": float(
                            str(getattr(assoc, "relevance_score", 0.0))
                        ),
                        "is_primary": getattr(assoc, "is_primary", False),
                        "error_type": getattr(assoc, "error_type", ""),
                        "error_reason": getattr(assoc, "error_reason"),
                        "mastery_level": (
                            float(str(getattr(mastery, "mastery_level", 0.0)))
                            if mastery
                            else 0.0
                        ),
                        "mastered": getattr(assoc, "mastered_after_review", False),
                        "review_count": getattr(assoc, "review_count", 0),
                        "last_review_result": getattr(assoc, "last_review_result"),
                    }
                )

            logger.debug(
                f"为错题 {mistake_id} 附加了 {len(knowledge_point_associations)} 个知识点关联"
            )
        except Exception as e:
            # 知识点关联查询失败不影响错题详情返回
            logger.warning(f"查询知识点关联失败: {e}")

        # �🛠️ 使用extract_orm_*函数提取ORM对象的值
        return MistakeDetailResponse(
            id=UUID(extract_orm_uuid_str(mistake, "id")),
            title=extract_orm_str(mistake, "title") or "未命名错题",
            description=None,
            subject=extract_orm_str(mistake, "subject"),
            difficulty_level=extract_orm_int(mistake, "difficulty_level"),
            source=extract_orm_str(mistake, "source"),
            source_id=None,
            question_content=question_content or "暂无题目内容",
            student_answer=extract_orm_str(mistake, "student_answer") or None,
            correct_answer=correct_answer or None,
            explanation=explanation,  # 🔧 从AI反馈提取
            knowledge_points=parse_json_field(
                getattr(mistake, "knowledge_points", None)
            ),
            mastery_status=extract_orm_str(mistake, "mastery_status"),
            correct_count=extract_orm_int(mistake, "correct_count") or 0,
            total_reviews=extract_orm_int(mistake, "review_count") or 0,
            next_review_date=to_iso_string(getattr(mistake, "next_review_at", None)),
            created_at=to_iso_string(getattr(mistake, "created_at", None)) or "",
            updated_at=to_iso_string(getattr(mistake, "updated_at", None)) or "",
            image_urls=parse_json_field(getattr(mistake, "image_urls", None)),
            knowledge_point_associations=knowledge_point_associations,  # 🔧 新增字段
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
            filters: 筛选条件（subject, mastery_status, knowledge_point等）

        Returns:
            错题列表响应
        """
        subject = filters.get("subject") if filters else None
        mastery_status = filters.get("mastery_status") if filters else None
        knowledge_point = filters.get("knowledge_point") if filters else None
        knowledge_point_id = filters.get("knowledge_point_id") if filters else None
        category = filters.get("category") if filters else None
        source = filters.get("source") if filters else None

        # 【新增】如果指定了 knowledge_point（名称），先查询对应的 knowledge_point_id
        if knowledge_point and not knowledge_point_id:
            try:
                from sqlalchemy import and_, select

                from src.models.study import KnowledgeMastery

                # 查询该用户该学科该知识点的掌握度记录
                stmt = select(KnowledgeMastery.id).where(
                    and_(
                        KnowledgeMastery.user_id == str(user_id),
                        KnowledgeMastery.knowledge_point == knowledge_point,
                    )
                )
                if subject:
                    stmt = stmt.where(KnowledgeMastery.subject == subject)

                result = await self.db.execute(stmt)
                kp_id = result.scalar_one_or_none()

                if kp_id:
                    knowledge_point_id = str(kp_id)
                else:
                    # 如果找不到该知识点，返回空列表
                    logger.info(
                        f"用户 {user_id} 在学科 {subject} 中未找到知识点 {knowledge_point}"
                    )
                    return MistakeListResponse(
                        items=[], total=0, page=page, page_size=page_size
                    )
            except Exception as e:
                logger.warning(f"查询知识点ID失败: {e}，降级到普通查询")
                knowledge_point_id = None

        # 【新增】如果指定了 knowledge_point_id，使用新的查询方法
        if knowledge_point_id:
            try:
                items, total = await self.mistake_repo.find_by_knowledge_point_id(
                    user_id=user_id,
                    knowledge_point_id=UUID(knowledge_point_id),
                    subject=subject,
                    mastery_status=mastery_status,
                    page=page,
                    page_size=page_size,
                )
            except Exception as e:
                logger.warning(f"按知识点筛选失败: {e}，降级到普通查询")
                # 降级处理：如果知识点筛选失败，使用普通查询
                items, total = await self.mistake_repo.find_by_user(
                    user_id=user_id,
                    subject=subject,
                    mastery_status=mastery_status,
                    category=category,
                    source=source,
                    page=page,
                    page_size=page_size,
                )
        else:
            # 普通查询
            items, total = await self.mistake_repo.find_by_user(
                user_id=user_id,
                subject=subject,
                mastery_status=mastery_status,
                category=category,
                source=source,
                page=page,
                page_size=page_size,
            )

        # 🎯 异步转换列表项（包含知识点关联查询）
        list_items = []
        for item in items:
            list_item = await self._to_list_item(item)
            list_items.append(list_item)

        return MistakeListResponse(
            items=list_items,
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

        return await self._to_detail_response(mistake)

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
            "user_id": (
                str(user_id) if is_sqlite else user_id
            ),  # SQLite使用字符串，PostgreSQL使用UUID
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

        # 【新增】自动关联知识点
        try:
            from src.services.knowledge_graph_service import KnowledgeGraphService

            kg_service = KnowledgeGraphService(self.db, self.bailian_service)

            # 构建 AI 反馈（用于知识点提取）
            ai_feedback = {
                "knowledge_points": request.knowledge_points or [],
                "question": request.question_content,
                "explanation": request.explanation,
            }

            # 调用知识图谱服务分析并关联知识点
            await kg_service.analyze_and_associate_knowledge_points(
                mistake_id=UUID(str(getattr(mistake, "id"))),
                user_id=user_id,
                subject=request.subject,
                ocr_text=request.question_content,
                ai_feedback=(
                    ai_feedback if ai_feedback.get("knowledge_points") else None
                ),
            )

            logger.info(f"已为错题 {mistake.id} 自动关联知识点")
        except Exception as e:
            # 知识点关联失败不影响错题创建
            logger.warning(f"知识点自动关联失败: {e}")

        return await self._to_detail_response(mistake)

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

        return await self._to_detail_response(mistake)

    async def delete_mistake(self, mistake_id: UUID, user_id: UUID) -> None:
        """
        删除错题（级联删除关联数据）

        Args:
            mistake_id: 错题ID
            user_id: 用户ID
        """
        from sqlalchemy import delete, select, text

        mistake = await self.mistake_repo.get_by_id(str(mistake_id))

        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        # 🔧 Phase 8.3: 删除前记录受影响的学科
        affected_subjects = set()

        try:
            # 查询该错题关联的知识点，提取学科信息
            from src.models.knowledge_graph import MistakeKnowledgePoint
            from src.models.study import KnowledgeMastery

            stmt = (
                select(KnowledgeMastery.subject)
                .join(
                    MistakeKnowledgePoint,
                    MistakeKnowledgePoint.knowledge_point_id == KnowledgeMastery.id,
                )
                .where(MistakeKnowledgePoint.mistake_id == str(mistake_id))
                .distinct()
            )

            result = await self.db.execute(stmt)
            subjects = result.scalars().all()
            affected_subjects = set(str(s) for s in subjects if s)

            if affected_subjects:
                logger.info(f"错题 {mistake_id} 影响的学科: {affected_subjects}")
        except Exception as e:
            logger.warning(f"查询受影响学科失败: {e}，继续执行删除")

        # 🔧 级联删除：先删除关联数据，再删除错题
        mistake_id_str = str(mistake_id)

        # ✅ 方案A：使用实时计算，无需维护 mistake_count 字段
        # 删除关联记录即可，前端查询时会实时统计

        # 1. 删除复习记录 (mistake_review_sessions)
        await self.db.execute(
            text("DELETE FROM mistake_review_sessions WHERE mistake_id = :mid"),
            {"mid": mistake_id_str},
        )

        # 2. 删除知识点关联 (mistake_knowledge_points)
        await self.db.execute(
            text("DELETE FROM mistake_knowledge_points WHERE mistake_id = :mid"),
            {"mid": mistake_id_str},
        )

        # 3. 删除错题记录
        await self.mistake_repo.delete(mistake_id_str)

        # 提交删除操作
        await self.db.commit()

        logger.info(f"Deleted mistake {mistake_id} with all associations")

        # 🔧 Phase 8.3: 删除后异步触发快照更新
        if affected_subjects:
            try:
                from src.services.knowledge_graph_service import KnowledgeGraphService

                kg_service = KnowledgeGraphService(self.db, self.bailian_service)

                for subject in affected_subjects:
                    try:
                        await kg_service.create_knowledge_graph_snapshot(
                            user_id=user_id, subject=subject, period_type="auto_update"
                        )
                        logger.info(
                            f"✅ 已更新知识图谱快照: user={user_id}, subject={subject}"
                        )
                    except Exception as e:
                        # 单个学科快照更新失败不影响其他学科
                        logger.warning(
                            f"⚠️ 更新学科 {subject} 快照失败: {e}，继续处理其他学科"
                        )

                # 提交快照更新
                await self.db.commit()

            except Exception as e:
                # 快照更新失败不回滚删除操作
                logger.warning(
                    f"⚠️ 知识图谱快照更新失败: {e}，但错题已成功删除", exc_info=True
                )
                # 不抛出异常，确保删除操作成功

    async def get_today_review_tasks(self, user_id: UUID) -> TodayReviewResponse:
        """
        获取今日复习任务

        Args:
            user_id: 用户ID

        Returns:
            今日复习任务响应
        """
        mistakes = await self.mistake_repo.find_due_for_review(
            user_id=user_id, limit=50
        )

        tasks = []
        total_minutes = 0

        from src.utils.type_converters import (
            extract_orm_int,
            extract_orm_str,
            extract_orm_uuid_str,
        )

        for mistake in mistakes:
            # 🛠️ 安全地提取ORM属性
            mistake_id_str = extract_orm_uuid_str(mistake, "id")
            next_review = getattr(mistake, "next_review_at", None)

            tasks.append(
                TodayReviewTask(
                    id=UUID(mistake_id_str),
                    mistake_id=UUID(mistake_id_str),
                    title=extract_orm_str(mistake, "title") or "未命名错题",
                    subject=extract_orm_str(mistake, "subject"),
                    review_round=(extract_orm_int(mistake, "review_count") or 0) + 1,
                    due_date=(
                        next_review.isoformat()
                        if next_review and hasattr(next_review, "isoformat")
                        else datetime.now().isoformat()
                    ),
                    question_content=extract_orm_str(mistake, "ocr_text") or "",
                    image_urls=getattr(mistake, "image_urls", None) or [],
                )
            )
            estimated_time = extract_orm_int(mistake, "estimated_time")
            total_minutes += estimated_time if estimated_time else 5

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
        from src.utils.type_converters import extract_orm_int

        next_review, interval = self.algorithm.calculate_next_review(
            review_count=extract_orm_int(mistake, "review_count")
            or 0,  # 🛠️ 使用extract_orm_int
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

        from src.utils.type_converters import extract_orm_uuid_str

        # 7. 更新错题状态
        update_data = {
            "review_count": mistake.review_count + 1,
            "last_review_at": datetime.now(),
            "next_review_at": next_review,
        }

        if request.review_result == "correct":
            update_data["correct_count"] = mistake.correct_count + 1

        # 8. 判断是否已掌握
        consecutive_correct = update_data.get("correct_count", mistake.correct_count)
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

        # 【新增】更新知识点掌握度
        try:
            from src.services.knowledge_graph_service import KnowledgeGraphService

            kg_service = KnowledgeGraphService(self.db, self.bailian_service)

            # 调用知识图谱服务更新掌握度
            await kg_service.update_knowledge_mastery_after_review(
                mistake_id=mistake_id,
                review_result=request.review_result,
                confidence_level=request.confidence_level,
            )

            logger.info(f"已更新错题 {mistake_id} 关联的知识点掌握度")
        except Exception as e:
            # 知识点掌握度更新失败不影响复习流程
            logger.warning(f"知识点掌握度更新失败: {e}")

        logger.info(
            f"Completed review for mistake {mistake_id}, mastery: {current_mastery}, next review: {next_review}"
        )

        return ReviewCompleteResponse(
            review_id=UUID(extract_orm_uuid_str(review, "id")),
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
        from src.utils.type_converters import (
            extract_orm_float,
            extract_orm_int,
            extract_orm_str,
            extract_orm_uuid_str,
            extract_orm_value,
        )

        items = [
            ReviewHistoryItem(
                id=UUID(extract_orm_uuid_str(r, "id")),
                review_date=extract_orm_value(r, "review_date", datetime.now()),
                review_result=extract_orm_str(r, "review_result"),
                mastery_level=extract_orm_float(r, "mastery_level") or 0.0,
                time_spent=extract_orm_int(r, "time_spent"),
                confidence_level=extract_orm_int(r, "confidence_level") or 0,
                notes=extract_orm_str(r, "notes"),
            )
            for r in reviews
        ]

        latest_mastery_value = (
            extract_orm_float(reviews[0], "mastery_level") or 0.0 if reviews else 0.0
        )

        return ReviewHistoryResponse(
            items=items,
            total=len(reviews),
            average_mastery=avg_mastery,
            latest_mastery=latest_mastery_value,
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

        from src.utils.type_converters import extract_orm_float, extract_orm_value

        daily_stats = defaultdict(lambda: {"sum": 0.0, "count": 0})

        for review in reviews:
            review_date = extract_orm_value(review, "review_date", datetime.now())
            date_str = review_date.date().isoformat()
            mastery_level = extract_orm_float(review, "mastery_level") or 0.0
            daily_stats[date_str]["sum"] += mastery_level
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
                    review_count=int(stats["count"]),
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

    async def analyze_mistake_with_ai(self, mistake_id: UUID, user_id: UUID) -> Dict:
        """
        使用AI分析错题（带学情上下文）

        Args:
            mistake_id: 错题ID
            user_id: 用户ID

        Returns:
            AI分析结果，包含：
            - knowledge_points: 知识点列表
            - error_reasons: 错误原因分析
            - suggestions: 学习建议
        """
        mistake = await self.mistake_repo.get_by_id(str(mistake_id))
        if not mistake or str(mistake.user_id) != str(user_id):
            raise NotFoundError(f"错题 {mistake_id} 不存在")

        if not self.bailian_service:
            raise ServiceError("AI服务未配置")

        try:
            from src.utils.type_converters import extract_orm_int, extract_orm_str

            # 初始化变量，避免在异常处理中未绑定
            ai_content = ""

            # 安全提取ORM属性
            subject = extract_orm_str(mistake, "subject") or "未知"
            difficulty = extract_orm_int(mistake, "difficulty_level")
            difficulty_text = str(difficulty) if difficulty else "未知"
            ocr_text = extract_orm_str(mistake, "ocr_text") or "无题目内容"

            # 【新增】构建学情上下文
            learning_context = await self._build_learning_context_for_ai(
                user_id, subject
            )

            # 构造分析提示词（加入学情上下文）
            analysis_prompt = f"""请分析以下错题，结合学生的学情数据，提取关键信息并给出个性化学习建议。

{learning_context}

【题目信息】
学科：{subject}
难度：{difficulty_text}
题目内容：
{ocr_text}

【任务要求】
请以JSON格式返回分析结果，包含以下字段：
1. knowledge_points: 知识点列表（数组，3-5个核心知识点，每个知识点需包含:
   - name: 知识点名称
   - relevance: 相关性 (0.0-1.0)
   - error_type: 错误类型 (concept_misunderstanding/calculation_error/formula_misuse/logic_error/knowledge_gap/method_confusion/other)
   - error_reason: 错误原因（简洁描述）
   - suggestions: 改进建议（数组，2-3条具体建议）
)
2. error_reason: 本次错题的主要错误原因分析（字符串，100字以内）
3. suggestions: 学习建议（字符串，150字以内，结合学生薄弱知识点给出针对性建议）
4. personalized_insight: 个性化洞察（字符串，基于学生历史学情的特别提示，如果是初次使用可省略）

示例格式：
{{
    "knowledge_points": [
        {{
            "name": "一元二次方程",
            "relevance": 0.9,
            "error_type": "concept_misunderstanding",
            "error_reason": "对判别式的计算理解有误",
            "suggestions": ["复习判别式b²-4ac的定义", "做5道判别式专项练习"]
        }},
        {{
            "name": "配方法",
            "relevance": 0.7,
            "error_type": "method_confusion",
            "error_reason": "配方步骤出现错误",
            "suggestions": ["重新学习配方法步骤", "对比配方法与公式法的区别"]
        }}
    ],
    "error_reason": "对判别式的计算理解有误，导致解题思路错误。",
    "suggestions": "建议复习判别式的定义和应用，多做相关练习题，重点掌握b²-4ac的计算方法。结合你在'一元二次方程'上的薄弱情况，建议从基础例题入手，逐步提升难度。",
    "personalized_insight": "你在一元二次方程相关题目上已经出现3次错误，这是需要重点突破的知识点。"
}}

请严格按照JSON格式返回，不要包含其他内容。"""

            # 调用百炼AI服务
            logger.info(f"开始AI分析错题（带学情上下文）: {mistake_id}")

            messages = [
                {
                    "role": "system",
                    "content": "你是一位经验丰富的学科教师，擅长分析学生的错题，找出知识盲点并给出针对性建议。你会根据学生的历史学情数据，提供个性化的学习指导。",
                },
                {"role": "user", "content": analysis_prompt},
            ]

            response = await self.bailian_service.chat_completion(
                messages=messages,
                stream=False,
                temperature=0.7,  # 适中的创造性
                max_tokens=1500,  # 增加token以支持更详细的分析
            )

            if not response.success:
                logger.error(f"AI分析失败: {response.error_message}")
                # 降级方案：返回基础信息
                return self._fallback_analysis(mistake)

            # 解析AI返回的JSON
            ai_content = response.content.strip() if response.content else ""

            # 尝试提取JSON（处理AI可能返回的额外文本）
            json_match = re.search(r"\{.*\}", ai_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis_result = json.loads(json_str)
            else:
                # 如果无法提取JSON，尝试直接解析
                analysis_result = json.loads(ai_content)

            # 【新增】标准化知识点格式
            knowledge_points = self._standardize_knowledge_points(
                analysis_result.get("knowledge_points", [])
            )

            # 验证和标准化返回结果
            result = {
                "knowledge_points": knowledge_points,
                "error_reason": analysis_result.get("error_reason", ""),
                "suggestions": analysis_result.get("suggestions", ""),
                "personalized_insight": analysis_result.get("personalized_insight", ""),
                "ai_tokens_used": response.tokens_used,
                "analysis_time": response.processing_time,
                "has_learning_context": bool(
                    learning_context and "初次使用系统" not in learning_context
                ),
            }

            # 更新错题记录中的AI分析结果（可选）
            update_data = {}
            if result["knowledge_points"]:
                # 只存储知识点名称列表（向后兼容）
                update_data["knowledge_points"] = [
                    kp.get("name", kp) if isinstance(kp, dict) else kp
                    for kp in knowledge_points
                ]

            if update_data:
                await self.mistake_repo.update(str(mistake_id), update_data)
            else:
                await self.db.commit()

            logger.info(
                f"AI分析完成: {mistake_id}, "
                f"知识点数量: {len(result['knowledge_points'])}, "
                f"Token使用: {response.tokens_used}, "
                f"学情上下文: {result['has_learning_context']}"
            )

            return result

        except json.JSONDecodeError as e:
            content_preview = ai_content[:200] if ai_content else "无AI响应内容"  # type: ignore[possibly-unbound]
            logger.error(f"AI返回的JSON解析失败: {e}, 原始内容: {content_preview}")
            # 降级方案
            return self._fallback_analysis(mistake)

        except Exception as e:
            logger.error(f"AI分析错题失败: {e}", exc_info=True)
            # 降级方案：返回基础信息
            return self._fallback_analysis(mistake)

    async def _build_learning_context_for_ai(self, user_id: UUID, subject: str) -> str:
        """
        构建学情上下文（供AI分析使用）

        Args:
            user_id: 用户ID
            subject: 学科

        Returns:
            学情上下文文本
        """
        try:
            from src.services.knowledge_graph_service import KnowledgeGraphService

            kg_service = KnowledgeGraphService(self.db, self.bailian_service)
            learning_context = await kg_service.build_learning_context(user_id, subject)

            return learning_context

        except Exception as e:
            logger.warning(f"构建学情上下文失败: {e}")
            return "学生是初次使用系统，尚无历史学情数据。"

    def _standardize_knowledge_points(self, knowledge_points: List) -> List[Dict]:
        """
        标准化知识点格式

        将AI返回的知识点列表转换为统一的字典格式

        Args:
            knowledge_points: AI返回的知识点列表

        Returns:
            标准化的知识点列表
        """
        standardized = []

        for kp in knowledge_points:
            # 如果是字符串，转换为字典
            if isinstance(kp, str):
                standardized.append(
                    {
                        "name": kp,
                        "relevance": 0.8,
                        "error_type": "other",
                        "error_reason": "",
                        "suggestions": [],
                    }
                )
            elif isinstance(kp, dict):
                # 确保必要字段存在
                standardized.append(
                    {
                        "name": kp.get("name", kp.get("knowledge_point", "未知知识点")),
                        "relevance": kp.get("relevance", 0.8),
                        "error_type": kp.get("error_type", "other"),
                        "error_reason": kp.get("error_reason", ""),
                        "suggestions": kp.get("suggestions", []),
                    }
                )
            else:
                logger.warning(f"未知的知识点格式: {type(kp)}")

        return standardized

    def _fallback_analysis(self, mistake) -> Dict:
        """
        AI分析失败时的降级方案

        Args:
            mistake: 错题记录

        Returns:
            基础分析结果
        """
        logger.warning(f"使用降级分析方案: {mistake.id}")

        # 根据学科提供默认的学习建议
        subject_suggestions = {
            "math": "建议回顾相关章节的基础概念，多做类似题目练习，注意解题步骤的规范性。",
            "chinese": "建议加强基础知识的积累，多阅读优秀范文，注意答题技巧和表达规范。",
            "english": "建议复习相关语法点，积累词汇，多做阅读和写作练习。",
            "physics": "建议理解物理概念的本质，掌握公式的推导过程，多做实验分析题。",
            "chemistry": "建议熟记化学方程式，理解反应原理，注意实验操作的细节。",
            "biology": "建议系统复习相关知识点，理解生物过程，注意图表分析能力的培养。",
        }

        return {
            "knowledge_points": mistake.knowledge_points or [],
            "error_reason": "建议仔细分析题目要求，对比正确答案找出差异。",
            "suggestions": subject_suggestions.get(
                mistake.subject, "建议回顾课本知识，多做练习，及时请教老师或同学。"
            ),
            "ai_tokens_used": 0,
            "analysis_time": 0.0,
            "is_fallback": True,
        }
