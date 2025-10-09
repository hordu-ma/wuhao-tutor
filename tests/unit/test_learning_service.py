"""
学习服务单元测试
测试聊天会话、问答等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.learning_service import LearningService
from tests.factories import LearningFactory, UserFactory, MockDataFactory


class TestLearningServiceSession:
    """学习会话测试"""

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """测试成功创建会话"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        user_id = "test_user_123"
        title = "数学学习"
        
        # Mock创建会话
        new_session = LearningFactory.create_chat_session(
            user_id=user_id,
            title=title
        )
        
        with patch.object(learning_service.session_repo, 'create', return_value=new_session):
            result = await learning_service.create_session(user_id, title)
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_session_by_id(self):
        """测试获取会话"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        session_id = "test_session_123"
        expected_session = LearningFactory.create_chat_session(session_id=session_id)
        
        with patch.object(learning_service.session_repo, 'get_by_id', return_value=expected_session):
            result = await learning_service.get_session(session_id)
            
            assert result is not None
            assert result.id == session_id

    @pytest.mark.asyncio
    async def test_get_user_sessions(self):
        """测试获取用户会话列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        user_id = "test_user_123"
        sessions = [
            LearningFactory.create_chat_session(user_id=user_id)
            for _ in range(3)
        ]
        
        with patch.object(learning_service.session_repo, 'filter', return_value=sessions):
            result = await learning_service.get_user_sessions(user_id)
            
            assert len(result) == 3


class TestLearningServiceQuestion:
    """问题处理测试"""

    @pytest.mark.asyncio
    async def test_ask_question_success(self):
        """测试提问成功"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        session_id = "test_session_123"
        user_id = "test_user_123"
        question_text = "什么是勾股定理?"
        
        # Mock创建问题
        new_question = LearningFactory.create_question(
            session_id=session_id,
            user_id=user_id,
            content=question_text
        )
        
        with patch.object(learning_service.question_repo, 'create', return_value=new_question):
            result = await learning_service.create_question(session_id, user_id, question_text)
            
            assert result is not None
            assert result.content == question_text

    @pytest.mark.asyncio
    async def test_get_session_questions(self):
        """测试获取会话问题列表"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        session_id = "test_session_123"
        questions = [
            LearningFactory.create_question(session_id=session_id)
            for _ in range(5)
        ]
        
        with patch.object(learning_service.question_repo, 'filter', return_value=questions):
            result = await learning_service.get_session_questions(session_id)
            
            assert len(result) == 5


class TestLearningServiceAnswer:
    """答案处理测试"""

    @pytest.mark.asyncio
    async def test_create_answer_success(self):
        """测试创建答案成功"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        question_id = "test_question_123"
        answer_text = "勾股定理是直角三角形两直角边的平方和等于斜边的平方"
        
        # Mock创建答案
        new_answer = LearningFactory.create_answer(
            question_id=question_id,
            content=answer_text
        )
        
        with patch.object(learning_service.answer_repo, 'create', return_value=new_answer):
            result = await learning_service.create_answer(question_id, answer_text)
            
            assert result is not None
            assert result.content == answer_text

    @pytest.mark.asyncio
    async def test_get_answer_by_question(self):
        """测试获取问题的答案"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        question_id = "test_question_123"
        expected_answer = LearningFactory.create_answer(question_id=question_id)
        
        with patch.object(learning_service.answer_repo, 'get_by_field', return_value=expected_answer):
            result = await learning_service.get_answer_by_question(question_id)
            
            assert result is not None


class TestLearningServiceAIIntegration:
    """AI集成测试"""

    @pytest.mark.asyncio
    async def test_generate_answer_with_ai(self):
        """测试使用AI生成答案"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        question_text = "什么是质数?"
        
        # Mock AI服务
        ai_response = MockDataFactory.create_bailian_response(
            content="质数是大于1且只能被1和自身整除的自然数"
        )
        
        with patch('src.services.bailian_service.get_bailian_service') as mock_bailian:
            mock_bailian_instance = MagicMock()
            mock_bailian_instance.chat_completion = AsyncMock(return_value=ai_response)
            mock_bailian.return_value = mock_bailian_instance
            
            result = await learning_service.generate_ai_answer(question_text)
            
            assert result is not None
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_answer_ai_error(self):
        """测试AI服务错误"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        question_text = "什么是质数?"
        
        # Mock AI服务抛出错误
        with patch('src.services.bailian_service.get_bailian_service') as mock_bailian:
            from src.core.exceptions import BailianServiceError
            mock_bailian_instance = MagicMock()
            mock_bailian_instance.chat_completion = AsyncMock(
                side_effect=BailianServiceError("AI服务不可用")
            )
            mock_bailian.return_value = mock_bailian_instance
            
            with pytest.raises(BailianServiceError):
                await learning_service.generate_ai_answer(question_text)


class TestLearningServiceHistory:
    """学习历史测试"""

    @pytest.mark.asyncio
    async def test_get_learning_history(self):
        """测试获取学习历史"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        user_id = "test_user_123"
        
        # Mock会话和问题
        sessions = [LearningFactory.create_chat_session(user_id=user_id)]
        questions = [LearningFactory.create_question() for _ in range(3)]
        
        with patch.object(learning_service.session_repo, 'filter', return_value=sessions):
            with patch.object(learning_service.question_repo, 'filter', return_value=questions):
                result = await learning_service.get_learning_history(user_id)
                
                assert result is not None


class TestLearningServiceValidation:
    """学习服务验证测试"""

    @pytest.mark.asyncio
    async def test_validate_question_length(self):
        """测试问题长度验证"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        # 过长的问题
        long_question = "什么" * 1000
        
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            await learning_service.validate_question(long_question)

    @pytest.mark.asyncio
    async def test_validate_empty_question(self):
        """测试空问题验证"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            await learning_service.validate_question("")


class TestLearningServiceEdgeCases:
    """学习服务边界情况测试"""

    @pytest.mark.asyncio
    async def test_create_session_with_empty_title(self):
        """测试创建空标题会话"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        user_id = "test_user_123"
        
        # Mock创建会话
        new_session = LearningFactory.create_chat_session(
            user_id=user_id,
            title="新会话"  # 应使用默认标题
        )
        
        with patch.object(learning_service.session_repo, 'create', return_value=new_session):
            result = await learning_service.create_session(user_id, "")
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_answer_nonexistent_question(self):
        """测试回答不存在的问题"""
        mock_db = AsyncMock(spec=AsyncSession)
        learning_service = LearningService(mock_db)
        
        # Mock问题不存在
        with patch.object(learning_service.question_repo, 'get_by_id', return_value=None):
            from src.core.exceptions import NotFoundError
            with pytest.raises(NotFoundError):
                await learning_service.create_answer("nonexistent_question", "答案")
