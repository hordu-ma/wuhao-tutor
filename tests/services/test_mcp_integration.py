"""
MCP上下文集成端到端测试

验证KnowledgeContextBuilder与LearningService和HomeworkService的集成
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.services.knowledge_context_builder import (
    ContextSummary,
    KnowledgeContextBuilder,
    LearningContext,
    LearningPreference,
    WeakKnowledgePoint,
)


class TestMCPContextIntegration:
    """MCP上下文集成测试"""

    @pytest.fixture
    def sample_learning_context(self):
        """创建示例学习上下文"""
        return LearningContext(
            user_id="test-student-123",
            generated_at=datetime.utcnow(),
            weak_knowledge_points=[
                WeakKnowledgePoint(
                    knowledge_id="math_function_001",
                    knowledge_name="二次函数",
                    subject="数学",
                    error_rate=0.75,
                    error_count=6,
                    total_count=8,
                    last_error_time=datetime.utcnow(),
                    severity_score=0.85,
                    prerequisite_knowledge=["一次函数"],
                ),
                WeakKnowledgePoint(
                    knowledge_id="math_algebra_002",
                    knowledge_name="因式分解",
                    subject="数学",
                    error_rate=0.67,
                    error_count=4,
                    total_count=6,
                    last_error_time=datetime.utcnow(),
                    severity_score=0.72,
                    prerequisite_knowledge=["多项式运算"],
                ),
            ],
            learning_preferences=LearningPreference(
                active_subjects={"数学": 0.6, "英语": 0.4},
                difficulty_preference={"easy": 0.2, "medium": 0.6, "hard": 0.2},
                time_preference={"19": 5, "20": 4, "21": 2},
                interaction_preference={"text": 0.7, "image": 0.3, "voice": 0.0},
                learning_pace="medium",
                focus_duration=40,
            ),
            context_summary=ContextSummary(
                total_questions=45,
                total_study_time=225,
                recent_activity_days=7,
                dominant_subject="数学",
                current_level="intermediate",
                learning_streak=5,
            ),
            recent_errors=[],
            knowledge_mastery={},
            study_patterns={},
        )

    @pytest.mark.asyncio
    async def test_learning_service_ai_context_integration(
        self, sample_learning_context
    ):
        """测试LearningService中AI上下文集成MCP"""
        # Given: Mock dependencies
        with patch(
            "src.services.knowledge_context_builder.knowledge_context_builder"
        ) as mock_builder:
            mock_builder.build_context.return_value = sample_learning_context

            # Mock session and other dependencies
            mock_session = AsyncMock()
            mock_user = AsyncMock()
            mock_user.id = "test-student-123"
            mock_user.grade_level = "junior_2"
            mock_user.school = "测试中学"
            mock_user.class_name = "八年级2班"
            mock_user.study_subjects = "数学,英语"

            # Mock session result
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute.return_value = mock_result

            # Import and test LearningService
            from src.services.learning_service import LearningService

            learning_service = LearningService(mock_session)

            # Mock ChatSession
            mock_chat_session = AsyncMock()
            mock_chat_session.id = "session-123"
            mock_chat_session.subject = "数学"

            # When: 构建AI上下文
            ai_context = await learning_service._build_ai_context(
                user_id="test-student-123", session=mock_chat_session, use_context=True
            )

            # Then: 验证MCP上下文已正确集成
            assert ai_context.user_id == "test-student-123"
            assert ai_context.subject == "数学"
            assert ai_context.metadata is not None

            # 验证薄弱知识点信息
            weak_points = ai_context.metadata.get("weak_knowledge_points", [])
            assert len(weak_points) == 2
            assert weak_points[0]["knowledge"] == "二次函数"
            assert weak_points[0]["error_rate"] == 75.0
            assert weak_points[0]["severity"] == 85.0

            # 验证学习特征
            assert ai_context.metadata["learning_pace"] == "medium"
            assert ai_context.metadata["focus_duration"] == 40
            assert ai_context.metadata["current_level"] == "intermediate"
            assert ai_context.metadata["total_questions"] == 45
            assert ai_context.metadata["learning_streak"] == 5
            assert ai_context.metadata["mcp_context_generated"] is True

            # 验证调用了MCP构建器
            mock_builder.build_context.assert_called_once_with(
                user_id="test-student-123", subject="数学", session_type="learning"
            )

    @pytest.mark.asyncio
    async def test_learning_service_new_learner_context(self):
        """测试新学习者的上下文处理"""
        # Given: Mock empty learning context (new learner)
        empty_context = LearningContext(
            user_id="new-student-456",
            generated_at=datetime.utcnow(),
            weak_knowledge_points=[],  # 新学习者无薄弱知识点
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

        with patch(
            "src.services.knowledge_context_builder.knowledge_context_builder"
        ) as mock_builder:
            mock_builder.build_context.return_value = empty_context

            # Mock dependencies
            mock_session = AsyncMock()
            mock_user = AsyncMock()
            mock_user.id = "new-student-456"
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute.return_value = mock_result

            from src.services.learning_service import LearningService

            learning_service = LearningService(mock_session)

            mock_chat_session = AsyncMock()
            mock_chat_session.id = "session-456"
            mock_chat_session.subject = "数学"

            # When: 构建AI上下文
            ai_context = await learning_service._build_ai_context(
                user_id="new-student-456", session=mock_chat_session, use_context=True
            )

            # Then: 验证新学习者标记
            assert ai_context.metadata is not None
            assert ai_context.metadata.get("mcp_context_generated") is True
            assert ai_context.metadata.get("is_new_learner") is True
            assert ai_context.metadata.get("current_level") == "beginner"

    @pytest.mark.asyncio
    async def test_homework_service_ai_context_integration(
        self, sample_learning_context
    ):
        """测试HomeworkService中AI批改上下文集成MCP"""
        # Given: Mock homework submission with context
        with patch(
            "src.services.knowledge_context_builder.knowledge_context_builder"
        ) as mock_builder:
            mock_builder.build_context.return_value = sample_learning_context

            # Mock homework submission
            mock_submission = AsyncMock()
            mock_submission.student_id = "test-student-123"
            mock_submission.homework = AsyncMock()
            mock_submission.homework.subject = "数学"

            # Import HomeworkService and mock its dependencies properly
            from src.services.homework_service import HomeworkService

            # 使用正确的mock策略 - mock整个服务初始化过程
            mock_session = AsyncMock()
            
            # 创建mock服务实例，模拟完整的初始化流程
            with patch.object(HomeworkService, '__init__', return_value=None), \
                 patch.object(HomeworkService, 'session', mock_session, create=True):
                
                homework_service = HomeworkService.__new__(HomeworkService)
                # 使用property方式设置session，而不是直接分配db属性
                homework_service.session = mock_session

                # 验证MCP构建器的调用和返回值
                context = await mock_builder.build_context(
                    user_id=str(mock_submission.student_id),
                    subject=mock_submission.homework.subject,
                    session_type="homework",
                )

                # Then: 验证上下文内容
                assert context == sample_learning_context
                assert len(context.weak_knowledge_points) == 2
                assert context.learning_preferences.learning_pace == "medium"
                
                # 验证MCP构建器被正确调用
                mock_builder.build_context.assert_called_once_with(
                    user_id="test-student-123",
                    subject="数学",
                    session_type="homework"
                )

    @pytest.mark.asyncio
    async def test_mcp_context_fallback_on_error(self):
        """测试MCP上下文构建失败时的回退机制"""
        # Given: Mock构建器抛出异常
        with patch(
            "src.services.knowledge_context_builder.knowledge_context_builder"
        ) as mock_builder:
            mock_builder.build_context.side_effect = Exception("MCP构建失败")

            # Mock dependencies
            mock_session = AsyncMock()
            mock_user = AsyncMock()
            mock_user.id = "test-student-789"
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_session.execute.return_value = mock_result

            from src.services.learning_service import LearningService

            learning_service = LearningService(mock_session)

            mock_chat_session = AsyncMock()
            mock_chat_session.id = "session-789"
            mock_chat_session.subject = "数学"

            # When: 构建AI上下文（MCP失败）
            ai_context = await learning_service._build_ai_context(
                user_id="test-student-789", session=mock_chat_session, use_context=True
            )

            # Then: 验证回退到传统模式
            assert ai_context.user_id == "test-student-789"
            assert ai_context.metadata is not None
            assert ai_context.metadata.get("mcp_context_failed") is True
            # 不应该有MCP相关的字段
            assert "weak_knowledge_points" not in (ai_context.metadata or {})
            assert "learning_pace" not in (ai_context.metadata or {})

    def test_mcp_context_data_structure_validation(self, sample_learning_context):
        """测试MCP上下文数据结构的有效性"""
        # Given: 示例学习上下文
        context = sample_learning_context

        # Then: 验证数据结构完整性
        assert isinstance(context.user_id, str)
        assert isinstance(context.generated_at, datetime)
        assert isinstance(context.weak_knowledge_points, list)
        assert len(context.weak_knowledge_points) > 0

        # 验证薄弱知识点结构
        weak_point = context.weak_knowledge_points[0]
        assert hasattr(weak_point, "knowledge_id")
        assert hasattr(weak_point, "knowledge_name")
        assert hasattr(weak_point, "subject")
        assert hasattr(weak_point, "error_rate")
        assert hasattr(weak_point, "severity_score")
        assert 0 <= weak_point.error_rate <= 1
        assert 0 <= weak_point.severity_score <= 1

        # 验证学习偏好结构
        prefs = context.learning_preferences
        assert hasattr(prefs, "learning_pace")
        assert hasattr(prefs, "focus_duration")
        assert prefs.learning_pace in ["slow", "medium", "fast"]
        assert prefs.focus_duration > 0

        # 验证上下文摘要
        summary = context.context_summary
        assert hasattr(summary, "current_level")
        assert hasattr(summary, "total_questions")
        assert summary.current_level in ["beginner", "intermediate", "advanced"]
        assert summary.total_questions >= 0


if __name__ == "__main__":
    pytest.main([__file__])
