"""
Mock 数据工厂
用于创建外部服务的 Mock 响应数据
"""

import uuid
from typing import Any, Dict, List, Optional


class MockDataFactory:
    """Mock数据工厂"""

    @staticmethod
    def create_bailian_response(
        content: str = "这是AI的回答",
        finish_reason: str = "stop",
        **kwargs,
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
    def create_bailian_homework_review(
        score: float = 85.0,
        accuracy_rate: float = 0.85,
        **kwargs,
    ) -> Dict[str, Any]:
        """创建百炼AI作业批改响应数据"""
        return {
            "total_score": score,
            "accuracy_rate": accuracy_rate,
            "detailed_feedback": kwargs.get(
                "detailed_feedback",
                [
                    {
                        "question_number": 1,
                        "score": 10.0,
                        "is_correct": True,
                        "feedback": "回答正确",
                    },
                    {
                        "question_number": 2,
                        "score": 8.0,
                        "is_correct": False,
                        "feedback": "部分正确，需要注意...",
                    },
                ],
            ),
            "overall_comment": kwargs.get("overall_comment", "总体表现良好"),
            "knowledge_points": kwargs.get(
                "knowledge_points",
                [
                    {"name": "一元二次方程", "mastery": 0.9},
                    {"name": "因式分解", "mastery": 0.7},
                ],
            ),
        }

    @staticmethod
    def create_wechat_session_response(
        openid: str = "test_openid_123",
        session_key: str = "test_session_key",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建微信会话响应数据"""
        return {
            "openid": openid,
            "session_key": session_key,
            "unionid": kwargs.get("unionid"),
            "errcode": kwargs.get("errcode", 0),
            "errmsg": kwargs.get("errmsg", "ok"),
        }

    @staticmethod
    def create_wechat_user_info(
        nickname: str = "微信用户",
        avatar_url: str = "https://example.com/avatar.png",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建微信用户信息"""
        return {
            "nickName": nickname,
            "avatarUrl": avatar_url,
            "gender": kwargs.get("gender", 0),
            "city": kwargs.get("city", ""),
            "province": kwargs.get("province", ""),
            "country": kwargs.get("country", "中国"),
        }

    @staticmethod
    def create_ocr_response(
        text: str = "识别的文本内容",
        confidence: float = 0.95,
        **kwargs,
    ) -> Dict[str, Any]:
        """创建OCR识别响应数据"""
        return {
            "text": text,
            "confidence": confidence,
            "regions": kwargs.get(
                "regions",
                [
                    {
                        "text": text,
                        "confidence": confidence,
                        "bounding_box": {
                            "x": 10,
                            "y": 20,
                            "width": 100,
                            "height": 30,
                        },
                    }
                ],
            ),
        }

    @staticmethod
    def create_file_upload_response(
        file_url: str = "https://example.com/uploads/test.jpg",
        file_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """创建文件上传响应数据"""
        return {
            "file_id": file_id or str(uuid.uuid4()),
            "file_url": file_url,
            "file_name": kwargs.get("file_name", "test.jpg"),
            "file_size": kwargs.get("file_size", 1024),
            "content_type": kwargs.get("content_type", "image/jpeg"),
        }

    @staticmethod
    def create_jwt_token(
        user_id: str = "test_user_123",
        token_type: str = "access",
        **kwargs,
    ) -> str:
        """创建JWT Token（模拟）"""
        # 注意：这只是一个模拟token，不是真实的JWT
        return f"mock_{token_type}_token_for_{user_id}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def create_auth_response(
        user_id: str = "test_user_123",
        phone: str = "13800138000",
        **kwargs,
    ) -> Dict[str, Any]:
        """创建认证响应数据"""
        return {
            "access_token": MockDataFactory.create_jwt_token(user_id, "access"),
            "refresh_token": MockDataFactory.create_jwt_token(user_id, "refresh"),
            "token_type": "bearer",
            "expires_in": kwargs.get("expires_in", 3600),
            "user": {
                "id": user_id,
                "phone": phone,
                "name": kwargs.get("name", "测试用户"),
                "role": kwargs.get("role", "student"),
            },
        }
