"""
学习相关数据工厂
"""

import uuid
from datetime import datetime
from typing import Optional

from src.models.learning import Answer, ChatSession, Question


class ChatSessionFactory:
    """聊天会话数据工厂"""

    @staticmethod
    def create_chat_session(
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        title: str = "测试会话",
        **kwargs,
    ) -> ChatSession:
        """创建测试聊天会话"""
        session = ChatSession(
            id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs,
        )
        return session


class QuestionFactory:
    """问题数据工厂"""

    @staticmethod
    def create_question(
        question_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        content: str = "测试问题",
        **kwargs,
    ) -> Question:
        """创建测试问题"""
        question = Question(
            id=question_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            content=content,
            created_at=datetime.utcnow(),
            **kwargs,
        )
        return question


class AnswerFactory:
    """答案数据工厂"""

    @staticmethod
    def create_answer(
        answer_id: Optional[str] = None,
        question_id: Optional[str] = None,
        content: str = "测试答案",
        **kwargs,
    ) -> Answer:
        """创建测试答案"""
        answer = Answer(
            id=answer_id or str(uuid.uuid4()),
            question_id=question_id or str(uuid.uuid4()),
            content=content,
            created_at=datetime.utcnow(),
            **kwargs,
        )
        return answer
