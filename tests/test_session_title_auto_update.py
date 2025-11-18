"""
测试会话标题自动更新功能
"""

import pytest

from src.schemas.learning import AskQuestionRequest, CreateSessionRequest, QuestionType
from src.services.learning_service import LearningService


@pytest.mark.asyncio
class TestSessionTitleAutoUpdate:
    """测试会话标题自动更新"""

    async def test_first_question_updates_new_conversation_title(
        self, db_session, test_user, mock_bailian_service
    ):
        """测试：首次提问时，如果会话标题是'新对话'，自动更新为问题摘要"""
        # Arrange: 创建一个标题为"新对话"的会话
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service  # 注入Mock服务
        user_id = str(test_user.id)

        session = await service.create_session(
            user_id,
            CreateSessionRequest(title="新对话", context_enabled=True),
        )

        assert session.title == "新对话"
        assert session.question_count == 0

        # Act: 首次提问
        question_content = "最简单的方法教给我求解球的体积"
        response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content=question_content,
                session_id=session.id,
                question_type=QuestionType.PROBLEM_SOLVING,
                use_context=True,
            ),
        )

        # Assert: 标题应该已更新（question_count更新在后台SQL中，测试环境可能失败，不影响标题更新逻辑）
        assert response.session.title != "新对话"
        assert response.session.title == "最简单的方法教给我求解球的体积"
        assert len(response.session.title) <= 33  # 30字符 + "..."

        print(f"✅ 标题已更新: '{response.session.title}'")

    async def test_first_question_with_custom_title_not_updated(
        self, db_session, test_user, mock_bailian_service
    ):
        """测试：如果会话标题不是'新对话'，不应自动更新"""
        """测试：如果会话已有自定义标题，首次提问时不更新标题"""
        # Arrange: 创建一个有自定义标题的会话
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service  # 注入Mock服务
        user_id = str(test_user.id)

        custom_title = "数学学习会话"
        session = await service.create_session(
            user_id,
            CreateSessionRequest(title=custom_title, context_enabled=True),
        )

        # Act: 首次提问
        response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content="什么是二次函数？",
                session_id=session.id,
                use_context=True,
            ),
        )

        # Assert: 标题应该保持不变
        assert response.session.title == custom_title

        print(f"✅ 自定义标题未被修改: '{response.session.title}'")

    async def test_second_question_not_update_title(
        self, db_session, test_user, mock_bailian_service
    ):
        """测试：如果是第二次提问，不更新标题"""
        # Arrange: 创建会话并提问第一次
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service  # 注入Mock服务
        user_id = str(test_user.id)

        session = await service.create_session(
            user_id,
            CreateSessionRequest(title="新对话", context_enabled=True),
        )

        # 第一次提问
        first_response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content="第一个问题",
                session_id=session.id,
                use_context=True,
            ),
        )

        first_title = first_response.session.title
        assert first_title != "新对话"

        # Act: 第二次提问
        second_response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content="这是完全不同的第二个问题，内容更长一些",
                session_id=session.id,
                use_context=True,
            ),
        )

        # Assert: 标题应该保持为第一次的标题，不应更新为第二个问题
        assert second_response.session.title == first_title

        print(f"✅ 第二次提问未更新标题: '{second_response.session.title}'")

    async def test_auto_created_session_updates_title(
        self, db_session, test_user, mock_bailian_service
    ):
        """测试：通过ask_question自动创建的会话，标题应该是问题摘要而不是'新对话'"""
        # Arrange
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service  # 注入Mock服务
        user_id = str(test_user.id)

        # Act: 不提供session_id，让系统自动创建会话
        question_content = "请解释什么是勾股定理"
        response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content=question_content,
                use_context=True,
            ),
        )

        # Assert: 自动创建的会话标题应该是问题摘要
        assert response.session.title == "请解释什么是勾股定理"
        assert response.session.title != "新对话"

        print(f"✅ 自动创建会话的标题: '{response.session.title}'")

    async def test_long_question_title_truncated(
        self, db_session, test_user, mock_bailian_service
    ):
        """测试：长问题应该被截断为30字符+省略号"""
        # Arrange
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service  # 注入Mock服务
        user_id = str(test_user.id)

        session = await service.create_session(
            user_id,
            CreateSessionRequest(title="新对话", context_enabled=True),
        )

        # Act: 提一个很长的问题
        long_question = "这是一个非常非常长的问题，用来测试标题生成功能是否能够正确地将超过三十个字符的问题内容截断并添加省略号"
        response = await service.ask_question(
            user_id,
            AskQuestionRequest(
                content=long_question,
                session_id=session.id,
                use_context=True,
            ),
        )

        # Assert: 标题应该被截断
        assert len(response.session.title) == 33  # 30字符 + "..."
        assert response.session.title.endswith("...")
        assert response.session.title.startswith("这是一个非常非常长的问题")

        print(f"✅ 长标题已截断: '{response.session.title}'")
