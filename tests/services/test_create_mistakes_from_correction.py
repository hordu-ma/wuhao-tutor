"""
Phase 3 单元测试 - 从批改结果创建错题
测试 LearningService._create_mistakes_from_correction() 方法

用途: 验证错题创建逻辑、字段映射、错误处理
覆盖: 各种批改结果组合、错误处理、边界情况
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.study import MistakeRecord
from src.repositories.mistake_repository import MistakeRepository
from src.schemas.learning import HomeworkCorrectionResult, QuestionCorrectionItem
from src.services.learning_service import LearningService


class TestCreateMistakesFromCorrection:
    """测试从批改结果创建错题"""

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

    # ========== 成功路径测试 ==========

    @pytest.mark.asyncio
    async def test_create_mistakes_with_errors_and_unanswered(
        self, learning_service, test_user_id, test_correction_result, test_image_urls
    ):
        """测试: 创建包含错误和未作答的错题"""
        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=test_correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        # 验证只创建了错误和未作答的题目
        # test_correction_result 有 3 题：1 个错误 + 1 个未作答 + 1 个正确
        # 应该只创建 2 个错题（错误 + 未作答）
        assert created_count == 2
        assert len(created_mistakes) == 2

    @pytest.mark.asyncio
    async def test_skip_correct_answers(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 跳过正确答案不创建错题"""
        # 创建全部正确的批改结果
        corrections = [
            QuestionCorrectionItem(
                question_number=1,
                question_type="选择题",
                is_unanswered=False,
                student_answer="A",
                correct_answer="A",
                error_type=None,  # 没有错误
                explanation="正确",
                knowledge_points=["知识点1"],
                score=100,
            ),
            QuestionCorrectionItem(
                question_number=2,
                question_type="填空题",
                is_unanswered=False,
                student_answer="42",
                correct_answer="42",
                error_type=None,
                explanation="正确",
                knowledge_points=["知识点2"],
                score=100,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="全部正确",
            overall_score=100,
            total_questions=2,
            unanswered_count=0,
            error_count=0,
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        # 应该没有创建任何错题
        assert created_count == 0
        assert len(created_mistakes) == 0

    @pytest.mark.asyncio
    async def test_create_for_unanswered_questions(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 为未作答的题目创建错题"""
        corrections = [
            QuestionCorrectionItem(
                question_number=1,
                question_type="解答题",
                is_unanswered=True,
                student_answer=None,
                correct_answer="完整解答过程",
                error_type=None,
                explanation="学生未作答",
                knowledge_points=["知识点1", "知识点2"],
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="有未作答",
            overall_score=0,
            total_questions=1,
            unanswered_count=1,
            error_count=0,
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        # 应该创建 1 个错题
        assert created_count == 1
        assert len(created_mistakes) == 1
        assert created_mistakes[0]["question_number"] == 1

    @pytest.mark.asyncio
    async def test_create_for_error_questions(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 为错误题目创建错题"""
        corrections = [
            QuestionCorrectionItem(
                question_number=2,
                question_type="选择题",
                is_unanswered=False,
                student_answer="B",
                correct_answer="A",
                error_type="理解错误",
                explanation="学生理解错了题意",
                knowledge_points=["知识点1"],
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="有错误",
            overall_score=0,
            total_questions=1,
            unanswered_count=0,
            error_count=1,
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        assert created_count == 1
        assert len(created_mistakes) == 1
        assert created_mistakes[0]["error_type"] == "理解错误"

    @pytest.mark.asyncio
    async def test_mistake_returned_data_structure(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 验证返回的错题数据结构"""
        corrections = [
            QuestionCorrectionItem(
                question_number=5,
                question_type="解答题",
                is_unanswered=False,
                student_answer="学生答案",
                correct_answer="正确答案",
                error_type="计算错误",
                explanation="第 3 步计算错了",
                knowledge_points=["导数", "积分"],
                score=30,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="需要加强计算",
            overall_score=30,
            total_questions=1,
            unanswered_count=0,
            error_count=1,
        )

        _, created_mistakes = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        # 验证返回的错题数据结构
        assert len(created_mistakes) == 1
        mistake_info = created_mistakes[0]

        # 验证关键字段
        assert "id" in mistake_info
        assert "question_number" in mistake_info
        assert "error_type" in mistake_info
        assert "title" in mistake_info

        assert mistake_info["question_number"] == 5
        assert mistake_info["error_type"] == "计算错误"
        assert "第5题" in mistake_info["title"]

    # ========== 多题批处理测试 ==========

    @pytest.mark.asyncio
    async def test_create_multiple_mistakes_batch(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 批量创建多个错题"""
        corrections = [
            QuestionCorrectionItem(
                question_number=i + 1,
                question_type="选择题" if i % 2 == 0 else "填空题",
                is_unanswered=i % 3 == 0,  # 每 3 个一个未作答
                student_answer=None if i % 3 == 0 else f"答案{i}",
                correct_answer=f"正确答案{i}",
                error_type="错误" if i % 2 != 0 and i % 3 != 0 else None,
                explanation=f"题目 {i} 的说明",
                knowledge_points=[f"知识点{i}"],
                score=0 if (i % 2 != 0 or i % 3 == 0) else 100,
            )
            for i in range(10)
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="10 道题混合情况",
            overall_score=50,
            total_questions=10,
            unanswered_count=4,  # 0, 3, 6, 9
            error_count=4,  # 奇数索引的
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        # 应该创建错误的题目和未作答的题目
        assert created_count > 0
        assert len(created_mistakes) == created_count

    @pytest.mark.asyncio
    async def test_create_mistakes_preserves_order(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 创建的错题保持顺序"""
        corrections = [
            QuestionCorrectionItem(
                question_number=i + 1,
                question_type="选择题",
                is_unanswered=True,
                student_answer=None,
                correct_answer=f"答案{i}",
                error_type=None,
                explanation="未作答",
                knowledge_points=["知识点"],
                score=0,
            )
            for i in range(5)
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="5 个未作答",
            overall_score=0,
            total_questions=5,
            unanswered_count=5,
            error_count=0,
        )

        _, created_mistakes = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        # 验证顺序
        for i, mistake in enumerate(created_mistakes):
            assert mistake["question_number"] == i + 1

    # ========== 字段处理测试 ==========

    @pytest.mark.asyncio
    async def test_title_generation_with_error_type(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 标题生成包含错误类型"""
        corrections = [
            QuestionCorrectionItem(
                question_number=3,
                question_type="选择题",
                is_unanswered=False,
                student_answer="A",
                correct_answer="B",
                error_type="概念混淆",
                explanation="混淆了两个概念",
                knowledge_points=["概念1"],
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="",
            overall_score=0,
            total_questions=1,
            unanswered_count=0,
            error_count=1,
        )

        _, created_mistakes = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        # 标题应该包含题号和错误类型
        assert "第3题" in created_mistakes[0]["title"]
        assert "概念混淆" in created_mistakes[0]["title"]

    @pytest.mark.asyncio
    async def test_title_without_error_type_for_unanswered(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 未作答题目的标题不包含错误类型"""
        corrections = [
            QuestionCorrectionItem(
                question_number=7,
                question_type="解答题",
                is_unanswered=True,
                student_answer=None,
                correct_answer="正确答案",
                error_type=None,
                explanation="未作答",
                knowledge_points=["知识点"],
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="",
            overall_score=0,
            total_questions=1,
            unanswered_count=1,
            error_count=0,
        )

        _, created_mistakes = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        # 标题应该只有题号，没有错误类型（因为 error_type 是 None）
        assert created_mistakes[0]["title"] == "第7题"

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_empty_corrections_list(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 空的 corrections 列表"""
        correction_result = HomeworkCorrectionResult(
            corrections=[],
            summary="没有题目",
            overall_score=100,
            total_questions=1,  # 至少要 1
            unanswered_count=0,
            error_count=0,
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        assert created_count == 0
        assert len(created_mistakes) == 0

    @pytest.mark.asyncio
    async def test_very_long_title_truncation(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 很长的标题被截断"""
        long_error_type = "A" * 300  # 非常长的错误类型

        corrections = [
            QuestionCorrectionItem(
                question_number=1,
                question_type="选择题",
                is_unanswered=False,
                student_answer="A",
                correct_answer="B",
                error_type=long_error_type,
                explanation="说明",
                knowledge_points=["知识点"],
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="",
            overall_score=0,
            total_questions=1,
            unanswered_count=0,
            error_count=1,
        )

        _, created_mistakes = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        # 标题应该被截断为 200 字符
        assert len(created_mistakes[0]["title"]) <= 200

    @pytest.mark.asyncio
    async def test_empty_knowledge_points(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 空的知识点列表"""
        corrections = [
            QuestionCorrectionItem(
                question_number=1,
                question_type="选择题",
                is_unanswered=False,
                student_answer="A",
                correct_answer="B",
                error_type="错误",
                explanation="说明",
                knowledge_points=[],  # 空列表
                score=0,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="",
            overall_score=0,
            total_questions=1,
            unanswered_count=0,
            error_count=1,
        )

        created_count, _ = await learning_service._create_mistakes_from_correction(
            user_id=test_user_id,
            correction_result=correction_result,
            subject="math",
            image_urls=test_image_urls,
        )

        assert created_count == 1

    @pytest.mark.asyncio
    async def test_all_question_types_supported(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 各种题型都被支持"""
        question_types = [
            "选择题",
            "填空题",
            "解答题",
            "简答题",
            "计算题",
            "证明题",
        ]

        for q_type in question_types:
            corrections = [
                QuestionCorrectionItem(
                    question_number=1,
                    question_type=q_type,
                    is_unanswered=False,
                    student_answer="答案",
                    correct_answer="正确答案",
                    error_type="错误",
                    explanation="说明",
                    knowledge_points=["知识点"],
                    score=0,
                ),
            ]

            correction_result = HomeworkCorrectionResult(
                corrections=corrections,
                summary="",
                overall_score=0,
                total_questions=1,
                unanswered_count=0,
                error_count=1,
            )

            created_count, _ = await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )

            assert created_count == 1, f"题型 {q_type} 应该被支持"

    @pytest.mark.asyncio
    async def test_different_subjects(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 不同学科的支持"""
        subjects = ["math", "chinese", "english", "physics", "chemistry", "biology"]

        for subject in subjects:
            corrections = [
                QuestionCorrectionItem(
                    question_number=1,
                    question_type="选择题",
                    is_unanswered=False,
                    student_answer="答案",
                    correct_answer="正确答案",
                    error_type="错误",
                    explanation="说明",
                    knowledge_points=["知识点"],
                    score=0,
                ),
            ]

            correction_result = HomeworkCorrectionResult(
                corrections=corrections,
                summary="",
                overall_score=0,
                total_questions=1,
                unanswered_count=0,
                error_count=1,
            )

            created_count, _ = await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject=subject,
                image_urls=test_image_urls,
            )

            assert created_count == 1, f"学科 {subject} 应该被支持"

    @pytest.mark.asyncio
    async def test_mixed_unanswered_and_errors(
        self, learning_service, test_user_id, test_image_urls
    ):
        """测试: 混合的未作答和错误题目"""
        corrections = [
            # 未作答
            QuestionCorrectionItem(
                question_number=1,
                question_type="选择题",
                is_unanswered=True,
                student_answer=None,
                correct_answer="A",
                error_type=None,
                explanation="未作答",
                knowledge_points=["知识点1"],
                score=0,
            ),
            # 错误
            QuestionCorrectionItem(
                question_number=2,
                question_type="填空题",
                is_unanswered=False,
                student_answer="42",
                correct_answer="41",
                error_type="计算错误",
                explanation="计算错了",
                knowledge_points=["知识点2"],
                score=0,
            ),
            # 正确（应该跳过）
            QuestionCorrectionItem(
                question_number=3,
                question_type="解答题",
                is_unanswered=False,
                student_answer="正确",
                correct_answer="正确",
                error_type=None,
                explanation="正确",
                knowledge_points=["知识点3"],
                score=100,
            ),
        ]

        correction_result = HomeworkCorrectionResult(
            corrections=corrections,
            summary="混合情况",
            overall_score=66,
            total_questions=3,
            unanswered_count=1,
            error_count=1,
        )

        created_count, created_mistakes = (
            await learning_service._create_mistakes_from_correction(
                user_id=test_user_id,
                correction_result=correction_result,
                subject="math",
                image_urls=test_image_urls,
            )
        )

        # 应该只创建 2 个（未作答 + 错误，不包括正确的）
        assert created_count == 2
        assert len(created_mistakes) == 2
        question_numbers = {m["question_number"] for m in created_mistakes}
        assert question_numbers == {1, 2}
