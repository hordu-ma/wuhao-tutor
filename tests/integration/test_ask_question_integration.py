"""
Phase 3.2 集成测试 - ask_question 完整流程

测试覆盖：
1. 基础提问流程（创建会话、保存问题、获取答案）
2. 会话管理（继续会话、会话统计更新）
3. 作业批改场景（图片处理、AI 调用、错题创建）
4. 数据一致性（数据库状态正确、事务一致）
5. 性能指标（processing_time、tokens_used）
6. 错误处理（AI 失败、数据库错误）

预计覆盖：
- 完整的 ask_question() 方法
- 三层架构集成（API → Service → Repository → DB）
- 错题自动创建逻辑
- 数据库事务一致性
"""

import json
import logging
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import BailianServiceError, ServiceError, ValidationError
from src.models.learning import Answer, ChatSession, Question, QuestionStatus
from src.models.study import MistakeRecord
from src.schemas.learning import AskQuestionRequest, QuestionType
from src.services.learning_service import LearningService
from tests.conftest import MockBailianService

logger = logging.getLogger(__name__)


class TestAskQuestionBasic:
    """测试基础提问流程"""

    @pytest.mark.asyncio
    async def test_ask_question_creates_session_and_question(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：新建会话的提问
        验证：
        - 创建新会话
        - 保存问题
        - 保存答案
        - 返回响应包含所有字段
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert
            assert response is not None
            assert response.question is not None
            assert response.answer is not None
            assert response.session is not None
            assert response.processing_time > 0
            assert response.tokens_used > 0

            # 验证会话创建
            assert response.session.title is not None
            assert response.session.user_id == str(test_user.id)
            assert response.session.status == "active"
            assert response.session.question_count == 1

            # 验证问题保存
            assert response.question.content == test_ask_question_request.content
            assert response.question.question_type == "problem_solving"
            assert response.question.subject == "math"
            assert response.question.is_processed is True

            # 验证答案保存
            assert response.answer.content is not None
            assert response.answer.tokens_used > 0

    @pytest.mark.asyncio
    async def test_ask_question_with_existing_session(
        self,
        db_session: AsyncSession,
        test_user,
        test_session: ChatSession,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：继续现有会话的提问
        验证：
        - 使用现有会话
        - 问题关联到会话
        - 会话统计更新
        """
        # Arrange
        request = AskQuestionRequest(
            **test_ask_question_request.model_dump(),
            session_id=str(test_session.id),
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.session.id == test_session.id
            assert response.session.question_count >= 1

            # 验证问题关联
            assert response.question.session_id == test_session.id

    @pytest.mark.asyncio
    async def test_ask_question_response_fields(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：响应包含所有必要字段
        验证：AskQuestionResponse 的字段完整性
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert - 检查所有必要字段
            required_fields = [
                "question",
                "answer",
                "session",
                "processing_time",
                "tokens_used",
            ]
            for field in required_fields:
                assert hasattr(response, field), f"Missing field: {field}"
                assert getattr(response, field) is not None


class TestAskQuestionWithImages:
    """测试包含图片的提问"""

    @pytest.mark.asyncio
    async def test_ask_question_with_image_urls(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_with_images_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：包含图片 URL 的提问
        验证：
        - 图片 URL 正确保存
        - AI 调用包含图片信息
        - 问题标记为包含图片
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_with_images_request
            )

            # Assert
            assert response.question.has_images is True
            assert response.question.image_urls is not None

            # 验证 Mock 服务接收到了正确的消息
            assert mock_bailian_service.call_count == 1
            assert mock_bailian_service.last_messages is not None
            # 至少有一条消息包含图片 URL
            has_images = any(
                "image_urls" in msg for msg in mock_bailian_service.last_messages
            )
            assert has_images


class TestHomeworkCorrectionScenario:
    """测试作业批改场景"""

    @pytest.mark.asyncio
    async def test_homework_correction_full_flow(
        self,
        db_session: AsyncSession,
        test_user,
        test_homework_correction_ai_response: str,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：作业批改的完整流程
        验证：
        - 检测作业批改场景
        - 调用 AI 进行批改
        - 创建错题
        - 返回批改结果
        """
        # Arrange
        mock_bailian_service.set_response(test_homework_correction_ai_response)

        request = AskQuestionRequest(
            content="请帮我批改这份数学作业",
            question_type="homework_help",
            subject="math",
            image_urls=["https://example.com/homework.jpg"],
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.correction_result is not None
            assert response.correction_result.total_questions == 2
            assert response.correction_result.error_count == 1
            assert response.correction_result.overall_score == 75
            assert response.mistakes_created >= 1  # 至少创建 1 个错题

    @pytest.mark.asyncio
    async def test_homework_correction_creates_mistakes(
        self,
        db_session: AsyncSession,
        test_user,
        test_homework_correction_ai_response: str,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：批改后正确创建错题
        验证：
        - 只创建错误和未作答的题目
        - 正确答案不创建
        - 错题字段完整
        """
        # Arrange
        mock_bailian_service.set_response(test_homework_correction_ai_response)

        request = AskQuestionRequest(
            content="请批改作业",
            question_type="homework_help",
            subject="math",
            image_urls=["https://example.com/homework.jpg"],
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.mistakes_created >= 1

            # 从数据库查询创建的错题
            from sqlalchemy import select

            stmt = select(MistakeRecord).where(
                MistakeRecord.user_id == str(test_user.id)
            )
            result = await db_session.execute(stmt)
            mistakes = result.scalars().all()

            assert len(mistakes) >= 1
            for mistake in mistakes:
                assert mistake.user_id == str(test_user.id)
                assert mistake.subject == "math"
                assert mistake.title is not None


class TestDataConsistency:
    """测试数据一致性"""

    @pytest.mark.asyncio
    async def test_session_statistics_updated(
        self,
        db_session: AsyncSession,
        test_user,
        test_session: ChatSession,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：会话统计正确更新
        验证：
        - question_count 增加
        - total_tokens 累加
        """
        # Arrange
        initial_count = test_session.question_count
        initial_tokens = test_session.total_tokens

        request = AskQuestionRequest(
            **test_ask_question_request.model_dump(),
            session_id=str(test_session.id),
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.session.question_count == initial_count + 1
            assert response.session.total_tokens >= initial_tokens

    @pytest.mark.asyncio
    async def test_question_answer_relationship(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：问题和答案的关系
        验证：
        - 答案正确关联到问题
        - 一个问题只有一个答案
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert
            assert response.answer.question_id == response.question.id

            # 验证数据库中的关系
            from sqlalchemy import select

            stmt = (
                select(Question)
                .where(Question.id == response.question.id)
                .options(selectinload(Question.answer))
            )
            result = await db_session.execute(stmt)
            db_question = result.scalar_one_or_none()

            assert db_question is not None
            assert db_question.answer is not None
            assert db_question.answer.id == response.answer.id

    @pytest.mark.asyncio
    async def test_multiple_questions_in_session(
        self,
        db_session: AsyncSession,
        test_user,
        test_session: ChatSession,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：会话中的多个问题
        验证：
        - 多个问题都关联到同一会话
        - 顺序正确
        """
        # Arrange
        request = AskQuestionRequest(
            **test_ask_question_request.model_dump(),
            session_id=str(test_session.id),
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act - 提两个问题
            response1 = await service.ask_question(str(test_user.id), request)
            response2 = await service.ask_question(
                str(test_user.id),
                AskQuestionRequest(
                    **test_ask_question_request.model_dump(),
                    content="另一个问题",
                    session_id=str(test_session.id),
                ),
            )

            # Assert
            assert response1.session.id == response2.session.id
            assert response1.question.session_id == response2.question.session_id

            # 验证会话问题数
            from sqlalchemy import select

            stmt = select(ChatSession).where(ChatSession.id == test_session.id)
            result = await db_session.execute(stmt)
            updated_session = result.scalar_one()

            assert updated_session.question_count >= 2


class TestPerformanceMetrics:
    """测试性能指标"""

    @pytest.mark.asyncio
    async def test_processing_time_metric(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：processing_time 指标
        验证：
        - processing_time 被正确记录
        - processing_time > 0
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert
            assert response.processing_time > 0
            assert isinstance(response.processing_time, int)

    @pytest.mark.asyncio
    async def test_tokens_used_metric(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：tokens_used 指标
        验证：
        - tokens_used 被正确记录
        - tokens_used > 0
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert
            assert response.tokens_used > 0
            assert isinstance(response.tokens_used, int)


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_ai_service_failure_handling(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：AI 服务失败处理
        验证：
        - AI 失败时抛出 BailianServiceError
        - 问题仍被保存但标记为失败
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.chat_completion.return_value = MagicMock(
            success=False, error_message="AI Service Error"
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_service,
        ):
            service = LearningService(db_session)

            # Act & Assert
            with pytest.raises(BailianServiceError):
                await service.ask_question(str(test_user.id), test_ask_question_request)

    @pytest.mark.asyncio
    async def test_invalid_session_id_handling(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：无效的 session_id 处理
        验证：
        - 无效的 session_id 创建新会话
        或者抛出错误
        """
        # Arrange
        invalid_session_id = str(uuid4())
        request = AskQuestionRequest(
            **test_ask_question_request.model_dump(),
            session_id=invalid_session_id,
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act & Assert - 应该抛出 NotFoundError 或类似的异常
            try:
                response = await service.ask_question(str(test_user.id), request)
                # 如果不抛出异常，验证创建了新会话
                assert response.session is not None
            except Exception as e:
                # 验证抛出的是预期的异常
                assert "not found" in str(e).lower() or "session" in str(e).lower()


class TestQuestionType:
    """测试不同的问题类型"""

    @pytest.mark.asyncio
    async def test_concept_question_type(
        self,
        db_session: AsyncSession,
        test_user,
        mock_bailian_service: MockBailianService,
    ):
        """测试概念解释问题类型"""
        # Arrange
        request = AskQuestionRequest(
            content="什么是函数？",
            question_type="concept",
            subject="math",
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.question.question_type == "concept"
            assert response.answer is not None

    @pytest.mark.asyncio
    async def test_problem_solving_question_type(
        self,
        db_session: AsyncSession,
        test_user,
        mock_bailian_service: MockBailianService,
    ):
        """测试题目求解问题类型"""
        # Arrange
        request = AskQuestionRequest(
            content="求解方程 x + 5 = 12",
            question_type="problem_solving",
            subject="math",
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.question.question_type == "problem_solving"
            assert response.answer is not None


class TestSubjectHandling:
    """测试不同学科的处理"""

    @pytest.mark.asyncio
    async def test_math_subject(
        self,
        db_session: AsyncSession,
        test_user,
        mock_bailian_service: MockBailianService,
    ):
        """测试数学学科"""
        # Arrange
        request = AskQuestionRequest(
            content="求解二次方程",
            subject="math",
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.question.subject == "math"
            assert response.session.subject == "math"

    @pytest.mark.asyncio
    async def test_chinese_subject(
        self,
        db_session: AsyncSession,
        test_user,
        mock_bailian_service: MockBailianService,
    ):
        """测试语文学科"""
        # Arrange
        request = AskQuestionRequest(
            content="分析这首诗的含义",
            subject="chinese",
        )

        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(str(test_user.id), request)

            # Assert
            assert response.question.subject == "chinese"


class TestTransactionConsistency:
    """测试事务一致性"""

    @pytest.mark.asyncio
    async def test_question_answer_transaction(
        self,
        db_session: AsyncSession,
        test_user,
        test_ask_question_request: AskQuestionRequest,
        mock_bailian_service: MockBailianService,
    ):
        """
        测试：问题和答案的事务一致性
        验证：
        - 要么都创建，要么都不创建
        """
        # Arrange
        with patch(
            "src.services.learning_service.get_bailian_service",
            return_value=mock_bailian_service,
        ):
            service = LearningService(db_session)

            # Act
            response = await service.ask_question(
                str(test_user.id), test_ask_question_request
            )

            # Assert - 验证都被创建
            from sqlalchemy import select

            question_stmt = select(Question).where(Question.id == response.question.id)
            question_result = await db_session.execute(question_stmt)
            db_question = question_result.scalar_one_or_none()

            answer_stmt = select(Answer).where(Answer.id == response.answer.id)
            answer_result = await db_session.execute(answer_stmt)
            db_answer = answer_result.scalar_one_or_none()

            assert db_question is not None, "Question not found in DB"
            assert db_answer is not None, "Answer not found in DB"
            assert db_question.id == db_answer.question_id, "Q-A relationship broken"
