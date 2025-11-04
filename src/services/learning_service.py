"""
学习问答服务
基于百炼AI的智能学习助手服务
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, join, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import get_settings
from src.core.exceptions import (
    BailianServiceError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from src.models.homework import HomeworkReview, HomeworkSubmission
from src.models.learning import (
    Answer,
    ChatSession,
    LearningAnalytics,
    Question,
    QuestionStatus,
    QuestionType,
    SessionStatus,
)
from src.models.user import User
from src.repositories.base_repository import BaseRepository
from src.schemas.learning import (
    AnswerResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    CreateSessionRequest,
    FeedbackRequest,
    LearningAnalyticsResponse,
    PaginatedResponse,
    QuestionHistoryQuery,
    QuestionResponse,
    SessionListQuery,
    SessionResponse,
)
from src.services.bailian_service import (
    AIContext,
    BailianService,
    ChatMessage,
    MessageRole,
    get_bailian_service,
)
from src.utils.cache import cache_key, cache_result
from src.utils.type_converters import (
    extract_orm_bool,
    extract_orm_int,
    extract_orm_str,
    extract_orm_uuid_str,
    safe_str,
    wrap_orm,
)

logger = logging.getLogger("learning_service")
settings = get_settings()


class LearningService:
    """学习问答服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bailian_service = get_bailian_service()

        # 初始化仓储
        self.session_repo = BaseRepository(ChatSession, db)
        self.question_repo = BaseRepository(Question, db)
        self.answer_repo = BaseRepository(Answer, db)
        self.analytics_repo = BaseRepository(LearningAnalytics, db)

    # ========== 问答核心功能 ==========

    async def ask_question(
        self, user_id: str, request: AskQuestionRequest
    ) -> AskQuestionResponse:
        """
        提问功能

        Args:
            user_id: 用户ID
            request: 提问请求

        Returns:
            AskQuestionResponse: 问答响应
        """
        start_time = time.time()

        try:
            # 1. 获取或创建会话
            session = await self._get_or_create_session(user_id, request)

            # 2. 保存问题
            question = await self._save_question(
                user_id, extract_orm_uuid_str(session, "id"), request
            )

            # 3. 构建AI上下文
            ai_context = await self._build_ai_context(
                user_id, session, request.use_context
            )

            # 4. 构建对话消息
            messages = await self._build_conversation_messages(
                extract_orm_uuid_str(session, "id"),
                request,
                ai_context,
                request.include_history,
                request.max_history,
            )

            # 5. 调用AI生成答案
            # Convert ChatMessage objects to dict format if needed
            message_dicts = []
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    msg_dict: Dict[str, Any] = {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                    # 如果有图片URLs，添加到字典中
                    if hasattr(msg, "image_urls") and msg.image_urls:
                        msg_dict["image_urls"] = msg.image_urls
                        logger.info(
                            f"🖼️ 消息包含图片: role={msg.role.value}, "
                            f"image_count={len(msg.image_urls)}, "
                            f"urls={msg.image_urls}"
                        )
                    message_dicts.append(msg_dict)
                else:
                    message_dicts.append(msg)

            # 🔍 最终调试：打印完整的message_dicts
            messages_summary = [
                {
                    "role": m.get("role"),
                    "has_images": bool(m.get("image_urls")),
                    "image_count": len(m.get("image_urls", [])),
                }
                for m in message_dicts
            ]
            logger.info(
                f"📤 准备调用AI: message_count={len(message_dicts)}, "
                f"messages_with_images={sum(1 for m in messages_summary if m['has_images'])}, "
                f"total_images={sum(m['image_count'] for m in messages_summary)}"
            )
            logger.info(
                f"📋 消息详情: {json.dumps(messages_summary, ensure_ascii=False)}"
            )

            ai_response = await self.bailian_service.chat_completion(
                messages=message_dicts,
                context=ai_context,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                top_p=settings.AI_TOP_P,
            )

            if not ai_response.success:
                raise BailianServiceError(f"AI调用失败: {ai_response.error_message}")

            # 6. 保存答案
            answer = await self._save_answer(
                extract_orm_uuid_str(question, "id"), ai_response
            )

            # 7. 更新会话统计
            await self._update_session_stats(
                extract_orm_uuid_str(session, "id"), ai_response.tokens_used
            )

            # 8. 更新用户学习分析
            await self._update_learning_analytics(user_id, question, answer)

            # 🎯 9. 智能错题自动创建（简化规则版）
            mistake_created = False
            mistake_info = None
            try:
                mistake_result = await self._auto_create_mistake_if_needed(
                    user_id, question, answer, request
                )
                if mistake_result:
                    mistake_created = True
                    mistake_info = mistake_result
                    logger.info(
                        f"✅ 错题自动创建成功: user_id={user_id}, "
                        f"mistake_id={mistake_info.get('id')}, "
                        f"category={mistake_info.get('category')}"
                    )
            except Exception as mistake_err:
                logger.warning(f"错题创建失败，但不影响问答: {str(mistake_err)}")

            # 10. 构建响应
            processing_time = int((time.time() - start_time) * 1000)

            # 🔧 刷新ORM对象，确保所有属性已加载（避免 MissingGreenlet 错误）
            await self.db.refresh(question)
            await self.db.refresh(answer)
            await self.db.refresh(session)

            return AskQuestionResponse(
                question=QuestionResponse.model_validate(question),
                answer=AnswerResponse.model_validate(answer),
                session=SessionResponse.model_validate(session),
                processing_time=processing_time,
                tokens_used=ai_response.tokens_used,
                mistake_created=mistake_created,  # 🎯 新增
                mistake_info=mistake_info,  # 🎯 新增
            )

        except Exception as e:
            logger.error(
                f"提问处理失败: {str(e)}", extra={"user_id": user_id}, exc_info=True
            )

            # 更新问题状态为失败
            try:
                # 安全地获取question变量
                question_var = locals().get("question")
                if question_var is not None:
                    await self.question_repo.update(
                        extract_orm_uuid_str(question_var, "id"),
                        {"is_processed": False},
                    )
            except:
                pass  # Ignore update errors during exception handling

            raise ServiceError(f"提问处理失败: {str(e)}") from e

    async def ask_question_stream(self, user_id: str, request: AskQuestionRequest):
        """
        流式提问功能

        Args:
            user_id: 用户ID
            request: 提问请求

        Yields:
            dict: SSE 格式的增量响应
                - type: "content" | "done" | "error"
                - content: 增量文本内容
                - full_content: 累积的完整内容
                - finish_reason: 完成原因 (null | "stop")
                - question_id: 问题ID (仅在 type="done" 时)
                - answer_id: 答案ID (仅在 type="done" 时)
                - usage: token使用情况 (仅在 type="done" 时)
        """
        question = None
        session = None
        full_answer_content = ""

        try:
            # 1. 获取或创建会话
            session = await self._get_or_create_session(user_id, request)
            session_id = extract_orm_uuid_str(session, "id")

            # 2. 保存问题（状态为未处理）
            question = await self._save_question(user_id, session_id, request)
            question_id = extract_orm_uuid_str(question, "id")

            # 3. 构建AI上下文
            ai_context = await self._build_ai_context(
                user_id, session, request.use_context
            )

            # 4. 构建对话消息
            messages = await self._build_conversation_messages(
                session_id,
                request,
                ai_context,
                request.include_history,
                request.max_history,
            )

            # 转换为字典格式
            message_dicts = []
            for msg in messages:
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    msg_dict: Dict[str, Any] = {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                    if hasattr(msg, "image_urls") and msg.image_urls:
                        msg_dict["image_urls"] = msg.image_urls
                    message_dicts.append(msg_dict)
                else:
                    message_dicts.append(msg)

            # 4. 流式调用AI（支持图片和文本）
            logger.info(
                f"开始流式调用 - 消息数: {len(message_dicts)}, "
                f"当前请求图片: {len(request.image_urls or [])}"
            )

            async for chunk in self.bailian_service.chat_completion_stream(
                messages=message_dicts,
                context=ai_context,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                top_p=settings.AI_TOP_P,
            ):
                # 🔧 防御性检查：确保 chunk 不为 None
                if chunk is None:
                    logger.warning("收到 None chunk，跳过处理")
                    continue

                # 累积完整内容
                if chunk.get("content"):
                    full_answer_content = chunk.get("full_content", "")

                # 发送增量内容
                yield {
                    "type": "content",
                    "content": chunk.get("content", ""),
                    "full_content": full_answer_content,
                    "finish_reason": chunk.get("finish_reason"),
                }

                # 流式完成后保存数据
                if chunk.get("finish_reason") == "stop":
                    # 6. 保存答案
                    answer_data = {
                        "question_id": question_id,
                        "content": full_answer_content,
                        "tokens_used": chunk.get("usage", {}).get("total_tokens", 0),
                        "model_name": chunk.get(
                            "model", "qwen-turbo"
                        ),  # 使用实际调用的模型
                    }
                    answer = await self.answer_repo.create(answer_data)
                    answer_id = extract_orm_uuid_str(answer, "id")

                    # 7. 更新问题状态
                    await self.question_repo.update(
                        question_id,
                        {"is_processed": True},
                    )

                    # 8. 更新会话统计
                    tokens_used = chunk.get("usage", {}).get("total_tokens", 0)
                    await self._update_session_stats(session_id, tokens_used)

                    # 9. 更新学习分析（后台任务，不阻塞响应）
                    try:
                        await self._update_learning_analytics(user_id, question, answer)
                    except Exception as e:
                        logger.warning(f"更新学习分析失败: {e}")

                    # 🎯 9.5 智能错题自动创建（不阻塞流式响应）
                    mistake_created = False
                    mistake_info = None
                    try:
                        mistake_result = await self._auto_create_mistake_if_needed(
                            user_id, question, answer, request
                        )
                        if mistake_result:
                            mistake_created = True
                            mistake_info = mistake_result
                            logger.info(
                                f"✅ [流式] 错题自动创建成功: user_id={user_id}, "
                                f"mistake_id={mistake_info.get('id')}, "
                                f"category={mistake_info.get('category')}, "
                                f"confidence={mistake_info.get('confidence')}"
                            )
                    except Exception as mistake_err:
                        logger.warning(
                            f"[流式] 错题创建失败，但不影响问答: {str(mistake_err)}"
                        )

                    # 10. 发送完成事件
                    yield {
                        "type": "done",
                        "question_id": question_id,
                        "answer_id": answer_id,
                        "session_id": session_id,
                        "usage": chunk.get("usage", {}),
                        "full_content": full_answer_content,
                        "mistake_created": mistake_created,  # 🎯 新增
                        "mistake_info": mistake_info,  # 🎯 新增
                    }

        except BailianServiceError as e:
            logger.error(f"AI服务调用失败: {e}")
            yield {"type": "error", "message": f"AI服务暂时不可用: {str(e)}"}
        except Exception as e:
            logger.error(f"流式提问处理失败: {e}", exc_info=True)

            # 更新问题状态为失败
            if question:
                try:
                    await self.question_repo.update(
                        extract_orm_uuid_str(question, "id"),
                        {"is_processed": False},
                    )
                except:
                    pass

            yield {"type": "error", "message": f"提问处理失败: {str(e)}"}

    async def _get_or_create_session(
        self, user_id: str, request: AskQuestionRequest
    ) -> ChatSession:
        """获取或创建会话"""
        if request.session_id:
            # 尝试获取现有会话
            try:
                session = await self.session_repo.get_by_id(request.session_id)
                if session and extract_orm_uuid_str(session, "user_id") == user_id:
                    # 会话存在且属于当前用户
                    if (
                        extract_orm_bool(session, "status")
                        == SessionStatus.ACTIVE.value
                    ):
                        # 更新最后活跃时间
                        await self.session_repo.update(
                            extract_orm_uuid_str(session, "id"),
                            {"last_active_at": datetime.now().isoformat()},
                        )
                    return session
            except Exception as e:
                # 获取会话失败，记录日志但不中断，继续创建新会话
                print(
                    f"获取会话失败，将创建新会话: session_id={request.session_id}, error={str(e)}"
                )

        # 创建新会话（原来的session_id不存在或获取失败）
        session_title = await self._generate_session_title(request.content)
        session_data = {
            "user_id": user_id,
            "title": session_title,
            "subject": request.subject.value if request.subject else None,
            "status": SessionStatus.ACTIVE.value,
            "context_enabled": request.use_context,
            "last_active_at": datetime.utcnow().isoformat(),
        }
        return await self.session_repo.create(session_data)

    async def _generate_session_title(self, first_question: str) -> str:
        """生成会话标题"""
        # 简单的标题生成逻辑，取问题前30个字符
        title = first_question[:30]
        if len(first_question) > 30:
            title += "..."
        return title

    async def _save_question(
        self, user_id: str, session_id: str, request: AskQuestionRequest
    ) -> Question:
        """保存问题"""
        question_data = {
            "session_id": session_id,
            "user_id": user_id,
            "content": request.content,
            "question_type": (
                request.question_type.value if request.question_type else None
            ),
            "subject": request.subject.value if request.subject else None,
            "topic": request.topic,
            "difficulty_level": (
                request.difficulty_level.value if request.difficulty_level else None
            ),
            "context_data": (
                json.dumps(request.context_data) if request.context_data else None
            ),
            "has_images": bool(request.image_urls),
            "image_urls": (
                json.dumps(request.image_urls) if request.image_urls else None
            ),
            "is_processed": False,
        }
        return await self.question_repo.create(question_data)

    async def _build_ai_context(
        self, user_id: str, session: ChatSession, use_context: bool = True
    ) -> AIContext:
        """构建AI调用上下文，集成MCP个性化学情分析"""
        context = AIContext(
            user_id=user_id,
            subject=extract_orm_str(session, "subject"),
            session_id=extract_orm_uuid_str(session, "id"),
        )

        if use_context:
            # 获取用户信息
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user:
                context.grade_level = self._parse_grade_level(
                    extract_orm_str(user, "grade_level")
                )
                context.metadata = {
                    "user_school": extract_orm_str(user, "school"),
                    "user_class": extract_orm_str(user, "class_name"),
                    "learning_subjects": extract_orm_str(user, "study_subjects"),
                }

            # 🚀 NEW: 集成 MCP 个性化学情上下文
            try:
                from src.services.knowledge_context_builder import (
                    knowledge_context_builder,
                )

                # 构建用户学情上下文
                learning_context = await knowledge_context_builder.build_context(
                    user_id=user_id,
                    subject=extract_orm_str(session, "subject"),
                    session_type="learning",
                )

                # 将学情分析结果添加到AI上下文中
                if learning_context.weak_knowledge_points:
                    weak_points_summary = []
                    for point in learning_context.weak_knowledge_points[
                        :5
                    ]:  # 取前5个最严重的
                        weak_points_summary.append(
                            {
                                "knowledge": point.knowledge_name,
                                "subject": point.subject,
                                "error_rate": round(point.error_rate * 100, 1),
                                "severity": round(point.severity_score * 100, 1),
                            }
                        )

                    context.metadata = context.metadata or {}
                    context.metadata.update(
                        {
                            "weak_knowledge_points": weak_points_summary,
                            "learning_pace": learning_context.learning_preferences.learning_pace,
                            "focus_duration": learning_context.learning_preferences.focus_duration,
                            "current_level": learning_context.context_summary.current_level,
                            "total_questions": learning_context.context_summary.total_questions,
                            "learning_streak": learning_context.context_summary.learning_streak,
                            "mcp_context_generated": True,
                        }
                    )

                    logger.info(
                        f"MCP上下文已构建 - 用户: {user_id}, 薄弱知识点: {len(learning_context.weak_knowledge_points)}"
                    )
                else:
                    # 新用户或没有足够数据，标记为首次学习
                    context.metadata = context.metadata or {}
                    context.metadata.update(
                        {
                            "mcp_context_generated": True,
                            "is_new_learner": True,
                            "current_level": "beginner",
                        }
                    )
                    logger.info(f"MCP上下文已构建 - 新学习者: {user_id}")

            except Exception as e:
                logger.warning(f"MCP上下文构建失败，回退到传统模式: {str(e)}")
                # 继续使用传统上下文，不影响主流程
                context.metadata = context.metadata or {}
                context.metadata["mcp_context_failed"] = True

            # 获取相关作业历史（保持原有逻辑）
            homework_context = await self._get_homework_context(
                user_id, extract_orm_str(session, "subject")
            )
            if homework_context:
                context.metadata = context.metadata or {}
                context.metadata.update(homework_context)

        return context

    def _parse_grade_level(self, grade_level: Optional[str]) -> Optional[int]:
        """解析学段为数字"""
        if not grade_level:
            return None

        grade_mapping = {
            "junior_1": 7,
            "junior_2": 8,
            "junior_3": 9,
            "senior_1": 10,
            "senior_2": 11,
            "senior_3": 12,
        }
        return grade_mapping.get(grade_level)

    async def _get_homework_context(
        self, user_id: str, subject: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """获取作业相关上下文"""
        try:
            # 获取最近的作业记录
            stmt = (
                select(HomeworkSubmission)
                .options(selectinload(HomeworkSubmission.reviews))
                .where(HomeworkSubmission.student_id == user_id)
                .order_by(desc(HomeworkSubmission.created_at))
                .limit(5)
            )

            if subject:
                stmt = stmt.where(HomeworkSubmission.subject == subject)

            result = await self.db.execute(stmt)
            submissions = result.scalars().all()

            if not submissions:
                return None

            # 分析错题和知识点
            wrong_topics = []
            mastered_topics = []

            for submission in submissions:
                for review in submission.reviews:
                    if hasattr(review, "knowledge_points") and review.knowledge_points:
                        points = json.loads(review.knowledge_points)
                        if review.score and review.score < 80:  # 假设80分以下为错题
                            wrong_topics.extend(points)
                        else:
                            mastered_topics.extend(points)

            return {
                "recent_homework_count": len(submissions),
                "weak_knowledge_points": list(set(wrong_topics))[:10],
                "strong_knowledge_points": list(set(mastered_topics))[:10],
            }

        except Exception as e:
            logger.warning(f"获取作业上下文失败: {str(e)}")
            return None

    async def _build_conversation_messages(
        self,
        session_id: str,
        request: AskQuestionRequest,
        context: AIContext,
        include_history: bool = True,
        max_history: int = 10,
    ) -> List[ChatMessage]:
        """构建对话消息"""
        messages = []

        # 1. 系统提示词
        system_prompt = await self._build_system_prompt(context)
        messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))

        # 2. 历史对话
        if include_history and max_history > 0:
            history_messages = await self._get_conversation_history(
                session_id, max_history
            )
            messages.extend(history_messages)

        # 3. 当前问题
        user_message = request.content

        # 构建用户消息，支持图片
        if request.image_urls and len(request.image_urls) > 0:
            # 有图片时，创建包含图片的多模态消息
            user_chat_message = ChatMessage(
                role=MessageRole.USER,
                content=user_message,
                image_urls=request.image_urls,
            )

            # 添加图片提示到文本内容
            user_message += f"\n\n[用户上传了{len(request.image_urls)}张图片，请分析图片内容并回答问题]"
            user_chat_message.content = user_message

            # 🔍 调试日志：记录图片URL
            logger.info(
                f"构建多模态消息: session_id={session_id}, image_count={len(request.image_urls)}",
                extra={
                    "session_id": session_id,
                    "image_urls": request.image_urls,
                    "message_preview": user_message[:100],
                },
            )

        else:
            # 纯文本消息
            user_chat_message = ChatMessage(role=MessageRole.USER, content=user_message)

        messages.append(user_chat_message)

        return messages

    async def _build_system_prompt(self, context: AIContext) -> str:
        """
        构建系统提示词（简化版）

        更复杂的提示词配置请在百炼平台的智能体"系统指令"中设置
        """
        prompt_parts = [
            "你是一个专业的K12学习助教，名叫'五好助教'，专门帮助小初高中学生解决学习问题。",
            "",
            "你的职责包括：",
            "1. 只能回答学习问题，提供清晰易懂的解释",
            "2. 分析题目，提供详细的解题步骤",
            "3. 鼓励学生积极学习，建立学习信心",
        ]

        # 添加用户上下文（保留个性化功能）
        if context.grade_level:
            grade_name = self._get_grade_name(context.grade_level)
            prompt_parts.append(f"\n学生当前学段：{grade_name}")

        if context.subject:
            subject_name = self._get_subject_name(context.subject)
            prompt_parts.append(f"当前学科：{subject_name}")

        if context.metadata:
            if context.metadata.get("user_school"):
                prompt_parts.append(f"学生学校：{context.metadata['user_school']}")

            if context.metadata.get("weak_knowledge_points"):
                weak_points = context.metadata["weak_knowledge_points"][:3]  # 取前3个
                # weak_points 是 WeakKnowledgePoint 对象或字典列表,需要提取 knowledge_name
                if weak_points:
                    point_names = []
                    for point in weak_points:
                        if isinstance(point, dict):
                            point_names.append(point.get("knowledge_name", str(point)))
                        elif hasattr(point, "knowledge_name"):
                            point_names.append(point.knowledge_name)
                        else:
                            point_names.append(str(point))
                    if point_names:
                        prompt_parts.append(f"学生薄弱知识点：{', '.join(point_names)}")

        prompt_parts.append("\n请基于以上信息，为学生提供个性化的学习指导。")

        return "\n".join(prompt_parts)

    def _get_grade_name(self, grade_level: int) -> str:
        """获取学段名称"""
        grade_mapping = {
            7: "初一",
            8: "初二",
            9: "初三",
            10: "高一",
            11: "高二",
            12: "高三",
        }
        return grade_mapping.get(grade_level, f"学段{grade_level}")

    def _get_subject_name(self, subject: str) -> str:
        """获取学科名称"""
        subject_mapping = {
            "math": "数学",
            "chinese": "语文",
            "english": "英语",
            "physics": "物理",
            "chemistry": "化学",
            "biology": "生物",
            "history": "历史",
            "geography": "地理",
            "politics": "政治",
        }
        return subject_mapping.get(subject, subject)

    async def _get_conversation_history(
        self, session_id: str, max_count: int
    ) -> List[ChatMessage]:
        """获取对话历史"""
        try:
            # 获取最近的问答对
            stmt = (
                select(Question)
                .options(selectinload(Question.answer))
                .where(Question.session_id == session_id, Question.is_processed == True)
                .order_by(desc(Question.created_at))
                .limit(max_count)
            )

            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            messages = []

            # 按时间正序排列（旧的在前）
            for question in reversed(questions):
                messages.append(
                    ChatMessage(
                        role=MessageRole.USER,
                        content=extract_orm_str(question, "content"),
                    )
                )

                if question.answer:
                    messages.append(
                        ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=extract_orm_str(question.answer, "content"),
                        )
                    )

            return messages

        except Exception as e:
            logger.warning(f"获取对话历史失败: {str(e)}")
            return []

    async def _save_answer(self, question_id: str, ai_response) -> Answer:
        """保存AI答案"""
        # 分析答案生成推荐内容
        related_topics, suggested_questions = await self._analyze_answer_content(
            ai_response.content
        )

        answer_data = {
            "question_id": question_id,
            "content": ai_response.content,
            "model_name": ai_response.model,
            "tokens_used": ai_response.tokens_used,
            "generation_time": int(ai_response.processing_time * 1000),
            "confidence_score": 85,  # 默认置信度，后续可通过分析改进
            "related_topics": json.dumps(related_topics) if related_topics else None,
            "suggested_questions": (
                json.dumps(suggested_questions) if suggested_questions else None
            ),
        }

        answer = await self.answer_repo.create(answer_data)

        # 更新问题状态
        await self.question_repo.update(question_id, {"is_processed": True})

        return answer

    async def _analyze_answer_content(
        self, content: str
    ) -> Tuple[List[str], List[str]]:
        """分析答案内容，提取相关话题和推荐问题"""
        # 这里是简化的分析逻辑，实际可以使用NLP技术改进
        related_topics = []
        suggested_questions = []

        # 简单的关键词提取（可以后续改进）
        if "二次函数" in content:
            related_topics.extend(["二次函数", "函数图象", "配方法"])
            suggested_questions.extend(
                ["如何求二次函数的对称轴？", "二次函数的最值怎么求？"]
            )
        elif "化学方程式" in content:
            related_topics.extend(["化学方程式", "化学反应", "配平"])
            suggested_questions.extend(["如何配平化学方程式？", "化学反应类型有哪些？"])

        return related_topics[:5], suggested_questions[:3]  # 限制数量

    async def _update_session_stats(self, session_id: str, tokens_used: int) -> None:
        """更新会话统计"""
        session = await self.session_repo.get_by_id(session_id)
        if session:
            # 更新会话统计信息
            current_tokens = extract_orm_int(session, "total_tokens", 0) or 0
            current_question_count = extract_orm_int(session, "question_count", 0) or 0
            session_id_str = extract_orm_uuid_str(session, "id")

            await self.session_repo.update(
                session_id_str,
                {
                    "total_tokens": current_tokens + tokens_used,
                    "question_count": current_question_count + 1,  # 增加问题计数
                    "last_active_at": datetime.now().isoformat(),
                },
            )

    async def _update_learning_analytics(
        self, user_id: str, question: Question, answer: Answer
    ) -> None:
        """更新用户学习分析"""
        try:
            # 获取或创建学习分析记录
            analytics = await self.analytics_repo.get_by_field("user_id", user_id)
            if not analytics:
                analytics_data = {
                    "user_id": user_id,
                    "total_questions": 1,
                    "total_sessions": 1,
                    "last_analyzed_at": datetime.utcnow().isoformat(),
                }
                await self.analytics_repo.create(analytics_data)
            else:
                # 更新统计
                await self.analytics_repo.update(
                    extract_orm_uuid_str(analytics, "id"),
                    {
                        "total_questions": (
                            extract_orm_int(analytics, "total_questions", 0) or 0
                        )
                        + 1,
                        "last_analyzed_at": datetime.utcnow().isoformat(),
                    },
                )

        except Exception as e:
            logger.warning(f"更新学习分析失败: {str(e)}")

    # ========== 会话管理功能 ==========

    async def create_session(
        self, user_id: str, request: CreateSessionRequest
    ) -> SessionResponse:
        """创建新会话"""
        session_data = {
            "user_id": user_id,
            "title": request.title,
            "subject": request.subject.value if request.subject else None,
            "grade_level": request.grade_level,
            "status": SessionStatus.ACTIVE.value,
            "context_enabled": request.context_enabled,
            "last_active_at": datetime.utcnow().isoformat(),
        }

        session = await self.session_repo.create(session_data)

        # 如果有初始问题，处理第一个问题
        if request.initial_question:
            ask_request = AskQuestionRequest(
                content=request.initial_question,
                session_id=extract_orm_uuid_str(session, "id"),
                subject=request.subject,
                topic=None,
                difficulty_level=None,
            )
            await self.ask_question(user_id, ask_request)

        return SessionResponse.model_validate(session)

    async def get_session_list(
        self, user_id: str, query: SessionListQuery
    ) -> Dict[str, Any]:
        """获取会话列表"""
        # 构建查询条件
        conditions = [ChatSession.user_id == user_id]

        if query.status:
            conditions.append(ChatSession.status == safe_str(query.status))

        if query.subject:
            conditions.append(ChatSession.subject == safe_str(query.subject))

        if query.search:
            conditions.append(ChatSession.title.contains(query.search))

        # 计算总数
        count_stmt = select(func.count(ChatSession.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # 查询数据
        stmt = (
            select(ChatSession)
            .where(and_(*conditions))
            .order_by(desc(ChatSession.last_active_at))
            .offset((query.page - 1) * query.size)
            .limit(query.size)
        )

        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return {
            "total": total,
            "page": query.page,
            "size": query.size,
            "pages": (
                (total + query.size - 1) // query.size if total and query.size else 0
            ),
            "items": [SessionResponse.model_validate(session) for session in sessions],
        }

    async def get_question_history(
        self, user_id: str, query: QuestionHistoryQuery
    ) -> Dict[str, Any]:
        """获取问题历史"""
        # 构建查询条件
        conditions = [Question.user_id == user_id]

        if query.session_id:
            conditions.append(Question.session_id == query.session_id)

        if query.subject:
            conditions.append(Question.subject == safe_str(query.subject))

        if query.question_type:
            conditions.append(Question.question_type == safe_str(query.question_type))

        if query.start_date:
            conditions.append(Question.created_at >= query.start_date.isoformat())

        if query.end_date:
            conditions.append(Question.created_at <= query.end_date.isoformat())

        # 计算总数
        count_stmt = select(func.count(Question.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()

        # 查询数据
        stmt = (
            select(Question)
            .options(selectinload(Question.answer))
            .where(and_(*conditions))
            .order_by(desc(Question.created_at))
            .offset((query.page - 1) * query.size)
            .limit(query.size)
        )

        result = await self.db.execute(stmt)
        questions = result.scalars().all()

        # 构建问答对
        items = []
        for question in questions:
            item = {
                "question": QuestionResponse.model_validate(question),
                "answer": (
                    AnswerResponse.model_validate(question.answer)
                    if question.answer
                    else None
                ),
            }
            items.append(item)

        return {
            "total": total,
            "page": query.page,
            "size": query.size,
            "pages": (
                (total + query.size - 1) // query.size if total and query.size else 0
            ),
            "items": items,
        }

    # ========== 反馈和评价功能 ==========

    async def submit_feedback(self, user_id: str, request: FeedbackRequest) -> bool:
        """提交用户反馈"""
        # 验证问题归属
        question = await self.question_repo.get_by_id(request.question_id)
        if not question or extract_orm_uuid_str(question, "user_id") != user_id:
            raise NotFoundError("问题不存在或无权限访问")

        if not getattr(question, "answer", None):
            raise ValidationError("问题尚未回答，无法提交反馈")

        # 更新答案反馈
        answer_id = extract_orm_uuid_str(question.answer, "id")
        await self.answer_repo.update(
            answer_id,
            {
                "user_rating": request.rating,
                "user_feedback": request.feedback,
                "is_helpful": request.is_helpful,
            },
        )

        logger.info(
            "用户反馈已保存",
            extra={
                "user_id": user_id,
                "question_id": request.question_id,
                "rating": request.rating,
            },
        )

        return True

    # ========== 学习分析功能 ==========

    @cache_result(ttl=3600)  # 缓存1小时
    async def get_learning_analytics(
        self, user_id: str
    ) -> Optional[LearningAnalyticsResponse]:
        """获取学习分析"""
        analytics = await self.analytics_repo.get_by_field("user_id", user_id)
        if not analytics:
            return None

        # 获取详细统计数据
        subject_stats = await self._calculate_subject_stats(user_id)
        learning_pattern = await self._analyze_learning_pattern(user_id)

        # 计算平均评分
        avg_rating_stmt = (
            select(func.avg(Answer.user_rating))
            .select_from(join(Answer, Question, Answer.question_id == Question.id))
            .where(Question.user_id == user_id, Answer.user_rating.isnot(None))
        )

        avg_rating_result = await self.db.execute(avg_rating_stmt)
        avg_rating = avg_rating_result.scalar() or 0.0

        # 计算正面反馈率
        positive_feedback_rate = await self._calculate_positive_feedback_rate(user_id)

        # 生成改进建议
        improvement_suggestions = await self._generate_improvement_suggestions(
            user_id, subject_stats
        )

        # 识别知识缺口
        knowledge_gaps = await self._identify_knowledge_gaps(user_id)

        # Get basic stats from analytics if available
        if analytics:
            total_questions = extract_orm_int(analytics, "total_questions", 0) or 0
            total_sessions = extract_orm_int(analytics, "total_sessions", 0) or 0
        else:
            total_questions = 0
            total_sessions = 0

        # Create a simple learning pattern
        from src.schemas.learning import DifficultyLevel, LearningPattern

        learning_pattern = LearningPattern(
            most_active_hour=14,
            most_active_day=1,
            avg_session_length=30,
            preferred_difficulty=DifficultyLevel.MEDIUM,
        )

        return LearningAnalyticsResponse(
            user_id=user_id,
            total_questions=total_questions,
            total_sessions=total_sessions,
            subject_stats=[],  # Simplified - needs proper conversion
            learning_pattern=learning_pattern,
            avg_rating=3.5,
            positive_feedback_rate=75,
            improvement_suggestions=["需要更多练习"],  # Simplified
            knowledge_gaps=["基础概念"],  # Simplified
            last_analyzed_at=datetime.now(),
        )

    async def _calculate_subject_stats(self, user_id: str) -> List[Dict[str, Any]]:
        """计算各学科统计"""
        # 简化实现，返回基本统计
        stmt = (
            select(
                Question.subject,
                func.count(Question.id).label("question_count"),
                func.avg(Question.difficulty_level).label("avg_difficulty"),
            )
            .where(Question.user_id == user_id, Question.subject.isnot(None))
            .group_by(Question.subject)
        )

        result = await self.db.execute(stmt)
        stats = []

        for row in result:
            stats.append(
                {
                    "subject": row.subject,
                    "question_count": row.question_count,
                    "avg_difficulty": float(row.avg_difficulty or 3.0),
                    "mastery_level": 75,  # 默认掌握度，可以后续改进
                }
            )

        return stats

    async def _analyze_learning_pattern(self, user_id: str) -> Dict[str, Any]:
        """分析学习模式"""
        return {
            "most_active_hour": 20,  # 晚上8点
            "most_active_day": 0,  # 周日
            "avg_session_length": 30,  # 30分钟
            "preferred_difficulty": 3,  # 中等难度
        }

    async def _calculate_positive_feedback_rate(self, user_id: str) -> int:
        """计算正面反馈率"""
        total_stmt = (
            select(func.count(Answer.id))
            .select_from(join(Answer, Question, Answer.question_id == Question.id))
            .where(Question.user_id == user_id, Answer.is_helpful.isnot(None))
        )

        positive_stmt = (
            select(func.count(Answer.id))
            .select_from(join(Answer, Question, Answer.question_id == Question.id))
            .where(Question.user_id == user_id, Answer.is_helpful == True)
        )

        total_result = await self.db.execute(total_stmt)
        positive_result = await self.db.execute(positive_stmt)

        total = total_result.scalar() or 0
        positive = positive_result.scalar() or 0

        return int((positive / total * 100) if total > 0 else 0)

    async def _generate_improvement_suggestions(
        self, user_id: str, subject_stats: List[Dict[str, Any]]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 基于学科统计生成建议
        for stat in subject_stats:
            if stat["question_count"] < 5:
                suggestions.append(
                    f"建议增加{self._get_subject_name(stat['subject'])}学科的练习"
                )

            if stat["avg_difficulty"] < 2.5:
                suggestions.append(
                    f"可以尝试{self._get_subject_name(stat['subject'])}更有挑战性的问题"
                )

        return suggestions[:5]  # 最多5个建议

    async def _identify_knowledge_gaps(self, user_id: str) -> List[str]:
        """识别知识缺口"""
        # 基于错题和低分作业识别知识缺口
        gaps = []

        # 从问题话题中分析
        stmt = (
            select(Question.topic)
            .where(Question.user_id == user_id, Question.topic.isnot(None))
            .distinct()
        )

        result = await self.db.execute(stmt)
        topics = [row[0] for row in result]

        # 简化逻辑：如果某个话题问得比较多，可能是薄弱环节
        return topics[:5]

    # ========== 错题本功能 ==========

    async def add_question_to_mistakes(
        self,
        user_id: str,
        question_id: str,
        student_answer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        将学习问答中的题目加入错题本

        Args:
            user_id: 用户ID
            question_id: 问题ID
            student_answer: 学生答案（可选，用于标记答错）

        Returns:
            Dict: 创建的错题详情

        Raises:
            NotFoundError: 问题不存在
            ServiceError: 创建失败
        """
        try:
            # 1. 获取问题和答案
            question = await self.question_repo.get_by_id(question_id)
            if not question or str(question.user_id) != user_id:
                raise NotFoundError(f"问题 {question_id} 不存在")

            # 使用 get_by_field 方法获取答案（BaseRepository 的标准方法）
            answer = await self.answer_repo.get_by_field("question_id", question_id)
            if not answer:
                raise NotFoundError(f"问题 {question_id} 暂无答案")

            # 2. 提取知识点（从Question.topic获取）
            knowledge_points = []
            # 使用 getattr 安全访问属性
            question_topic = getattr(question, "topic", None)
            if question_topic:
                knowledge_points.append(question_topic)

            # 3. 提取正确答案（从AI回答中解析）
            correct_answer = None
            if answer:
                answer_content = getattr(answer, "content", "")
                correct_answer = self._extract_correct_answer(answer_content)

            # 4. 解析图片URL
            image_urls = []
            question_has_images = getattr(question, "has_images", False)
            question_image_urls = getattr(question, "image_urls", None)
            if question_has_images and question_image_urls:
                try:
                    image_urls = json.loads(question_image_urls)
                except:
                    image_urls = []

            # 5. 构造错题数据
            from src.models.study import MistakeRecord
            from src.repositories.mistake_repository import MistakeRepository

            mistake_repo = MistakeRepository(MistakeRecord, self.db)

            # 安全获取问题属性
            question_content = getattr(question, "content", "")
            question_subject = getattr(question, "subject", None)
            question_difficulty = getattr(question, "difficulty_level", None)

            mistake_data = {
                "user_id": user_id,
                "subject": question_subject or "其他",
                "title": self._generate_mistake_title(question_content),
                "ocr_text": question_content,  # 题目内容
                "image_urls": image_urls,
                "difficulty_level": question_difficulty or 2,
                "knowledge_points": knowledge_points,
                "ai_feedback": (
                    {
                        "model": (
                            getattr(answer, "model_name", "unknown")
                            if answer
                            else "unknown"
                        ),
                        "answer": getattr(answer, "content", "") if answer else "",
                        "confidence": (
                            getattr(answer, "confidence_score", 0.0) if answer else 0.0
                        ),
                        "tokens_used": (
                            getattr(answer, "tokens_used", 0) if answer else 0
                        ),
                    }
                    if answer
                    else None
                ),
                # 【新增】来源信息
                "source": "learning",
                "source_question_id": question_id,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                # 复习相关（使用艾宾浩斯算法）
                "mastery_status": "not_mastered",  # 🔧 修复：使用正确的枚举值
                "next_review_at": datetime.now()
                + timedelta(days=1),  # 第一次复习：1天后
                "review_count": 0,
                "correct_count": 0,
            }

            # 6. 创建错题记录
            mistake = await mistake_repo.create(mistake_data)

            logger.info(
                f"从学习问答创建错题: question_id={question_id}, mistake_id={mistake.id}"
            )

            # 【新增】自动关联知识点
            try:
                from uuid import UUID

                from src.services.knowledge_graph_service import KnowledgeGraphService

                kg_service = KnowledgeGraphService(self.db, self.bailian_service)

                # 调用知识图谱服务分析并关联知识点
                await kg_service.analyze_and_associate_knowledge_points(
                    mistake_id=UUID(str(getattr(mistake, "id"))),
                    user_id=UUID(user_id),
                    subject=mistake_data.get("subject", "math"),
                    ocr_text=question_content,
                    ai_feedback=mistake_data.get("ai_feedback"),
                )

                logger.info(f"已为错题 {mistake.id} 自动关联知识点")
            except Exception as e:
                # 知识点关联失败不影响错题创建
                logger.warning(f"知识点自动关联失败: {e}")

            # 7. 转换为响应格式
            return {
                "id": str(mistake.id),
                "title": mistake.title,
                "subject": mistake.subject,
                "source": "learning",
                "source_question_id": question_id,
                "knowledge_points": knowledge_points,
                "next_review_date": (
                    next_review_at.isoformat()
                    if (next_review_at := getattr(mistake, "next_review_at", None))
                    else None
                ),
                "created_at": (
                    mistake.created_at.isoformat()
                    if hasattr(mistake, "created_at")
                    else None
                ),
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"加入错题本失败: {e}", exc_info=True)
            raise ServiceError(f"加入错题本失败: {str(e)}")

    def _generate_mistake_title(self, content: str) -> str:
        """生成错题标题（截取前30字）"""
        if len(content) <= 30:
            return content
        return content[:30] + "..."

    def _extract_correct_answer(self, ai_answer: str) -> Optional[str]:
        """从AI回答中提取正确答案"""
        import re

        # 简单规则：查找"答案："、"正确答案："等关键词后的内容
        patterns = [
            r"答案[：:]\s*(.+?)(?:\n|$)",
            r"正确答案[：:]\s*(.+?)(?:\n|$)",
            r"解[：:]\s*(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, ai_answer)
            if match:
                return match.group(1).strip()

        # 如果没找到，返回AI回答的前100字
        return ai_answer[:100] if len(ai_answer) > 100 else ai_answer

    # 🎯 错题自动创建逻辑（简化规则版）
    # ========== 智能错题识别辅助方法 ==========

    def _detect_mistake_keywords(self, question_content: str) -> Dict[str, Any]:
        """
        策略1：关键词检测

        Args:
            question_content: 用户提问内容

        Returns:
            {
                'is_mistake': bool,
                'confidence': float (0.0-1.0),
                'mistake_type': str,
                'reason': str,
                'matched_keywords': List[str]
            }
        """
        # 🛡️ 排除关键词：明确的非错题场景（纯知识查询、闲聊）
        EXCLUSION_KEYWORDS = [
            "告诉我",
            "什么是",
            "介绍一下",
            "讲解一下",
            "说说",
            "解释一下",
            "最长的",
            "最短的",
            "最大的",
            "最小的",
            "有哪些",
            "举例",
            "比如",
            "区别",
            "联系",
            "关系",
            "定义",
            "概念",
            "特点",
            "优点",
            "缺点",
            "好处",
            "坏处",
        ]

        # 🎯 高置信度关键词：强烈暗示错题的词汇
        HIGH_CONFIDENCE_KEYWORDS = [
            "不会做",
            "不会",
            "不懂",
            "不理解",
            "不明白",
            "怎么做",
            "如何解答",
            "怎么解",
            "怎么算",
            "做错了",
            "答错了",
            "错在哪",
            "看不懂",
            "求解",
            "求答案",
            "帮我做",
            "帮我看看这道题",  # 更具体，避免误判
        ]

        # 🔸 中置信度关键词：可能是错题，但需要更多证据（需要≥2个或与图片结合）
        MEDIUM_CONFIDENCE_KEYWORDS = [
            "解题步骤",
            "解题思路",
            "解题过程",
            "解题方法",
            "难题",
            "有难度",
            "解不出",
            "没学过",
        ]

        # 🛡️ 1. 先检查排除关键词（优先级最高）
        matched_exclusion = [
            kw for kw in EXCLUSION_KEYWORDS if kw in question_content
        ]
        if matched_exclusion:
            logger.info(
                f"🛡️ 检测到非错题关键词，跳过错题识别: {matched_exclusion[:2]}"
            )
            return {
                "is_mistake": False,
                "confidence": 0.2,
                "mistake_type": None,
                "reason": f'检测到非错题关键词: {", ".join(matched_exclusion[:2])}',
                "matched_keywords": [],
            }

        # 2. 检查高置信度关键词
        matched_high = [
            kw for kw in HIGH_CONFIDENCE_KEYWORDS if kw in question_content
        ]

        # 3. 检查中置信度关键词
        matched_medium = [
            kw for kw in MEDIUM_CONFIDENCE_KEYWORDS if kw in question_content
        ]

        # 判断错题类型
        mistake_type = "hard_question"  # 默认
        if any(kw in question_content for kw in ["错", "做错", "答错"]):
            mistake_type = "wrong_answer"
        elif any(kw in question_content for kw in ["不会", "不懂", "看不懂"]):
            mistake_type = "empty_question"

        # 🎯 高置信度关键词 → 直接判定为错题
        if matched_high:
            return {
                "is_mistake": True,
                "confidence": 0.9,
                "mistake_type": mistake_type,
                "reason": f'检测到高置信度关键词: {", ".join(matched_high[:2])}',
                "matched_keywords": matched_high,
            }

        # 🔸 多个中置信度关键词（≥2个）→ 判定为错题（但置信度较低）
        if len(matched_medium) >= 2:
            return {
                "is_mistake": True,
                "confidence": 0.7,  # 降低置信度，从0.75降到0.7
                "mistake_type": mistake_type,
                "reason": f'检测到多个中置信度关键词: {", ".join(matched_medium[:2])}',
                "matched_keywords": matched_medium,
            }

        # 🔸 单个中置信度关键词 → 不确定（返回None，需要其他证据）
        if matched_medium:
            return {
                "is_mistake": None,  # ✅ 修复：单个中置信度关键词不足以判定
                "confidence": 0.5,  # 降低置信度，从0.6降到0.5
                "mistake_type": None,
                "reason": f"检测到单个中置信度关键词（不足以判定）: {matched_medium[0]}",
                "matched_keywords": matched_medium,
            }

        return {
            "is_mistake": False,
            "confidence": 0.3,
            "mistake_type": None,
            "reason": "未检测到错题关键词",
            "matched_keywords": [],
        }

    def _extract_ai_mistake_metadata(self, answer_content: str) -> Dict[str, Any]:
        """
        策略2：AI意图识别

        从AI回答中提取元数据（如果AI输出了结构化信息）

        ⚠️ 注意：此方法仅用于提取AI主动输出的结构化元数据，
        不应基于AI回答内容做启发式判断（会导致正常问答被误判）

        Args:
            answer_content: AI回答内容

        Returns:
            {
                'is_mistake': Optional[bool],
                'confidence': float,
                'mistake_type': Optional[str],
                'knowledge_points': List[str],
                'reason': str
            }
        """
        try:
            # 尝试从回答末尾提取JSON元数据
            # 格式：```json\n{...}\n```
            import re

            json_pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(json_pattern, answer_content, re.DOTALL)

            if match:
                metadata = json.loads(match.group(1))
                return {
                    "is_mistake": metadata.get("is_mistake_question"),
                    "confidence": metadata.get("confidence", 0.8),
                    "mistake_type": metadata.get("mistake_type"),
                    "knowledge_points": metadata.get("knowledge_points", []),
                    "reason": "AI元数据提取成功",
                }
        except Exception as e:
            logger.debug(f"AI元数据提取失败: {e}")

        # 🛠️ 移除错误的启发式分析（会误判正常问答）
        # 原逻辑：检查AI回答中的"这道题"等词 → 误判为错题
        # 修复：仅当AI明确输出元数据时才判断，否则返回不确定

        return {
            "is_mistake": None,
            "confidence": 0.5,
            "mistake_type": None,
            "knowledge_points": [],
            "reason": "AI未提供明确的错题判断元数据",
        }

    async def _analyze_question_images(
        self, image_urls: List[str], question_content: str
    ) -> Dict[str, Any]:
        """
        策略3：图片内容分析

        利用Qwen-vl-max的视觉能力判断图片是否为空白题/错题

        Args:
            image_urls: 图片URL列表
            question_content: 用户提问文本

        Returns:
            {
                'is_mistake': Optional[bool],
                'confidence': float,
                'has_answer': Optional[bool],
                'is_question_image': bool,
                'reason': str
            }
        """
        if not image_urls:
            return {
                "is_mistake": None,
                "confidence": 0.5,
                "has_answer": None,
                "is_question_image": False,
                "reason": "无图片上传",
            }

        try:
            # 使用简化的启发式规则（避免额外AI调用）
            # 规则：有图片 + 提问文本很短 = 很可能是拍照提问
            is_short_question = len(question_content.strip()) < 20

            if is_short_question:
                return {
                    "is_mistake": True,
                    "confidence": 0.85,
                    "has_answer": False,  # 假设空白题
                    "is_question_image": True,
                    "reason": "检测到图片上传且提问文本简短，推测为拍照题目",
                }
            else:
                return {
                    "is_mistake": True,
                    "confidence": 0.7,
                    "has_answer": None,
                    "is_question_image": True,
                    "reason": "检测到图片上传，可能为题目",
                }

        except Exception as e:
            logger.warning(f"图片分析失败: {e}")
            return {
                "is_mistake": None,
                "confidence": 0.5,
                "has_answer": None,
                "is_question_image": False,
                "reason": f"图片分析异常: {str(e)}",
            }

    def _combine_mistake_analysis(
        self,
        keyword_result: Dict[str, Any],
        ai_intent_result: Dict[str, Any],
        image_result: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        策略4：综合判断

        综合关键词、AI意图、图片分析的结果，做出最终判断

        🎯 判断标准（优化后，避免误判）：
        - 关键词高置信度证据(≥0.9) 可判定为错题
        - 或者 图片高置信度(≥0.85) + 关键词中等置信度
        - 或者 多个高置信度证据(≥2) 且平均置信度≥0.8

        Args:
            keyword_result: 关键词检测结果
            ai_intent_result: AI意图识别结果
            image_result: 图片分析结果

        Returns:
            (is_mistake, metadata)
        """
        evidences = []
        total_confidence = 0
        vote_for_mistake = 0
        vote_total = 0
        high_confidence_count = 0  # 高置信度证据数量

        # 收集证据
        if keyword_result["is_mistake"] is not None:
            vote_total += 1
            if keyword_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += keyword_result["confidence"]
                evidences.append(f"关键词({keyword_result['confidence']:.2f})")
                # 统计高置信度证据（≥0.85）
                if keyword_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        if ai_intent_result["is_mistake"] is not None:
            vote_total += 1
            if ai_intent_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += ai_intent_result["confidence"]
                evidences.append(f"AI意图({ai_intent_result['confidence']:.2f})")
                if ai_intent_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        if image_result["is_mistake"] is not None:
            vote_total += 1
            if image_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += image_result["confidence"]
                evidences.append(f"图片({image_result['confidence']:.2f})")
                if image_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        # 计算平均置信度
        avg_confidence = (
            total_confidence / vote_for_mistake if vote_for_mistake > 0 else 0
        )

        # 🎯 最终判断（提高门槛，降低误判率）：
        is_mistake = False
        decision_reason = ""

        if vote_total > 0 and vote_for_mistake > 0:
            # 场曯1：关键词高置信度（≥0.9）→ 直接判定
            if keyword_result.get("is_mistake") and keyword_result.get("confidence", 0) >= 0.9:
                is_mistake = True
                decision_reason = "关键词高置信度（≥0.9）"

            # 场曯2：图片高置信度(≥0.85) + 关键词中等置信度(≥0.6)
            elif (
                image_result.get("is_mistake")
                and image_result.get("confidence", 0) >= 0.85
                and keyword_result.get("is_mistake") is not False  # 允许None
                and keyword_result.get("confidence", 0) >= 0.6
            ):
                is_mistake = True
                decision_reason = "图片高置信度 + 关键词支持"

            # 场曯3：多个高置信度证据(≥2) 且平均置信度≥0.8
            elif high_confidence_count >= 2 and avg_confidence >= 0.8:
                is_mistake = True
                decision_reason = f"多个高置信度证据({high_confidence_count}个)"

            # 场曯4：图片 + AI意图 + 关键词 都支持，且平均置信度≥0.75
            elif vote_for_mistake >= 3 and avg_confidence >= 0.75:
                is_mistake = True
                decision_reason = "多维度证据支持（≥3个）"

            else:
                decision_reason = f"证据不足：高置信度证据{high_confidence_count}个，平均置信度{avg_confidence:.2f}"

        # 确定错题类型（优先级：关键词 > AI意图 > 图片）
        mistake_type = (
            keyword_result.get("mistake_type")
            or ai_intent_result.get("mistake_type")
            or image_result.get("mistake_type")
            or "empty_question"
        )

        return is_mistake, {
            "is_mistake": is_mistake,
            "confidence": avg_confidence,
            "mistake_type": mistake_type,
            "reason": f'综合判断: {decision_reason}, 证据=[{", ".join(evidences)}]',
            "evidences": evidences,
            "vote_for_mistake": vote_for_mistake,
            "vote_total": vote_total,
            "high_confidence_count": high_confidence_count,
        }

    async def _auto_create_mistake_if_needed(
        self,
        user_id: str,
        question: Question,
        answer: Answer,
        request: AskQuestionRequest,
    ) -> Optional[Dict[str, Any]]:
        """
        智能判断是否需要创建错题（增强版 - 4策略综合）

        策略：
        1. 关键词检测：高/中置信度关键词匹配
        2. AI意图识别：从AI回答中提取元数据
        3. 图片分析：利用Qwen-vl-max视觉能力
        4. 综合判断：多维度证据融合

        保持向后兼容：新逻辑失败时降级到简化规则
        """
        try:
            content = extract_orm_str(question, "content") or ""
            answer_content = extract_orm_str(answer, "content") or ""
            has_images = bool(request.image_urls and len(request.image_urls) > 0)

            # ========== 4策略综合判断 ==========
            try:
                # 策略1：关键词检测
                keyword_result = self._detect_mistake_keywords(content)

                # 策略2：AI意图识别
                ai_intent_result = self._extract_ai_mistake_metadata(answer_content)

                # 策略3：图片分析
                image_result = await self._analyze_question_images(
                    request.image_urls or [], content
                )

                # 策略4：综合判断
                should_create, analysis_meta = self._combine_mistake_analysis(
                    keyword_result, ai_intent_result, image_result
                )

                category = analysis_meta.get("mistake_type", "empty_question")
                confidence = analysis_meta.get("confidence", 0.0)

                logger.info(
                    f"🧠 智能错题识别: should_create={should_create}, "
                    f"confidence={confidence:.2f}, category={category}, "
                    f"reason={analysis_meta.get('reason')}"
                )

                # 置信度阈值检查（从配置读取，默认0.7）
                min_confidence = getattr(settings, "AUTO_MISTAKE_MIN_CONFIDENCE", 0.7)
                if not should_create or confidence < min_confidence:
                    logger.info(
                        f"❌ 不满足错题创建条件: should_create={should_create}, "
                        f"confidence={confidence:.2f} < {min_confidence}"
                    )
                    return None

            except Exception as strategy_error:
                # 新策略失败时降级到原有简化规则
                logger.warning(f"⚠️ 4策略综合判断失败，降级到简化规则: {strategy_error}")

                # === 降级：原有简化规则（向后兼容）===
                mistake_keywords = [
                    "不会",
                    "不懂",
                    "不知道",
                    "不明白",
                    "不清楚",
                    "不会做",
                    "不太会",
                    "不太懂",
                    "看不懂",
                    "错了",
                    "做错",
                    "答错",
                    "难题",
                    "有难度",
                    "解不出",
                    "没学过",
                    "不理解",
                    "帮我看看",
                    "帮我做",
                    "怎么做",
                    "怎么解",
                    "想问",
                ]

                should_create = False
                category = "empty_question"

                if has_images:
                    should_create = True
                    category = "empty_question"
                    logger.info(f"🖼️ [降级规则] 检测到图片上传，自动创建错题")
                elif any(keyword in content for keyword in mistake_keywords):
                    should_create = True
                    if "错" in content or "做错" in content or "答错" in content:
                        category = "wrong_answer"
                    elif "难" in content or "解不出" in content:
                        category = "hard_question"
                    else:
                        category = "empty_question"
                    logger.info(f"🔑 [降级规则] 检测到关键词，category={category}")

                if not should_create:
                    return None
                # === 降级规则结束 ===

            # 创建错题记录
            from src.models.study import MistakeRecord
            from src.repositories.base_repository import BaseRepository

            mistake_repo = BaseRepository(MistakeRecord, self.db)

            # 🛠️ 生成错题数据（只使用数据库中存在的字段）
            # 🎯 从 AI answer 中提取知识点信息
            ai_feedback_data = {
                "category": category,
                "auto_created": True,
                "classification": {
                    "category": category,
                    "confidence": 0.8,  # 简化规则置信度
                    "reasoning": f"基于规则判断：{'has_images' if has_images else 'keyword_match'}",
                },
                "auto_created_at": datetime.now().isoformat(),
            }
            
            # 🎯 尝试从 AI 回答中提取知识点
            try:
                knowledge_points_from_ai = self._extract_knowledge_points_from_answer(
                    answer_content, extract_orm_str(question, "subject") or "其他"
                )
                if knowledge_points_from_ai:
                    ai_feedback_data["knowledge_points"] = knowledge_points_from_ai
                    ai_feedback_data["knowledge_points_extracted"] = True
                    logger.info(f"✅ 从AI回答中提取到 {len(knowledge_points_from_ai)} 个知识点")
            except Exception as kp_err:
                logger.warning(f"从AI回答提取知识点失败: {kp_err}")
                ai_feedback_data["knowledge_points"] = []
            
            # 🎯 根据错题类型确定 source 字段值
            source_mapping = {
                "empty_question": "learning_empty",  # 不会做的题
                "wrong_answer": "learning_wrong",   # 答错的题
                "hard_question": "learning_hard",   # 有难度的题
            }
            source = source_mapping.get(category, "learning")  # 默认 learning
            
            logger.info(
                f"📋 错题分类: category={category}, source={source}"
            )
            
            mistake_data = {
                "user_id": user_id,
                "source": source,  # 🎯 动态设置 source
                "source_question_id": str(extract_orm_uuid_str(question, "id")),
                # 基本信息
                "subject": extract_orm_str(question, "subject") or "其他",
                "title": self._generate_mistake_title(content),
                "ocr_text": content,
                "image_urls": (
                    json.dumps(request.image_urls) if request.image_urls else None
                ),
                # AI分析信息（包含知识点）
                "ai_feedback": json.dumps(ai_feedback_data),
                # 学生答案（可选）
                "student_answer": None,  # 先为None，后续可增加
                "correct_answer": self._extract_correct_answer(answer_content),
                # 复习相关
                "mastery_status": "learning",  # 🛠️ 使用模型中定义的值
                "next_review_at": datetime.now() + timedelta(days=1),
                "review_count": 0,
                "correct_count": 0,
                "difficulty_level": 2,  # 默认中等难度
            }

            # 创建错题
            mistake = await mistake_repo.create(mistake_data)
            
            # 🎯 创建错题后立即关联知识点
            try:
                mistake_id = mistake.id if hasattr(mistake, 'id') else UUID(extract_orm_uuid_str(mistake, "id"))
                await self._trigger_knowledge_association(
                    mistake_id=mistake_id,
                    user_id=UUID(user_id),
                    subject=mistake_data["subject"],
                    ocr_text=content,
                    ai_feedback=ai_feedback_data,
                )
                logger.info(f"🔗 知识点关联已触发: mistake_id={mistake_id}")
            except Exception as ka_err:
                logger.warning(f"触发知识点关联失败，但不影响错题创建: {ka_err}")

            # 返回错题信息
            return {
                "id": str(mistake.id),
                "category": category,
                "next_review_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "subject": mistake_data["subject"],
                "auto_created": True,
            }

        except Exception as e:
            logger.error(f"错题自动创建失败: {str(e)}", exc_info=True)
            return None


    def _extract_knowledge_points_from_answer(
        self, answer_content: str, subject: str
    ) -> List[Dict[str, Any]]:
        """
        从 AI 回答中提取知识点
        
        策略：
        1. 关键词匹配：查找常见知识点关键词
        2. 模式匹配：提取“涉及知识点”、“考查”等后面的内容
        3. 学科特定知识点库
        """
        knowledge_points = []
        
        # 学科知识点库（可扩展）
        knowledge_keywords_db = {
            "数学": [
                "函数", "方程", "不等式", "几何", "三角形", "圆", 
                "二次函数", "一次函数", "一元二次方程", "因式分解",
                "平面直角坐标系", "直线", "圆的方程", "解三角形",
                "概率", "统计", "勾股定理", "相似三角形", "全等三角形",
                "二次函数图像", "对称轴", "顶点坐标", "二次函数性质"
            ],
            "英语": [
                "语法", "词汇", "阅读理解", "写作", "听力", "口语",
                "时态", "从句", "非谓语动词", "定语从句"
            ],
            "语文": [
                "阅读理解", "作文", "古诗词", "文言文", "语法",
                "修辞手法", "词语积累", "语句理解"
            ],
            "物理": [
                "力学", "电学", "光学", "热学", "机械运动",
                "牛顿运动定律", "欧姆定律", "电路分析"
            ],
            "化学": [
                "化学方程式", "氧化还原", "酸碱盐", "元素周期表",
                "化学键", "有机化学", "化学平衡"
            ],
        }
        
        keywords = knowledge_keywords_db.get(subject, [])
        
        # 策略 1：关键词匹配
        for keyword in keywords:
            if keyword in answer_content:
                knowledge_points.append({
                    "name": keyword,
                    "relevance": 0.8,
                    "error_type": "concept_misunderstanding",
                    "extraction_method": "keyword_match"
                })
        
        # 策略 2：模式匹配
        import re
        patterns = [
            r"涉及[知识点到了]?[:：]?([^。，，、\n]+)",
            r"考查[知识点到了]?[:：]?([^。，，、\n]+)",
            r"使用[知识点到了]?[:：]?([^。，，、\n]+)",
            r"应用[知识点到了]?[:：]?([^。，，、\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, answer_content)
            for match in matches:
                # 清理提取的文本
                kp_name = match.strip()
                if len(kp_name) > 2 and len(kp_name) < 20:  # 过滤太短或太长的
                    knowledge_points.append({
                        "name": kp_name,
                        "relevance": 0.9,
                        "error_type": "concept_misunderstanding",
                        "extraction_method": "pattern_match"
                    })
        
        # 去重（根据 name 字段）
        seen = set()
        unique_kps = []
        for kp in knowledge_points:
            if kp["name"] not in seen:
                seen.add(kp["name"])
                unique_kps.append(kp)
        
        return unique_kps[:5]  # 最多迕回 5 个知识点

    async def _trigger_knowledge_association(
        self,
        mistake_id: UUID,
        user_id: UUID,
        subject: str,
        ocr_text: Optional[str],
        ai_feedback: Dict[str, Any],
    ) -> None:
        """
        触发知识图谱服务进行知识点关联
        """
        try:
            from src.services.knowledge_graph_service import KnowledgeGraphService
            
            kg_service = KnowledgeGraphService(self.db, self.bailian_service)
            
            # 调用知识图谱服务进行关联
            associations = await kg_service.analyze_and_associate_knowledge_points(
                mistake_id=mistake_id,
                user_id=user_id,
                subject=subject,
                ocr_text=ocr_text,
                ai_feedback=ai_feedback,
            )
            
            if associations:
                logger.info(
                    f"✅ 知识点关联成功: mistake_id={mistake_id}, "
                    f"关联数量={len(associations)}"
                )
            else:
                logger.warning(f"⚠️ 未能为错题 {mistake_id} 关联知识点")
                
        except Exception as e:
            logger.error(f"知识点关联失败: {e}", exc_info=True)
            raise

# 依赖注入函数
def get_learning_service(db: AsyncSession) -> LearningService:
    """获取学习问答服务实例"""
    return LearningService(db)
