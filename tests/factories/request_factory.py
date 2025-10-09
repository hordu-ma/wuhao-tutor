"""
API 请求数据工厂
"""

import uuid
from typing import Any, Dict, Optional


class RequestFactory:
    """API请求数据工厂"""

    @staticmethod
    def create_register_request(
        phone: str = "13800138001",
        password: str = "TestPass123!",
        name: str = "测试用户",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建注册请求数据"""
        return {
            "phone": phone,
            "password": password,
            "password_confirm": kwargs.get("password_confirm", password),
            "verification_code": kwargs.get(
                "verification_code", "123456"
            ),  # 添加验证码
            "name": name,
            "grade_level": kwargs.get("grade_level", "senior_1"),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["grade_level", "password_confirm", "verification_code"]
            },
        }

    @staticmethod
    def create_login_request(
        phone: str = "13800138000", password: str = "TestPass123!", **kwargs
    ) -> Dict[str, Any]:
        """创建登录请求数据"""
        return {
            "phone": phone,
            "password": password,
            **kwargs,
        }

    @staticmethod
    def create_wechat_login_request(
        code: str = "test_wechat_code", **kwargs
    ) -> Dict[str, Any]:
        """创建微信登录请求数据"""
        return {
            "code": code,
            "user_info": kwargs.get(
                "user_info",
                {
                    "nickName": "微信测试用户",
                    "avatarUrl": "https://example.com/avatar.png",
                },
            ),
            **{k: v for k, v in kwargs.items() if k != "user_info"},
        }

    @staticmethod
    def create_homework_submission_request(
        homework_id: Optional[str] = None,
        submission_title: str = "测试提交",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建作业提交请求数据"""
        return {
            "homework_id": homework_id or str(uuid.uuid4()),
            "submission_title": submission_title,
            "submission_note": kwargs.get("submission_note", "这是提交备注"),
            **{k: v for k, v in kwargs.items() if k != "submission_note"},
        }

    @staticmethod
    def create_homework_create_request(
        title: str = "测试作业",
        subject: str = "math",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建作业创建请求数据"""
        return {
            "title": title,
            "subject": subject,
            "homework_type": kwargs.get("homework_type", "daily"),
            "difficulty_level": kwargs.get("difficulty_level", "medium"),
            "grade_level": kwargs.get("grade_level", "senior_1"),
            "description": kwargs.get("description", "这是一个测试作业"),
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "homework_type",
                    "difficulty_level",
                    "grade_level",
                    "description",
                ]
            },
        }

    @staticmethod
    def create_question_request(
        content: str = "这是一个测试问题", **kwargs
    ) -> Dict[str, Any]:
        """创建问题请求数据"""
        return {
            "content": content,
            "subject": kwargs.get("subject", "math"),
            "grade_level": kwargs.get("grade_level", "senior_1"),
            **{k: v for k, v in kwargs.items() if k not in ["subject", "grade_level"]},
        }

    @staticmethod
    def create_password_reset_request(
        phone: str = "13800138000",
        verification_code: str = "123456",
        new_password: str = "NewPass123!",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建密码重置请求数据"""
        return {
            "phone": phone,
            "verification_code": verification_code,
            "new_password": new_password,
            "password_confirm": kwargs.get("password_confirm", new_password),
            **{k: v for k, v in kwargs.items() if k != "password_confirm"},
        }
