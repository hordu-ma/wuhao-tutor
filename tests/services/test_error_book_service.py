"""
错题本服务单元测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.error_book_service import ErrorBookService
from src.services.bailian_service import BailianService
from src.schemas.error_book import ErrorQuestionCreate, ReviewRecordCreate
from src.models.error_book import ErrorQuestion, ReviewRecord, MasteryStatus, SourceType


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_bailian_service():
    """模拟百炼服务"""
    service = AsyncMock(spec=BailianService)
    return service


@pytest.fixture
def error_book_service(mock_session, mock_bailian_service):
    """错题本服务实例"""
    return ErrorBookService(mock_session, mock_bailian_service)


@pytest.fixture
def sample_error_question():
    """示例错题数据"""
    return ErrorQuestion(
        id="test-error-id",
        user_id="test-user-id",
        subject="数学",
        question_content="解方程 2x + 3 = 7",
        student_answer="x = 1",
        correct_answer="x = 2",
        error_type="计算错误",
        knowledge_points=["一元一次方程"],
        difficulty_level=2,
        source_type=SourceType.MANUAL,
        mastery_status=MasteryStatus.LEARNING,
        review_count=0,
        correct_count=0
    )


class TestErrorBookService:
    """错题本服务测试类"""

    async def test_create_error_question_success(self, error_book_service, mock_session):
        """测试创建错题成功"""
        # 准备数据
        user_id = "test-user-id"
        error_data = ErrorQuestionCreate(
            subject="数学",
            question_content="解方程 2x + 3 = 7",
            student_answer="x = 1",
            correct_answer="x = 2",
            error_type="计算错误",
            knowledge_points=["一元一次方程"],
            difficulty_level=2
        )

        # 模拟repository创建
        mock_error_question = ErrorQuestion(
            id="test-error-id",
            user_id=user_id,
            **error_data.model_dump(),
            mastery_status=MasteryStatus.LEARNING,
            review_count=0,
            correct_count=0,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        error_book_service.repository.create = AsyncMock(return_value=mock_error_question)

        # 执行测试
        result = await error_book_service.create_error_question(user_id, error_data)

        # 验证结果
        assert result.subject == "数学"
        assert result.question_content == "解方程 2x + 3 = 7"
        assert result.mastery_status == "learning"
        
        # 验证调用
        error_book_service.repository.create.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_create_review_record_success(self, error_book_service, sample_error_question):
        """测试创建复习记录成功"""
        # 准备数据
        user_id = "test-user-id"
        review_data = ReviewRecordCreate(
            review_result="correct",
            score=100,
            time_spent=300,
            notes="复习完成，已掌握"
        )

        # 模拟repository方法
        error_book_service.repository.get_by_id = AsyncMock(return_value=sample_error_question)
        
        mock_review_record = ReviewRecord(
            id="test-review-id",
            error_question_id=sample_error_question.id,
            user_id=user_id,
            **review_data.model_dump(),
            reviewed_at=datetime.utcnow(),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        error_book_service.repository.create_review_record = AsyncMock(return_value=mock_review_record)

        # 执行测试
        result = await error_book_service.create_review_record(user_id, review_data)

        # 验证结果
        assert result.review_result == "correct"
        assert result.score == 100
        assert result.user_id == user_id

    async def test_create_review_record_invalid_question(self, error_book_service):
        """测试复习不存在的错题"""
        # 准备数据
        user_id = "test-user-id"
        review_data = ReviewRecordCreate(
            error_question_id="non-existent-id",
            review_result="correct",
            score=100
        )

        # 模拟repository返回None
        error_book_service.repository.get_by_id = AsyncMock(return_value=None)

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="错题不存在或无权限访问"):
            await error_book_service.create_review_record(user_id, review_data)

    async def test_get_review_recommendations(self, error_book_service, sample_error_question):
        """测试获取复习推荐"""
        # 准备数据
        user_id = "test-user-id"
        
        # 设置错题为逾期状态
        sample_error_question.next_review_at = datetime.utcnow() - timedelta(days=2)
        sample_error_question.overdue_days = 2
        
        # 模拟repository方法
        error_book_service.repository.get_review_recommendations = AsyncMock(
            return_value=[sample_error_question]
        )
        error_book_service.repository.get_weak_knowledge_points = AsyncMock(
            return_value=[
                {
                    "knowledge_point": "一元一次方程",
                    "error_count": 3,
                    "mastery_rate": 0.6,
                    "suggestion": "建议重点复习一元一次方程"
                }
            ]
        )

        # 执行测试
        result = await error_book_service.get_review_recommendations(user_id, 10)

        # 验证结果
        assert len(result.urgent_reviews) == 1
        assert result.urgent_reviews[0].error_question_id == sample_error_question.id
        assert result.urgent_reviews[0].overdue_days == 2
        assert len(result.weak_areas) == 1
        assert result.weak_areas[0].knowledge_point == "一元一次方程"

    async def test_collect_error_from_homework(self, error_book_service):
        """测试从作业收集错题"""
        # 准备数据
        user_id = "test-user-id"
        homework_submission_id = "homework-123"
        questions_data = [
            {
                "question": "2 + 2 = ?",
                "student_answer": "5",
                "correct_answer": "4",
                "score": 0,
                "subject": "数学",
                "knowledge_points": ["基础运算"]
            },
            {
                "question": "3 + 3 = ?",
                "student_answer": "6",
                "correct_answer": "6",
                "score": 100,  # 这道题不会被收集
                "subject": "数学",
                "knowledge_points": ["基础运算"]
            }
        ]

        # 模拟repository创建方法
        error_book_service.repository.create = AsyncMock(
            side_effect=lambda data: ErrorQuestion(
                id=f"error-{len(data['question_content'])}",
                **data
            )
        )

        # 执行测试
        result = await error_book_service.collect_error_from_homework(
            user_id, homework_submission_id, questions_data
        )

        # 验证结果
        assert len(result) == 1  # 只有得分<70的题目被收集
        error_book_service.repository.create.assert_called_once()

    def test_calculate_importance_score(self, error_book_service, sample_error_question):
        """测试重要性得分计算"""
        # 设置错题属性
        sample_error_question.is_overdue = True
        sample_error_question.overdue_days = 3
        sample_error_question.difficulty_level = 4
        sample_error_question.review_count = 1
        sample_error_question.knowledge_points = ["函数", "方程"]

        # 执行测试
        score = error_book_service._calculate_importance_score(sample_error_question)

        # 验证结果
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # 逾期且难度高的题目应该有较高分数

    def test_generate_daily_plan(self, error_book_service):
        """测试每日复习计划生成"""
        # 准备数据
        error_questions = [
            ErrorQuestion(
                id=f"error-{i}",
                user_id="test-user",
                subject=["数学", "物理", "化学"][i % 3],
                question_content=f"题目{i}",
                difficulty_level=2,
                mastery_status=MasteryStatus.LEARNING,
                review_count=0,
                correct_count=0
            )
            for i in range(15)
        ]

        # 执行测试
        plan = error_book_service._generate_daily_plan(error_questions)

        # 验证结果
        assert plan.target_count == 10  # 最多10题
        assert plan.estimated_time == 30  # 10题 * 3分钟
        assert len(plan.subjects) > 0
        assert len(plan.priority_items) == 10

    @pytest.mark.asyncio
    async def test_ai_error_analysis(self, error_book_service, mock_bailian_service):
        """测试AI错题分析"""
        # 模拟AI响应
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = '{"error_type": "计算错误", "knowledge_points": ["基础运算"], "suggestions": ["注意运算顺序"]}'
        
        mock_bailian_service.chat_completion = AsyncMock(return_value=mock_response)

        # 执行测试
        result = await error_book_service._analyze_error_with_ai(
            "2 + 2 = ?",
            "5",
            "4",
            "数学"
        )

        # 验证结果
        assert result is not None
        assert result["error_type"] == "计算错误"
        assert "基础运算" in result["knowledge_points"]
        assert len(result["suggestions"]) > 0

    def test_determine_error_type(self, error_book_service):
        """测试错误类型判断"""
        # 测试不同分数对应的错误类型
        test_cases = [
            (10, "理解错误"),
            (40, "方法错误"),
            (60, "计算错误"),
            (80, "表达错误")
        ]

        for score, expected_type in test_cases:
            question_data = {"score": score}
            result = error_book_service._determine_error_type(question_data)
            assert result == expected_type

    def test_estimate_difficulty(self, error_book_service):
        """测试难度估算"""
        # 测试不同分数对应的难度等级
        test_cases = [
            (90, 2),  # 简单
            (70, 3),  # 中等
            (50, 4),  # 困难
            (20, 5)   # 非常困难
        ]

        for score, expected_difficulty in test_cases:
            question_data = {"score": score}
            result = error_book_service._estimate_difficulty(question_data)
            assert result == expected_difficulty