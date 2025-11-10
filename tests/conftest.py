"""
Phase 3 测试基础设施
提供公共 fixture、Mock 服务和测试数据工厂

用途: 单元测试、集成测试、性能测试
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根路径到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.config import get_settings
from src.models.base import Base
from src.models.learning import Answer, ChatSession, Question, QuestionType
from src.models.study import MistakeRecord
from src.models.user import User
from src.schemas.learning import (
    AskQuestionRequest,
    DifficultyLevel,
    HomeworkCorrectionResult,
    QuestionCorrectionItem,
    SubjectType,
)
from src.services.bailian_service import ChatCompletionResponse

# ========== 数据库 Fixture ==========


@pytest.fixture
async def db_session():
    """
    创建测试数据库会话 (in-memory SQLite)

    Returns:
        AsyncSession: 异步数据库会话
    """
    # 创建 in-memory SQLite 引擎
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话工厂
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 创建会话并返回
    async with async_session() as session:
        yield session

    # 清理
    await engine.dispose()


@pytest.fixture
async def cleanup_db(db_session: AsyncSession):
    """
    清理数据库 fixture

    Args:
        db_session: 数据库会话
    """
    yield
    # 可选：在测试后清理特定的表
    # await db_session.execute(delete(MistakeRecord))
    # await db_session.commit()


# ========== Mock Bailian Service ==========


class MockBailianService:
    """
    Mock BailianService for testing
    避免实际的 AI API 调用
    """

    def __init__(self, default_response: Optional[str] = None):
        """
        初始化 Mock 服务

        Args:
            default_response: 默认 AI 响应内容
        """
        self.default_response = (
            default_response or self._get_default_correction_response()
        )
        self.call_count = 0
        self.last_messages = None
        self.last_kwargs = None

    def _get_default_correction_response(self) -> str:
        """获取默认的批改响应"""
        return json.dumps(
            {
                "corrections": [
                    {
                        "question_number": 1,
                        "question_type": "选择题",
                        "is_unanswered": False,
                        "student_answer": "B",
                        "correct_answer": "A",
                        "error_type": "理解错误",
                        "explanation": "这道题考查的是...",
                        "knowledge_points": ["知识点1", "知识点2"],
                        "score": 0,
                    },
                    {
                        "question_number": 2,
                        "question_type": "填空题",
                        "is_unanswered": True,
                        "student_answer": None,
                        "correct_answer": "42",
                        "error_type": None,
                        "explanation": "学生未作答",
                        "knowledge_points": ["知识点3"],
                        "score": 0,
                    },
                    {
                        "question_number": 3,
                        "question_type": "解答题",
                        "is_unanswered": False,
                        "student_answer": "过程正确",
                        "correct_answer": "过程正确",
                        "error_type": None,
                        "explanation": "答案正确",
                        "knowledge_points": ["知识点4"],
                        "score": 100,
                    },
                ],
                "summary": "总体不错，需要加强理解",
                "overall_score": 60,
                "total_questions": 3,
                "unanswered_count": 1,
                "error_count": 1,
            }
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        context: Optional[Any] = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """
        Mock chat_completion 方法

        Args:
            messages: 消息列表
            context: 调用上下文
            **kwargs: 其他参数

        Returns:
            ChatCompletionResponse: 模拟响应
        """
        self.call_count += 1
        self.last_messages = messages
        self.last_kwargs = kwargs

        return ChatCompletionResponse(
            content=self.default_response,
            tokens_used=100,
            processing_time=0.1,
            model="mock-bailian-v3",
            request_id=f"mock-{uuid4()}",
            success=True,
            error_message=None,
        )

    def set_response(self, response: str) -> None:
        """
        设置自定义响应

        Args:
            response: JSON 字符串
        """
        self.default_response = response

    def set_failure(self, error_message: str = "Mock API Error") -> None:
        """
        设置失败响应

        Args:
            error_message: 错误信息
        """
        self.default_response = ""  # 会导致 JSON 解析失败

    def reset(self) -> None:
        """重置 Mock 状态"""
        self.call_count = 0
        self.last_messages = None
        self.last_kwargs = None
        self.default_response = self._get_default_correction_response()


@pytest.fixture
def mock_bailian_service():
    """
    提供 Mock BailianService fixture

    Returns:
        MockBailianService: 可配置的 Mock 服务
    """
    return MockBailianService()


# ========== 测试数据工厂 ==========


class CorrectAnswerFactory:
    """正确答案工厂"""

    @staticmethod
    def create_correction_item(
        question_number: int = 1,
        question_type: str = "选择题",
        is_unanswered: bool = False,
        error_type: Optional[str] = None,
        score: int = 100,
    ) -> Dict[str, Any]:
        """
        创建单题批改结果

        Args:
            question_number: 题号
            question_type: 题型
            is_unanswered: 是否未作答
            error_type: 错误类型
            score: 得分

        Returns:
            Dict: 批改项数据
        """
        return {
            "question_number": question_number,
            "question_type": question_type,
            "is_unanswered": is_unanswered,
            "student_answer": None if is_unanswered else "学生答案",
            "correct_answer": "正确答案",
            "error_type": error_type,
            "explanation": "批改说明",
            "knowledge_points": ["知识点1"],
            "score": score,
        }

    @staticmethod
    def create_correction_result(
        num_total: int = 3,
        num_errors: int = 1,
        num_unanswered: int = 1,
    ) -> str:
        """
        创建完整的批改 JSON 响应

        Args:
            num_total: 总题数
            num_errors: 错误题数
            num_unanswered: 未作答题数

        Returns:
            str: 批改结果 JSON 字符串
        """
        corrections = []

        # 添加未作答的题目
        for i in range(num_unanswered):
            corrections.append(
                CorrectAnswerFactory.create_correction_item(
                    question_number=i + 1,
                    is_unanswered=True,
                    error_type=None,
                    score=0,
                )
            )

        # 添加错误的题目
        for i in range(num_errors):
            corrections.append(
                CorrectAnswerFactory.create_correction_item(
                    question_number=i + num_unanswered + 1,
                    error_type="计算错误",
                    score=0,
                )
            )

        # 添加正确的题目
        for i in range(num_total - num_unanswered - num_errors):
            corrections.append(
                CorrectAnswerFactory.create_correction_item(
                    question_number=i + num_unanswered + num_errors + 1,
                    error_type=None,
                    score=100,
                )
            )

        result = {
            "corrections": corrections,
            "summary": f"共{num_total}题，错误{num_errors}题，未作答{num_unanswered}题",
            "overall_score": int(
                (num_total - num_errors - num_unanswered) * 100 / num_total
            ),
            "total_questions": num_total,
            "unanswered_count": num_unanswered,
            "error_count": num_errors,
        }

        return json.dumps(result)


@pytest.fixture
def correction_factory():
    """提供批改数据工厂"""
    return CorrectAnswerFactory()


# ========== 测试用例基础数据 ==========


@pytest.fixture
def test_user_id():
    """获取测试用户 ID"""
    return str(uuid4())


@pytest.fixture
def test_image_urls():
    """获取测试图片 URLs"""
    return [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
    ]


@pytest.fixture
def test_correction_result() -> HomeworkCorrectionResult:
    """
    获取测试用的批改结果对象

    Returns:
        HomeworkCorrectionResult: 批改结果
    """
    items = [
        QuestionCorrectionItem(
            question_number=1,
            question_type="选择题",
            is_unanswered=False,
            student_answer="B",
            correct_answer="A",
            error_type="理解错误",
            explanation="学生理解错了",
            knowledge_points=["知识点1"],
            score=0,
        ),
        QuestionCorrectionItem(
            question_number=2,
            question_type="填空题",
            is_unanswered=True,
            student_answer=None,
            correct_answer="42",
            error_type=None,
            explanation="未作答",
            knowledge_points=["知识点2"],
            score=0,
        ),
        QuestionCorrectionItem(
            question_number=3,
            question_type="解答题",
            is_unanswered=False,
            student_answer="正确",
            correct_answer="正确",
            error_type=None,
            explanation="答案正确",
            knowledge_points=["知识点3"],
            score=100,
        ),
    ]

    return HomeworkCorrectionResult(
        corrections=items,
        summary="总体不错",
        overall_score=60,
        total_questions=3,
        unanswered_count=1,
        error_count=1,
    )


# ========== 辅助工具 ==========


@pytest.fixture
def settings():
    """获取应用配置"""
    return get_settings()


@pytest.fixture
def mock_logger():
    """提供 Mock logger"""
    return MagicMock()


# ========== 异步测试标记 ==========


def pytest_collection_modifyitems(items):
    """
    自动为异步测试添加 @pytest.mark.asyncio 标记
    """
    for item in items:
        if "async" in item.keywords:
            item.add_marker(pytest.mark.asyncio)


# ========== 集成测试 Fixture ==========


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    创建测试用户

    Args:
        db_session: 数据库会话

    Returns:
        User: 测试用户对象
    """
    user_id = str(uuid4())
    phone = f"1{str(uuid4())[:10]}"  # 生成模拟手机号
    user = User(
        id=user_id,
        phone=phone,
        password_hash="hashed_password",
        name=f"测试用户_{user_id[:8]}",
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_session(db_session: AsyncSession, test_user: User) -> ChatSession:
    """
    创建测试会话

    Args:
        db_session: 数据库会话
        test_user: 测试用户

    Returns:
        ChatSession: 测试会话对象
    """
    session = ChatSession(
        user_id=test_user.id,
        title="测试会话",
        subject="math",
        grade_level="高一",
        status="active",
        question_count=0,
        total_tokens=0,
        context_enabled=True,
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
def test_ask_question_request() -> AskQuestionRequest:
    """
    创建测试的 AskQuestionRequest

    Returns:
        AskQuestionRequest: 提问请求对象
    """
    return AskQuestionRequest(
        content="如何求解二次方程？",
        question_type=QuestionType.PROBLEM_SOLVING,
        subject=SubjectType.MATH,
        topic="二次方程",
        difficulty_level=DifficultyLevel.MEDIUM,
        use_context=True,
        include_history=True,
        max_history=5,
    )


@pytest.fixture
def test_ask_question_with_images_request() -> AskQuestionRequest:
    """
    创建包含图片的 AskQuestionRequest

    Returns:
        AskQuestionRequest: 包含图片的提问请求
    """
    return AskQuestionRequest(
        content="请批改这份作业",
        question_type=QuestionType.HOMEWORK_HELP,
        subject=SubjectType.MATH,
        topic="作业批改",
        difficulty_level=DifficultyLevel.EASY,
        image_urls=[
            "https://example.com/homework1.jpg",
            "https://example.com/homework2.jpg",
        ],
        use_context=False,
        include_history=False,
    )


@pytest.fixture
def test_simple_ai_response() -> str:
    """
    创建简单的 AI 响应

    Returns:
        str: JSON 格式的 AI 响应
    """
    return json.dumps(
        {
            "answer": "二次方程可以通过以下方法求解...",
            "key_points": ["判别式", "求根公式"],
            "difficulty": "middle",
            "timestamp": "2025-11-05T10:00:00Z",
        }
    )


@pytest.fixture
def test_homework_correction_ai_response() -> str:
    """
    创建作业批改的 AI 响应

    Returns:
        str: 作业批改的 JSON 响应
    """
    return json.dumps(
        {
            "corrections": [
                {
                    "question_number": 1,
                    "question_type": "选择题",
                    "is_unanswered": False,
                    "student_answer": "B",
                    "correct_answer": "A",
                    "error_type": "理解错误",
                    "explanation": "学生错误地理解了题意",
                    "knowledge_points": ["集合论", "逻辑"],
                    "score": 0,
                },
                {
                    "question_number": 2,
                    "question_type": "解答题",
                    "is_unanswered": False,
                    "student_answer": "正确过程",
                    "correct_answer": "正确过程",
                    "error_type": None,
                    "explanation": "过程和答案都正确",
                    "knowledge_points": ["函数"],
                    "score": 100,
                },
            ],
            "summary": "整体表现不错，需要加强概念理解",
            "overall_score": 75,
            "total_questions": 2,
            "unanswered_count": 0,
            "error_count": 1,
        }
    )


@pytest.fixture
def mock_bailian_service_for_integration():
    """
    提供用于集成测试的 Mock BailianService

    Returns:
        MockBailianService: 配置好的 Mock 服务
    """
    service = MockBailianService()
    # 设置为返回简单的 AI 响应
    service.set_response(
        json.dumps(
            {
                "answer": "这是 AI 的回答",
                "key_points": ["知识点1"],
            }
        )
    )
    return service
