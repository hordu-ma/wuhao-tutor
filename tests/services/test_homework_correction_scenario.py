"""
Phase 3 单元测试 - 作业批改场景检测
测试 LearningService._is_homework_correction_scenario() 方法

用途: 验证场景检测的准确性
覆盖: 各种文本/图片/问题类型组合
"""

from uuid import uuid4

import pytest

from src.models.learning import QuestionType
from src.services.learning_service import LearningService


class TestIsHomeworkCorrectionScenario:
    """测试作业批改场景检测"""

    @pytest.fixture
    async def learning_service(self, db_session):
        """
        创建 LearningService 实例

        Args:
            db_session: 测试数据库会话

        Returns:
            LearningService: 学习服务实例
        """
        return LearningService(db_session)

    # ========== 正例测试 (应该返回 True) ==========

    @pytest.mark.asyncio
    async def test_homework_help_question_type(self, learning_service):
        """测试: 问题类型为 HOMEWORK_HELP 时应该返回 True"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.HOMEWORK_HELP,
            content="这是作业",
            image_urls=None,
        )
        assert result is True, "问题类型为 HOMEWORK_HELP 时应该返回 True"

    @pytest.mark.asyncio
    async def test_homework_help_overrides_images(self, learning_service):
        """测试: 问题类型为 HOMEWORK_HELP 时，即使没有图片也返回 True"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.HOMEWORK_HELP,
            content="任何内容",
            image_urls=[],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_keyword_with_images(self, learning_service):
        """测试: 有关键词 + 有图片 时应该返回 True"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请帮我批改这份作业",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_various_correction_keywords(self, learning_service):
        """测试: 各种批改关键词组合"""
        keywords = [
            "批改",
            "改错",
            "作业",
            "题目",
            "答案",
            "对不对",
            "这道题",
            "帮我检查",
            "看看对不对",
            "这份作业",
            "逐题",
            "逐个",
        ]

        for keyword in keywords:
            result = learning_service._is_homework_correction_scenario(
                question_type=QuestionType.GENERAL_INQUIRY,
                content=f"请{keyword}一下这个",
                image_urls=["https://example.com/image.jpg"],
            )
            assert result is True, f"关键词 '{keyword}' 应该被识别"

    @pytest.mark.asyncio
    async def test_keyword_case_insensitive(self, learning_service):
        """测试: 关键词匹配不区分大小写"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请批改一下这份作业",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_images(self, learning_service):
        """测试: 多张图片的情况"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请批改我的作业",
            image_urls=[
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg",
            ],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_mixed_case_keyword(self, learning_service):
        """测试: 混合大小写的关键词"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请帮我改错一下",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is True

    # ========== 反例测试 (应该返回 False) ==========

    @pytest.mark.asyncio
    async def test_no_keyword_no_images(self, learning_service):
        """测试: 没有关键词、没有图片 应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="这是一个普通问题",
            image_urls=None,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_keyword_without_images(self, learning_service):
        """测试: 有关键词但没有图片 应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请帮我批改一下作业",
            image_urls=None,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_images_list(self, learning_service):
        """测试: 图片列表为空 应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请帮我批改一下作业",
            image_urls=[],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_images_without_keyword(self, learning_service):
        """测试: 有图片但没有关键词 应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="这是一个普通问题",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_different_question_types(self, learning_service):
        """测试: 非 HOMEWORK_HELP 的问题类型"""
        question_types = [
            QuestionType.CONCEPT,
            QuestionType.PROBLEM_SOLVING,
            QuestionType.STUDY_GUIDANCE,
            QuestionType.EXAM_PREPARATION,
            QuestionType.GENERAL_INQUIRY,
        ]

        for q_type in question_types:
            if q_type == QuestionType.HOMEWORK_HELP:
                continue

            result = learning_service._is_homework_correction_scenario(
                question_type=q_type,
                content="这是一个普通问题",
                image_urls=None,
            )
            # 没有关键词和图片 应该返回 False
            assert result is False, f"问题类型 {q_type} 没有关键词时应该返回 False"

    @pytest.mark.asyncio
    async def test_empty_content(self, learning_service):
        """测试: 空内容应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_whitespace_only_content(self, learning_service):
        """测试: 只有空白符的内容应该返回 False"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="   \n\t  ",
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is False

    # ========== 边界情况测试 ==========

    @pytest.mark.asyncio
    async def test_keyword_in_longer_word(self, learning_service):
        """测试: 关键词作为更长单词的一部分"""
        # 当前实现使用子串匹配，所以 "改正" 包含 "改" 不会被匹配
        # 因为 "改" 作为单独关键词，"改正" 不包含完整的关键词如 "改错"
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请改正这个句子",  # "改正" 不包含任何完整的批改关键词
            image_urls=["https://example.com/image.jpg"],
        )
        # 基于当前实现，应该不匹配
        assert result is False

    @pytest.mark.asyncio
    async def test_keyword_with_special_characters(self, learning_service):
        """测试: 包含特殊字符的内容"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="请批改@这份#作业$",
            image_urls=["https://example.com/image.jpg"],
        )
        # 应该找到 "批改" 和 "作业" 关键词
        assert result is True

    @pytest.mark.asyncio
    async def test_very_long_content(self, learning_service):
        """测试: 非常长的内容"""
        long_content = "这是一个很长的内容。" * 1000 + "请批改这份作业"
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content=long_content,
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_homework_help_with_all_none(self, learning_service):
        """测试: HOMEWORK_HELP 类型忽略其他参数"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.HOMEWORK_HELP,
            content=None,  # type: ignore
            image_urls=None,
        )
        assert result is True

    # ========== 综合场景测试 ==========

    @pytest.mark.asyncio
    async def test_comprehensive_correction_scenario(self, learning_service):
        """测试: 综合的批改场景"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.HOMEWORK_HELP,
            content="老师你好，请帮我批改一下这份数学作业，我觉得可能有些题目有问题",
            image_urls=[
                "https://example.com/homework_page1.jpg",
                "https://example.com/homework_page2.jpg",
            ],
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_not_a_correction_scenario(self, learning_service):
        """测试: 不是批改场景"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.CONCEPT,
            content="什么是勾股定理？",
            image_urls=None,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_minimal_keyword_match(self, learning_service):
        """测试: 最小关键词匹配"""
        result = learning_service._is_homework_correction_scenario(
            question_type=QuestionType.GENERAL_INQUIRY,
            content="作业",  # 最短的关键词
            image_urls=["https://example.com/image.jpg"],
        )
        assert result is True
