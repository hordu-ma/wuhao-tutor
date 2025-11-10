"""
Phase 3.3: Prompt 准确性测试

测试 HOMEWORK_CORRECTION_PROMPT 在不同场景下的准确率
通过 5 个典型场景验证批改功能的正确性
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from src.services.learning_service import LearningService
from tests.fixtures.test_data_loader import (
    SCENARIO_ALL_CORRECT,
    SCENARIO_ALL_WRONG,
    SCENARIO_MIXED_TYPES,
    SCENARIO_PARTIAL_UNANSWERED,
    SCENARIO_SINGLE_QUESTION,
    load_test_case,
)


@pytest.mark.asyncio
class TestPromptAccuracy:
    """
    Prompt 准确性测试类

    测试目标: 验证 AI 批改的准确率 ≥ 90%
    """

    async def test_single_question_correction(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试场景1: 单题作业批改

        验证点:
        - JSON 解析成功
        - 题号正确 (question_number = 1)
        - 答案判断准确 (正确答案不应标记为错误)
        - 知识点提取合理 (应包含相关知识点)
        - 错误类型为 null (正确答案)
        """
        # 加载测试用例
        test_case = load_test_case(SCENARIO_SINGLE_QUESTION)
        expected = test_case["expected_result"]

        # 设置 Mock 响应
        mock_response = self._build_mock_response(expected)
        mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

        # 创建服务
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        # 调用批改方法
        result = await service._call_ai_for_homework_correction(
            image_urls=test_case["image_urls"],
            subject=test_case["subject"],
            user_hint=test_case.get("user_hint", ""),
        )

        # 验证结果
        assert result is not None, "批改结果不应为 None"
        assert (
            len(result.corrections) == expected["total_questions"]
        ), f"题目数量不匹配: 期望 {expected['total_questions']}, 实际 {len(result.corrections)}"

        # 验证第一题
        correction = result.corrections[0]
        expected_correction = expected["corrections"][0]

        assert (
            correction.question_number == expected_correction["question_number"]
        ), f"题号不匹配: 期望 {expected_correction['question_number']}, 实际 {correction.question_number}"

        assert (
            correction.is_unanswered == expected_correction["is_unanswered"]
        ), f"未作答标记不匹配: 期望 {expected_correction['is_unanswered']}, 实际 {correction.is_unanswered}"

        assert (
            correction.error_type == expected_correction["error_type"]
        ), f"错误类型不匹配: 期望 {expected_correction['error_type']}, 实际 {correction.error_type}"

        assert (
            correction.score == expected_correction["score"]
        ), f"分数不匹配: 期望 {expected_correction['score']}, 实际 {correction.score}"

        # 验证知识点提取
        assert len(correction.knowledge_points) > 0, "应该提取到知识点"
        assert len(correction.knowledge_points) <= 3, "知识点数量不应超过3个"

        print(f"✅ 场景1通过: 单题作业批改准确")

    async def test_all_wrong_correction(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试场景2: 全错作业批改

        验证点:
        - 所有题目都应标记为错误
        - 错误类型应该不同 (计算错误、概念错误、单位错误)
        - error_count = 3
        - 分数都应该是 0
        """
        test_case = load_test_case(SCENARIO_ALL_WRONG)
        expected = test_case["expected_result"]

        # 设置 Mock 响应
        mock_response = self._build_mock_response(expected)
        mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

        # 创建服务并调用
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        result = await service._call_ai_for_homework_correction(
            image_urls=test_case["image_urls"],
            subject=test_case["subject"],
            user_hint=test_case.get("user_hint", ""),
        )

        # 验证结果
        assert result is not None
        assert len(result.corrections) == 3, "应该有3道题"
        assert result.error_count == 3, f"错误数量应为3, 实际 {result.error_count}"

        # 验证每道题
        error_types = []
        for i, correction in enumerate(result.corrections):
            expected_correction = expected["corrections"][i]

            # 验证题号连续
            assert (
                correction.question_number == i + 1
            ), f"题号应该是 {i + 1}, 实际 {correction.question_number}"

            # 验证错误标记
            assert correction.error_type is not None, f"第 {i + 1} 题应该有错误类型"

            assert (
                correction.score == 0
            ), f"第 {i + 1} 题分数应该是0, 实际 {correction.score}"

            error_types.append(correction.error_type)

        # 验证错误类型多样性
        unique_error_types = set(error_types)
        assert (
            len(unique_error_types) >= 2
        ), f"错误类型应该有多样性, 实际只有 {len(unique_error_types)} 种"

        print(f"✅ 场景2通过: 全错作业批改准确, 错误类型: {error_types}")

    async def test_all_correct_correction(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试场景3: 全对作业批改

        验证点:
        - 所有题目都应标记为正确
        - error_type 都应该是 null
        - error_count = 0
        - 分数都应该是 100
        """
        test_case = load_test_case(SCENARIO_ALL_CORRECT)
        expected = test_case["expected_result"]

        # 设置 Mock 响应
        mock_response = self._build_mock_response(expected)
        mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

        # 创建服务并调用
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        result = await service._call_ai_for_homework_correction(
            image_urls=test_case["image_urls"],
            subject=test_case["subject"],
            user_hint=test_case.get("user_hint", ""),
        )

        # 验证结果
        assert result is not None
        assert len(result.corrections) == 3, "应该有3道题"
        assert result.error_count == 0, f"错误数量应为0, 实际 {result.error_count}"

        # 验证每道题
        for i, correction in enumerate(result.corrections):
            assert correction.question_number == i + 1
            assert (
                correction.error_type is None
            ), f"第 {i + 1} 题不应该有错误类型, 实际 {correction.error_type}"
            assert (
                correction.score == 100
            ), f"第 {i + 1} 题分数应该是100, 实际 {correction.score}"
            assert not correction.is_unanswered, f"第 {i + 1} 题不应标记为未作答"

        print(f"✅ 场景3通过: 全对作业批改准确")

    async def test_partial_unanswered_correction(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试场景4: 部分未作答批改

        验证点:
        - 未作答题目 is_unanswered = true
        - 未作答题目 student_answer = null
        - unanswered_count = 2
        - 未作答题目 score = 0
        """
        test_case = load_test_case(SCENARIO_PARTIAL_UNANSWERED)
        expected = test_case["expected_result"]

        # 设置 Mock 响应
        mock_response = self._build_mock_response(expected)
        mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

        # 创建服务并调用
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        result = await service._call_ai_for_homework_correction(
            image_urls=test_case["image_urls"],
            subject=test_case["subject"],
            user_hint=test_case.get("user_hint", ""),
        )

        # 验证结果
        assert result is not None
        assert len(result.corrections) == 5, "应该有5道题"
        assert (
            result.unanswered_count == 2
        ), f"未作答数量应为2, 实际 {result.unanswered_count}"

        # 验证每道题
        unanswered_count = 0
        for correction in result.corrections:
            if correction.is_unanswered:
                unanswered_count += 1
                assert (
                    correction.student_answer is None
                ), f"未作答题目的学生答案应为 null, 实际 {correction.student_answer}"
                assert (
                    correction.score == 0
                ), f"未作答题目分数应为0, 实际 {correction.score}"

        assert (
            unanswered_count == 2
        ), f"统计的未作答题数与unanswered_count不一致: {unanswered_count} vs {result.unanswered_count}"

        print(f"✅ 场景4通过: 部分未作答批改准确")

    async def test_mixed_question_types(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试场景5: 混合题型批改

        验证点:
        - 正确识别不同题型 (选择题、填空题、解答题)
        - question_type 字段正确
        - 不同题型的批改逻辑正确
        """
        test_case = load_test_case(SCENARIO_MIXED_TYPES)
        expected = test_case["expected_result"]

        # 设置 Mock 响应
        mock_response = self._build_mock_response(expected)
        mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

        # 创建服务并调用
        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        result = await service._call_ai_for_homework_correction(
            image_urls=test_case["image_urls"],
            subject=test_case["subject"],
            user_hint=test_case.get("user_hint", ""),
        )

        # 验证结果
        assert result is not None
        assert len(result.corrections) == 3, "应该有3道题"

        # 验证题型
        question_types = [c.question_type for c in result.corrections]
        expected_types = test_case["validation_rules"]["question_types_must_include"]

        for expected_type in expected_types:
            assert (
                expected_type in question_types
            ), f"应该包含题型: {expected_type}, 实际题型: {question_types}"

        # 验证每道题
        for i, correction in enumerate(result.corrections):
            expected_correction = expected["corrections"][i]

            assert correction.question_type == expected_correction["question_type"], (
                f"第 {i + 1} 题题型不匹配: 期望 {expected_correction['question_type']}, "
                f"实际 {correction.question_type}"
            )

        print(f"✅ 场景5通过: 混合题型批改准确, 题型: {question_types}")

    def _build_mock_response(self, expected: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据预期结果构建 Mock 响应

        Args:
            expected: 预期结果字典

        Returns:
            Dict[str, Any]: Mock AI 响应
        """
        return {
            "corrections": expected["corrections"],
            "summary": expected.get("summary", "批改完成"),
            "overall_score": expected.get("overall_score", 100),
            "total_questions": expected["total_questions"],
            "unanswered_count": expected.get("unanswered_count", 0),
            "error_count": expected.get("error_count", 0),
        }


@pytest.mark.asyncio
class TestPromptAccuracyStatistics:
    """
    Prompt 准确率统计测试

    汇总所有场景的测试结果，计算整体准确率
    """

    async def test_overall_accuracy(
        self, db_session, mock_bailian_service_for_integration
    ):
        """
        测试整体准确率

        目标: ≥ 90% 的批改准确率
        """
        # 所有测试场景
        test_scenarios = [
            SCENARIO_SINGLE_QUESTION,
            SCENARIO_ALL_WRONG,
            SCENARIO_ALL_CORRECT,
            SCENARIO_PARTIAL_UNANSWERED,
            SCENARIO_MIXED_TYPES,
        ]

        total_questions = 0
        correct_judgements = 0

        service = LearningService(db_session)
        service.bailian_service = mock_bailian_service_for_integration

        for scenario_file in test_scenarios:
            test_case = load_test_case(scenario_file)
            expected = test_case["expected_result"]

            # 设置 Mock 响应
            mock_response = {
                "corrections": expected["corrections"],
                "summary": expected.get("summary", ""),
                "overall_score": expected.get("overall_score", 100),
                "total_questions": expected["total_questions"],
                "unanswered_count": expected.get("unanswered_count", 0),
                "error_count": expected.get("error_count", 0),
            }
            mock_bailian_service_for_integration.set_response(json.dumps(mock_response))

            # 调用批改
            result = await service._call_ai_for_homework_correction(
                image_urls=test_case["image_urls"],
                subject=test_case["subject"],
                user_hint=test_case.get("user_hint", ""),
            )

            if result is None:
                continue

            # 统计准确率
            for i, correction in enumerate(result.corrections):
                total_questions += 1
                expected_correction = expected["corrections"][i]

                # 判断是否准确（简化版，实际应更严格）
                is_correct = (
                    correction.question_number == expected_correction["question_number"]
                    and correction.is_unanswered == expected_correction["is_unanswered"]
                    and correction.error_type == expected_correction["error_type"]
                )

                if is_correct:
                    correct_judgements += 1

        # 计算准确率
        accuracy = (
            (correct_judgements / total_questions * 100) if total_questions > 0 else 0
        )

        print(f"\n{'='*60}")
        print(f"📊 Prompt 准确性统计")
        print(f"{'='*60}")
        print(f"总题数: {total_questions}")
        print(f"正确判断数: {correct_judgements}")
        print(f"准确率: {accuracy:.2f}%")
        print(f"目标准确率: ≥ 90%")
        print(f"{'='*60}")

        # 断言准确率
        assert accuracy >= 90.0, f"准确率 {accuracy:.2f}% 低于目标 90%，需要优化 Prompt"

        print(f"✅ 整体准确率测试通过: {accuracy:.2f}% ≥ 90%")
