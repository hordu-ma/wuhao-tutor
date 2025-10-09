"""
测试数据工厂
提供测试数据的快速生成工具
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from unittest.mock import MagicMock

from src.models.user import User, UserRole, GradeLevel
from src.models.homework import (
    Homework,
    HomeworkSubmission,
    SubjectType,
    HomeworkType,
    DifficultyLevel,
    SubmissionStatus,
)
from src.models.learning import ChatSession, Question, Answer


class UserFactory:
    """用户数据工厂"""

    @staticmethod
    def create_user(
        user_id: Optional[str] = None,
        phone: str = "13800138000",
        name: str = "测试用户",
        password_hash: str = "hashed_password",
        role: UserRole = UserRole.STUDENT,
        grade_level: Optional[GradeLevel] = GradeLevel.SENIOR_1,
        **kwargs
    ) -> User:
        """创建测试用户"""
        user = User(
            id=user_id or str(uuid.uuid4()),
            phone=phone,
            name=name,
            password_hash=password_hash,
            role=role.value if isinstance(role, UserRole) else role,
            grade_level=grade_level.value if isinstance(grade_level, GradeLevel) else grade_level,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )
        return user

    @staticmethod
    def create_mock_user(
        user_id: str = "test_user_123",
        username: str = "testuser",
        **kwargs
    ) -> MagicMock:
        """创建Mock用户对象"""
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = username
        mock_user.phone = kwargs.get("phone", "13800138000")
        mock_user.name = kwargs.get("name", "测试用户")
        mock_user.role = kwargs.get("role", UserRole.STUDENT.value)
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()
        return mock_user


class HomeworkFactory:
    """作业数据工厂"""

    @staticmethod
    def create_homework(
        homework_id: Optional[str] = None,
        title: str = "数学练习题",
        subject: str = SubjectType.MATH.value,
        teacher_id: Optional[str] = None,
        homework_type: str = HomeworkType.DAILY.value,
        difficulty: str = DifficultyLevel.MEDIUM.value,
        **kwargs
    ) -> Homework:
        """创建测试作业"""
        homework = Homework(
            id=homework_id or str(uuid.uuid4()),
            title=title,
            subject=subject,
            teacher_id=teacher_id or str(uuid.uuid4()),
            homework_type=homework_type,
            difficulty=difficulty,
            description=kwargs.get("description", "这是一个测试作业"),
            total_score=kwargs.get("total_score", 100.0),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "total_score"]}
        )
        return homework

    @staticmethod
    def create_homework_submission(
        submission_id: Optional[str] = None,
        homework_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: str = SubmissionStatus.UPLOADED.value,
        **kwargs
    ) -> HomeworkSubmission:
        """创建测试作业提交"""
        submission = HomeworkSubmission(
            id=submission_id or str(uuid.uuid4()),
            homework_id=homework_id or str(uuid.uuid4()),
            student_id=student_id or str(uuid.uuid4()),
            status=status,
            submission_title=kwargs.get("submission_title", "测试作业提交"),
            submission_content=kwargs.get("submission_content", "这是作业内容"),
            total_score=kwargs.get("total_score"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["submission_title", "submission_content", "total_score"]}
        )
        return submission


class LearningFactory:
    """学习数据工厂"""

    @staticmethod
    def create_chat_session(
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        title: str = "测试会话",
        **kwargs
    ) -> ChatSession:
        """创建测试聊天会话"""
        session = ChatSession(
            id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )
        return session

    @staticmethod
    def create_question(
        question_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        content: str = "测试问题",
        **kwargs
    ) -> Question:
        """创建测试问题"""
        question = Question(
            id=question_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            content=content,
            created_at=datetime.utcnow(),
            **kwargs
        )
        return question

    @staticmethod
    def create_answer(
        answer_id: Optional[str] = None,
        question_id: Optional[str] = None,
        content: str = "测试答案",
        **kwargs
    ) -> Answer:
        """创建测试答案"""
        answer = Answer(
            id=answer_id or str(uuid.uuid4()),
            question_id=question_id or str(uuid.uuid4()),
            content=content,
            created_at=datetime.utcnow(),
            **kwargs
        )
        return answer


class RequestFactory:
    """API请求数据工厂"""

    @staticmethod
    def create_register_request(
        phone: str = "13800138001",
        password: str = "TestPass123!",
        name: str = "测试用户",
        **kwargs
    ) -> Dict[str, Any]:
        """创建注册请求数据"""
        return {
            "phone": phone,
            "password": password,
            "name": name,
            "email": kwargs.get("email", "test@example.com"),
            "grade_level": kwargs.get("grade_level", "senior_1"),
            **{k: v for k, v in kwargs.items() if k not in ["email", "grade_level"]}
        }

    @staticmethod
    def create_login_request(
        phone: str = "13800138000",
        password: str = "TestPass123!",
        **kwargs
    ) -> Dict[str, Any]:
        """创建登录请求数据"""
        return {
            "phone": phone,
            "password": password,
            **kwargs
        }

    @staticmethod
    def create_homework_submission_request(
        homework_id: Optional[str] = None,
        submission_title: str = "测试提交",
        submission_content: str = "这是提交内容",
        **kwargs
    ) -> Dict[str, Any]:
        """创建作业提交请求数据"""
        return {
            "homework_id": homework_id or str(uuid.uuid4()),
            "submission_title": submission_title,
            "submission_content": submission_content,
            **kwargs
        }

    @staticmethod
    def create_wechat_login_request(
        code: str = "test_wechat_code",
        **kwargs
    ) -> Dict[str, Any]:
        """创建微信登录请求数据"""
        return {
            "code": code,
            "user_info": kwargs.get("user_info", {
                "nickName": "微信测试用户",
                "avatarUrl": "https://example.com/avatar.png"
            }),
            **{k: v for k, v in kwargs.items() if k != "user_info"}
        }


class MockDataFactory:
    """Mock数据工厂"""

    @staticmethod
    def create_bailian_response(
        content: str = "这是AI的回答",
        finish_reason: str = "stop",
        **kwargs
    ) -> Dict[str, Any]:
        """创建百炼AI响应数据"""
        return {
            "output": {
                "text": content,
                "finish_reason": finish_reason,
            },
            "usage": {
                "input_tokens": kwargs.get("input_tokens", 10),
                "output_tokens": kwargs.get("output_tokens", 20),
                "total_tokens": kwargs.get("total_tokens", 30),
            },
            "request_id": kwargs.get("request_id", str(uuid.uuid4())),
        }

    @staticmethod
    def create_wechat_session_response(
        openid: str = "test_openid_123",
        session_key: str = "test_session_key",
        **kwargs
    ) -> Dict[str, Any]:
        """创建微信会话响应数据"""
        return {
            "openid": openid,
            "session_key": session_key,
            "unionid": kwargs.get("unionid"),
            "errcode": kwargs.get("errcode", 0),
            "errmsg": kwargs.get("errmsg", "ok"),
        }
