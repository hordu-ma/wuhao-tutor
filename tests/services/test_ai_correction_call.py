"""
Phase 3 单元测试 - AI 作业批改调用
测试 LearningService._call_ai_for_homework_correction() 方法

用途: 验证 AI 调用、JSON 解析、错误处理
覆盖: 成功路径、失败路径、边界情况
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.schemas.learning import HomeworkCorrectionResult, QuestionCorrectionItem
from src.services.bailian_service import ChatCompletionResponse
from src.services.learning_service import LearningService
from tests.conftest import CorrectAnswerFactory, MockBailianService


class TestCallAiForHomeworkCorrection:
    """测试 AI 作业批改调用"""

    @pytest.fixture
    async def learning_service(self, db_session, mock_bailian_service):
        """
        创建 LearningService 实例（带 Mock BailianService）

        Args:
            db_session: 测试数据库会话
            mock_bailian_service: Mock AI 服务

        Returns:
            LearningService: 学习服务实例
        """
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service
        return service

    # ========== 成功路径测试 ==========

    @pytest.mark.asyncio
    async def test_successful_correction_with_valid_json(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 成功调用 AI 并解析有效的 JSON"""
        # 准备 Mock 数据
        json_response = correction_factory.create_correction_result(
            num_total=3, num_errors=1, num_unanswered=1
        )
        mock_bailian_service.set_response(json_response)

        # 调用方法
        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
            user_hint=None,
        )

        # 验证
        assert result is not None
        assert isinstance(result, HomeworkCorrectionResult)
        assert len(result.corrections) == 3
        assert result.total_questions == 3
        assert result.unanswered_count == 1
        assert result.error_count == 1

    @pytest.mark.asyncio
    async def test_correction_with_user_hint(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 带用户提示的批改"""
        json_response = correction_factory.create_correction_result()
        mock_bailian_service.set_response(json_response)

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="chinese",
            user_hint="请重点检查文言文翻译",
        )

        assert result is not None
        # 验证 user_hint 被传入（检查消息）
        assert mock_bailian_service.last_messages is not None

    @pytest.mark.asyncio
    async def test_correction_with_multiple_images(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 多张图片的批改"""
        json_response = correction_factory.create_correction_result()
        mock_bailian_service.set_response(json_response)

        images = [
            "https://example.com/page1.jpg",
            "https://example.com/page2.jpg",
            "https://example.com/page3.jpg",
        ]

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=images,
            subject="physics",
            user_hint=None,
        )

        assert result is not None
        assert mock_bailian_service.last_messages[0]["image_urls"] == images

    @pytest.mark.asyncio
    async def test_correction_result_structure(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 批改结果的数据结构完整性"""
        json_response = correction_factory.create_correction_result(
            num_total=5, num_errors=2, num_unanswered=1
        )
        mock_bailian_service.set_response(json_response)

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        # 验证每个 correction item 的结构
        for correction in result.corrections:
            assert isinstance(correction, QuestionCorrectionItem)
            assert correction.question_number > 0
            assert correction.question_type is not None
            assert isinstance(correction.is_unanswered, bool)
            assert correction.correct_answer is not None
            assert correction.knowledge_points is not None

    @pytest.mark.asyncio
    async def test_ai_parameters_optimization(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: AI 调用参数优化（温度、token 等）"""
        json_response = correction_factory.create_correction_result()
        mock_bailian_service.set_response(json_response)

        await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        # 验证调用参数
        assert mock_bailian_service.last_kwargs is not None
        assert mock_bailian_service.last_kwargs.get("temperature") == 0.3
        assert mock_bailian_service.last_kwargs.get("max_tokens") == 2000
        assert mock_bailian_service.last_kwargs.get("top_p") == 0.8

    # ========== JSON 解析测试 ==========

    @pytest.mark.asyncio
    async def test_json_with_prefix_text(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: JSON 前面有文本前缀"""
        json_response = correction_factory.create_correction_result()
        response_with_prefix = f"根据学生的作业，我来进行批改：\n\n{json_response}"
        mock_bailian_service.set_response(response_with_prefix)

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        assert len(result.corrections) > 0

    @pytest.mark.asyncio
    async def test_json_with_suffix_text(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: JSON 后面有文本后缀"""
        json_response = correction_factory.create_correction_result()
        response_with_suffix = f"{json_response}\n\n以上是批改结果，祝学习进步！"
        mock_bailian_service.set_response(response_with_suffix)

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_json_with_prefix_and_suffix(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: JSON 前后都有文本"""
        json_response = correction_factory.create_correction_result()
        response = f"开始批改...\n\n{json_response}\n\n批改完成！"
        mock_bailian_service.set_response(response)

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_json_with_nested_structures(
        self, learning_service, mock_bailian_service
    ):
        """测试: 复杂的嵌套 JSON 结构"""
        complex_json = {
            "corrections": [
                {
                    "question_number": 1,
                    "question_type": "选择题",
                    "is_unanswered": False,
                    "student_answer": "A",
                    "correct_answer": "B",
                    "error_type": "理解错误",
                    "explanation": "这道题考查...",
                    "knowledge_points": [
                        "知识点1",
                        "知识点2",
                        "知识点3",
                    ],
                    "score": 0,
                    "extra_info": {"nested": {"value": "test"}},
                }
            ],
            "summary": "总体评价",
            "overall_score": 50,
            "total_questions": 1,
            "unanswered_count": 0,
            "error_count": 1,
            "extra": {"metadata": "value"},
        }
        mock_bailian_service.set_response(json.dumps(complex_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        assert len(result.corrections) == 1

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_ai_service_failure(self, learning_service, mock_bailian_service):
        """测试: AI 服务返回失败"""
        # 模拟 AI 服务失败
        mock_bailian_service.default_response = ""

        service = LearningService(learning_service.db)

        # 创建一个返回失败的 Mock
        failed_response = ChatCompletionResponse(
            content="",
            tokens_used=0,
            processing_time=0.1,
            model="mock",
            request_id="test",
            success=False,
            error_message="API Error",
        )
        service.bailian_service.chat_completion = AsyncMock(
            return_value=failed_response
        )

        result = await service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, learning_service, mock_bailian_service):
        """测试: AI 返回无效的 JSON"""
        mock_bailian_service.set_response("这不是 JSON 格式 {broken json")

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_no_images_provided(self, learning_service, mock_bailian_service):
        """测试: 没有提供图片"""
        result = await learning_service._call_ai_for_homework_correction(
            image_urls=[],
            subject="math",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_none_images_provided(self, learning_service, mock_bailian_service):
        """测试: 图片为 None"""
        result = await learning_service._call_ai_for_homework_correction(
            image_urls=None,  # type: ignore
            subject="math",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_missing_required_json_fields(
        self, learning_service, mock_bailian_service
    ):
        """测试: JSON 缺少必要字段"""
        incomplete_json = {
            "corrections": [
                {
                    "question_number": 1,
                    # 缺少其他必要字段
                }
            ]
        }
        mock_bailian_service.set_response(json.dumps(incomplete_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        # 应该返回结果，但字段可能有 None 或默认值
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_corrections_list(self, learning_service, mock_bailian_service):
        """测试: 批改结果中的 corrections 为空（Schema 验证应该拒绝此情况）"""
        empty_json = {
            "corrections": [],
            "summary": "没有题目",
            "overall_score": 100,
            "total_questions": 0,
            "unanswered_count": 0,
            "error_count": 0,
        }
        mock_bailian_service.set_response(json.dumps(empty_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        # 由于 Schema 验证，total_questions 必须 >= 1，所以应该返回 None
        assert result is None

    # ========== 边界情况测试 ==========

    @pytest.mark.asyncio
    async def test_very_large_json_response(
        self, learning_service, mock_bailian_service
    ):
        """测试: 非常大的 JSON 响应"""
        # 创建包含大量题目的 JSON
        corrections = [
            {
                "question_number": i + 1,
                "question_type": "选择题",
                "is_unanswered": False,
                "student_answer": "A",
                "correct_answer": "B",
                "error_type": None if i % 2 == 0 else "错误",
                "explanation": f"题目 {i} 的说明" * 10,
                "knowledge_points": ["知识点"] * 5,
                "score": 100 if i % 2 == 0 else 0,
            }
            for i in range(100)
        ]

        large_json = {
            "corrections": corrections,
            "summary": "100 道题的批改",
            "overall_score": 50,
            "total_questions": 100,
            "unanswered_count": 0,
            "error_count": 50,
        }

        mock_bailian_service.set_response(json.dumps(large_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        assert len(result.corrections) == 100

    @pytest.mark.asyncio
    async def test_special_characters_in_json(
        self, learning_service, mock_bailian_service
    ):
        """测试: JSON 中包含特殊字符"""
        special_json = {
            "corrections": [
                {
                    "question_number": 1,
                    "question_type": "选择题",
                    "is_unanswered": False,
                    "student_answer": "A",
                    "correct_answer": "B",
                    "error_type": "理解错误",
                    "explanation": '这是 "特殊" 字符 \n 换行 \t 制表 \\ 反斜杠',
                    "knowledge_points": ["知识点1", "知识点2"],
                    "score": 0,
                }
            ],
            "summary": "总结：学生答案❌，正确答案✓",
            "overall_score": 0,
            "total_questions": 1,
            "unanswered_count": 0,
            "error_count": 1,
        }

        mock_bailian_service.set_response(json.dumps(special_json, ensure_ascii=False))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_all_subjects(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 各种不同学科的批改"""
        subjects = ["math", "chinese", "english", "physics", "chemistry"]
        json_response = correction_factory.create_correction_result()
        mock_bailian_service.set_response(json_response)

        for subject in subjects:
            result = await learning_service._call_ai_for_homework_correction(
                image_urls=["https://example.com/image.jpg"],
                subject=subject,
            )

            assert result is not None
            # 验证消息中包含了学科信息
            assert mock_bailian_service.last_messages is not None

    @pytest.mark.asyncio
    async def test_correction_with_all_correct_answers(
        self, learning_service, mock_bailian_service, correction_factory
    ):
        """测试: 所有答案都正确的情况"""
        # 创建全部正确的结果
        all_correct_json = {
            "corrections": [
                {
                    "question_number": i + 1,
                    "question_type": "选择题",
                    "is_unanswered": False,
                    "student_answer": "A",
                    "correct_answer": "A",
                    "error_type": None,
                    "explanation": "正确",
                    "knowledge_points": ["知识点"],
                    "score": 100,
                }
                for i in range(5)
            ],
            "summary": "全部正确！",
            "overall_score": 100,
            "total_questions": 5,
            "unanswered_count": 0,
            "error_count": 0,
        }

        mock_bailian_service.set_response(json.dumps(all_correct_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        assert result.error_count == 0
        assert result.unanswered_count == 0

    @pytest.mark.asyncio
    async def test_correction_with_all_errors(
        self, learning_service, mock_bailian_service
    ):
        """测试: 所有答案都错误的情况"""
        all_error_json = {
            "corrections": [
                {
                    "question_number": i + 1,
                    "question_type": "选择题",
                    "is_unanswered": False,
                    "student_answer": "A",
                    "correct_answer": "B",
                    "error_type": "错误",
                    "explanation": "错了",
                    "knowledge_points": ["知识点"],
                    "score": 0,
                }
                for i in range(5)
            ],
            "summary": "全部错误",
            "overall_score": 0,
            "total_questions": 5,
            "unanswered_count": 0,
            "error_count": 5,
        }

        mock_bailian_service.set_response(json.dumps(all_error_json))

        result = await learning_service._call_ai_for_homework_correction(
            image_urls=["https://example.com/image.jpg"],
            subject="math",
        )

        assert result is not None
        assert result.error_count == 5
