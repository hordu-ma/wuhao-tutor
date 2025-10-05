"""
KnowledgeContextBuilder 服务单元测试

测试用户学情上下文构建的各个核心功能
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.knowledge_context_builder import (
    ContextSummary,
    KnowledgeContextBuilder,
    LearningContext,
    LearningPreference,
    WeakKnowledgePoint,
)


class TestKnowledgeContextBuilder:
    """KnowledgeContextBuilder 测试套件"""

    @pytest.fixture
    def builder(self):
        """创建测试用的构建器实例"""
        return KnowledgeContextBuilder()

    @pytest.fixture
    def mock_session(self):
        """创建模拟的数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def sample_user_id(self):
        """测试用户ID"""
        return "test-user-123"

    @pytest.mark.asyncio
    async def test_build_context_basic(self, builder, sample_user_id):
        """测试基础上下文构建功能"""
        # Given: 一个用户ID

        # When: 构建用户上下文
        context = await builder.build_context(sample_user_id)

        # Then: 应该返回完整的学习上下文
        assert isinstance(context, LearningContext)
        assert context.user_id == sample_user_id
        assert context.generated_at is not None
        assert isinstance(context.weak_knowledge_points, list)
        assert isinstance(context.learning_preferences, LearningPreference)
        assert isinstance(context.context_summary, ContextSummary)

    @pytest.mark.asyncio
    async def test_build_context_with_subject_filter(self, builder, sample_user_id):
        """测试指定学科的上下文构建"""
        # Given: 用户ID和指定学科
        subject = "数学"

        # When: 构建特定学科的上下文
        context = await builder.build_context(sample_user_id, subject=subject)

        # Then: 应该返回针对该学科的上下文
        assert context.user_id == sample_user_id
        # 注意：当前实现返回空数据，后续实现后需要验证学科筛选逻辑

    @pytest.mark.asyncio
    async def test_build_context_different_session_types(self, builder, sample_user_id):
        """测试不同会话类型的上下文构建"""
        # Given: 不同的会话类型

        # When & Then: 测试学习类型会话
        learning_context = await builder.build_context(
            sample_user_id, session_type="learning"
        )
        assert learning_context.user_id == sample_user_id

        # When & Then: 测试作业类型会话
        homework_context = await builder.build_context(
            sample_user_id, session_type="homework"
        )
        assert homework_context.user_id == sample_user_id

    def test_calculate_time_decay_weight(self, builder):
        """测试时间衰减权重计算"""
        # Given: 不同时间的时间戳
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # When: 计算时间衰减权重
        weight_now = builder._calculate_time_decay_weight(now)
        weight_yesterday = builder._calculate_time_decay_weight(yesterday)
        weight_week = builder._calculate_time_decay_weight(week_ago)
        weight_month = builder._calculate_time_decay_weight(month_ago)

        # Then: 权重应该随时间递减
        assert abs(weight_now - 1.0) < 0.01  # 当前时间权重接近最高
        assert weight_yesterday < weight_now
        assert weight_week < weight_yesterday
        assert weight_month < weight_week
        assert weight_month >= 0.1  # 最小权重不低于0.1

    def test_calculate_severity_score(self, builder):
        """测试薄弱知识点严重程度评分计算"""
        # Given: 不同的错误率、错误次数和时间权重
        test_cases = [
            (0.8, 5, 1.0, "高错误率+高错误次数+近期"),
            (0.3, 2, 0.5, "低错误率+低错误次数+较远"),
            (0.9, 10, 0.2, "高错误率+高错误次数+很远"),
        ]

        # When & Then: 计算并验证评分
        for error_rate, error_count, time_weight, desc in test_cases:
            score = builder._calculate_severity_score(
                error_rate, error_count, time_weight
            )

            # 评分应该在0-1范围内
            assert 0 <= score <= 1, f"评分超出范围: {desc}"

            # 高错误率应该有更高的评分
            if error_rate > 0.7:
                assert score > 0.3, f"高错误率应该有较高评分: {desc}"

    def test_weak_knowledge_point_model(self):
        """测试薄弱知识点数据模型"""
        # Given: 薄弱知识点数据
        weak_point = WeakKnowledgePoint(
            knowledge_id="math-001",
            knowledge_name="二次函数",
            subject="数学",
            error_rate=0.75,
            error_count=6,
            total_count=8,
            last_error_time=datetime.utcnow(),
            severity_score=0.85,
            prerequisite_knowledge=["一次函数", "函数概念"],
        )

        # Then: 模型应该正确验证数据
        assert weak_point.knowledge_id == "math-001"
        assert weak_point.error_rate == 0.75
        assert 0 <= weak_point.error_rate <= 1
        assert weak_point.error_count >= 0
        assert len(weak_point.prerequisite_knowledge) == 2

    def test_learning_preference_model(self):
        """测试学习偏好数据模型"""
        # Given: 学习偏好数据
        preference = LearningPreference(
            active_subjects={"数学": 0.4, "英语": 0.3, "语文": 0.3},
            difficulty_preference={"easy": 0.2, "medium": 0.5, "hard": 0.3},
            time_preference={"morning": 2, "afternoon": 3, "evening": 5},
            interaction_preference={"text": 0.6, "image": 0.3, "voice": 0.1},
            learning_pace="medium",
            focus_duration=45,
        )

        # Then: 模型应该正确存储数据
        assert sum(preference.active_subjects.values()) == 1.0
        assert preference.learning_pace in ["slow", "medium", "fast"]
        assert preference.focus_duration > 0

    def test_context_summary_model(self):
        """测试上下文摘要数据模型"""
        # Given: 上下文摘要数据
        summary = ContextSummary(
            total_questions=150,
            total_study_time=480,  # 8小时
            recent_activity_days=7,
            dominant_subject="数学",
            current_level="intermediate",
            learning_streak=5,
        )

        # Then: 模型应该正确验证数据
        assert summary.total_questions >= 0
        assert summary.total_study_time >= 0
        assert summary.recent_activity_days >= 0
        assert summary.current_level in ["beginner", "intermediate", "advanced"]
        assert summary.learning_streak >= 0

    def test_learning_context_model(self):
        """测试完整学习上下文数据模型"""
        # Given: 完整的学习上下文数据
        context = LearningContext(
            user_id="test-user",
            generated_at=datetime.utcnow(),
            weak_knowledge_points=[],
            learning_preferences=LearningPreference(
                active_subjects={},
                difficulty_preference={},
                time_preference={},
                interaction_preference={},
                learning_pace="medium",
                focus_duration=30,
            ),
            context_summary=ContextSummary(
                total_questions=0,
                total_study_time=0,
                recent_activity_days=0,
                dominant_subject="数学",
                current_level="beginner",
                learning_streak=0,
            ),
            recent_errors=[],
            knowledge_mastery={},
            study_patterns={},
        )

        # Then: 完整上下文应该包含所有必需字段
        assert context.user_id == "test-user"
        assert isinstance(context.generated_at, datetime)
        assert isinstance(context.weak_knowledge_points, list)
        assert isinstance(context.learning_preferences, LearningPreference)
        assert isinstance(context.context_summary, ContextSummary)
        assert isinstance(context.recent_errors, list)
        assert isinstance(context.knowledge_mastery, dict)
        assert isinstance(context.study_patterns, dict)


