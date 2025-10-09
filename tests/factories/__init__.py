"""
测试数据工厂模块
提供基于 factory-boy 的测试数据生成工具
"""

from .homework_factory import (
    HomeworkFactory,
    HomeworkModelFactory,
    HomeworkSubmissionFactory,
    HomeworkSubmissionModelFactory,
)
from .learning_factory import AnswerFactory, ChatSessionFactory, QuestionFactory
from .mock_factory import MockDataFactory
from .request_factory import RequestFactory
from .user_factory import UserFactory, UserModelFactory

__all__ = [
    # User factories
    "UserFactory",
    "UserModelFactory",
    # Homework factories
    "HomeworkFactory",
    "HomeworkSubmissionFactory",
    "HomeworkModelFactory",
    "HomeworkSubmissionModelFactory",
    # Learning factories
    "ChatSessionFactory",
    "QuestionFactory",
    "AnswerFactory",
    # Request factories
    "RequestFactory",
    # Mock factories
    "MockDataFactory",
]