class TestKnowledgeContextBuilderPrivateMethods:
    """测试 KnowledgeContextBuilder 的私有方法"""

    @pytest.fixture
    def builder(self):
        return KnowledgeContextBuilder()

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_analyze_weak_knowledge_points_empty_result(
        self, builder, mock_session
    ):
        """测试薄弱知识点分析 - 空结果情况"""
        # Given: 没有历史数据的用户
        user_id = "new-user"

        # When: 分析薄弱知识点
        result = await builder._analyze_weak_knowledge_points(
            mock_session, user_id, None
        )

        # Then: 应该返回空列表
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_extract_learning_preferences_default_values(
        self, builder, mock_session
    ):
        """测试学习偏好提取 - 默认值情况"""
        # Given: 新用户
        user_id = "new-user"

        # When: 提取学习偏好
        result = await builder._extract_learning_preferences(
            mock_session, user_id, None
        )

        # Then: 应该返回默认偏好设置
        assert isinstance(result, LearningPreference)
        assert result.learning_pace == "medium"
        assert result.focus_duration == 30
        assert isinstance(result.active_subjects, dict)

    @pytest.mark.asyncio
    async def test_generate_context_summary_default_values(self, builder, mock_session):
        """测试上下文摘要生成 - 默认值情况"""
        # Given: 新用户
        user_id = "new-user"

        # When: 生成上下文摘要
        result = await builder._generate_context_summary(mock_session, user_id, None)

        # Then: 应该返回默认摘要
        assert isinstance(result, ContextSummary)
        assert result.total_questions == 0
        assert result.current_level == "beginner"
        assert result.dominant_subject == "数学"

    @pytest.mark.asyncio
    async def test_get_recent_errors_empty(self, builder, mock_session):
        """测试获取最近错题 - 空结果"""
        # Given: 没有错题的用户
        user_id = "good-student"

        # When: 获取最近错题
        result = await builder._get_recent_errors(mock_session, user_id, None)

        # Then: 应该返回空列表
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_calculate_knowledge_mastery_empty(self, builder, mock_session):
        """测试知识点掌握度计算 - 空结果"""
        # Given: 新用户
        user_id = "new-user"

        # When: 计算知识点掌握度
        result = await builder._calculate_knowledge_mastery(mock_session, user_id, None)

        # Then: 应该返回空字典
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_analyze_study_patterns_empty(self, builder, mock_session):
        """测试学习模式分析 - 空结果"""
        # Given: 新用户
        user_id = "new-user"

        # When: 分析学习模式
        result = await builder._analyze_study_patterns(mock_session, user_id, None)

        # Then: 应该返回空字典
        assert isinstance(result, dict)
        assert len(result) == 0


# 参数化测试数据
@pytest.mark.parametrize(
    "time_decay_factor,expected_min_weight",
    [
        (0.1, 0.1),  # 默认衰减因子
        (0.05, 0.1),  # 较小衰减因子
        (0.2, 0.1),  # 较大衰减因子
    ],
)
def test_time_decay_factor_configuration(time_decay_factor, expected_min_weight):
    """测试不同时间衰减因子配置"""
    builder = KnowledgeContextBuilder()
    builder.time_decay_factor = time_decay_factor

    # 测试很久以前的时间
    old_time = datetime.utcnow() - timedelta(days=365)
    weight = builder._calculate_time_decay_weight(old_time)

    assert weight >= expected_min_weight


@pytest.mark.parametrize("weak_threshold", [0.5, 0.6, 0.7])
def test_weak_threshold_configuration(weak_threshold):
    """测试不同薄弱知识点阈值配置"""
    builder = KnowledgeContextBuilder()
    builder.weak_threshold = weak_threshold

    assert builder.weak_threshold == weak_threshold
    assert 0 < builder.weak_threshold < 1


if __name__ == "__main__":
    pytest.main([__file__])
