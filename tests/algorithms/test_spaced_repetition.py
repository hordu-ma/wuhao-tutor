"""
测试间隔重复算法
测试艾宾浩斯遗忘曲线的实现

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.services.algorithms.spaced_repetition import SpacedRepetitionAlgorithm


class TestSpacedRepetitionAlgorithm:
    """测试间隔重复算法"""

    def test_ebbinghaus_intervals(self):
        """测试艾宾浩斯间隔常量"""
        assert SpacedRepetitionAlgorithm.EBBINGHAUS_INTERVALS == [1, 2, 4, 7, 15, 30]

    @pytest.mark.parametrize(
        "review_count,review_result,expected_interval",
        [
            (0, "correct", 2),  # 第1次正确后: 进入第2个间隔=2天
            (1, "correct", 4),  # 第2次正确后: 进入第3个间隔=4天
            (2, "correct", 7),  # 第3次正确后: 进入第4个间隔=7天
            (3, "correct", 15),  # 第4次正确后: 进入第5个间隔=15天
            (4, "correct", 30),  # 第5次正确后: 进入第6个间隔=30天
            (5, "correct", 30),  # 第6次正确后: 仍是第6个间隔=30天
            (10, "correct", 30),  # 超过最大索引: 30天
        ],
    )
    def test_calculate_next_review_correct(
        self, review_count, review_result, expected_interval
    ):
        """测试正确答案的间隔计算"""
        last_review = datetime.now()

        next_review, interval = SpacedRepetitionAlgorithm.calculate_next_review(
            review_count=review_count,
            review_result=review_result,
            current_mastery=0.7,  # 中等掌握度
            last_review_date=last_review,
        )

        assert interval == expected_interval
        assert next_review == last_review + timedelta(days=expected_interval)

    def test_calculate_next_review_incorrect(self):
        """测试错误答案重置间隔"""
        last_review = datetime.now()

        # 无论复习多少次，错误都重置为1天
        for review_count in [0, 1, 5, 10]:
            next_review, interval = SpacedRepetitionAlgorithm.calculate_next_review(
                review_count=review_count,
                review_result="incorrect",
                current_mastery=0.3,
                last_review_date=last_review,
            )

            assert interval == 1
            assert next_review == last_review + timedelta(days=1)

    @pytest.mark.parametrize(
        "review_count,expected_interval",
        [
            (0, 1),  # 第1次部分正确: 重复第1个间隔=1天
            (1, 2),  # 第2次部分正确: 重复第2个间隔=2天
            (2, 4),  # 第3次部分正确: 重复第3个间隔=4天
            (5, 30),  # 第6次部分正确: 重复第6个间隔=30天
        ],
    )
    def test_calculate_next_review_partial(self, review_count, expected_interval):
        """测试部分正确重复当前间隔"""
        last_review = datetime.now()

        next_review, interval = SpacedRepetitionAlgorithm.calculate_next_review(
            review_count=review_count,
            review_result="partial",
            current_mastery=0.5,
            last_review_date=last_review,
        )

        assert interval == expected_interval
        assert next_review == last_review + timedelta(days=expected_interval)

    def test_calculate_next_review_low_mastery(self):
        """测试低掌握度缩短间隔"""
        last_review = datetime.now()

        # 低掌握度 (< 0.5) 应该缩短间隔 * 0.8
        next_review, interval = SpacedRepetitionAlgorithm.calculate_next_review(
            review_count=2,  # 第3次复习，答对进入intervals[3]=7天
            review_result="correct",
            current_mastery=0.3,  # 低掌握度
            last_review_date=last_review,
        )

        # 7 * 0.8 = 5.6 -> int = 5
        assert interval == 5
        assert next_review == last_review + timedelta(days=5)

    def test_calculate_next_review_high_mastery(self):
        """测试高掌握度延长间隔"""
        last_review = datetime.now()

        # 高掌握度 (> 0.8) 应该延长间隔 * 1.2
        next_review, interval = SpacedRepetitionAlgorithm.calculate_next_review(
            review_count=2,  # 第3次复习，答对进入intervals[3]=7天
            review_result="correct",
            current_mastery=0.9,  # 高掌握度
            last_review_date=last_review,
        )

        # 7 * 1.2 = 8.4 -> int = 8
        assert interval == 8
        assert next_review == last_review + timedelta(days=8)

    def test_calculate_mastery_level_no_history(self):
        """测试无历史记录时的掌握度"""
        mastery = SpacedRepetitionAlgorithm.calculate_mastery_level([])
        assert mastery == 0.0

    def test_calculate_mastery_level_single_correct(self):
        """测试单次正确的掌握度"""
        review = MagicMock()
        review.review_result = "correct"

        mastery = SpacedRepetitionAlgorithm.calculate_mastery_level([review])

        # 权重 0.4 * 1.0 = 0.4
        assert mastery == 0.4

    def test_calculate_mastery_level_weighted_average(self):
        """测试加权平均计算"""
        # 创建5次复习记录
        reviews = []
        results = ["correct", "correct", "partial", "correct", "incorrect"]

        for result in results:
            review = MagicMock()
            review.review_result = result
            reviews.append(review)

        mastery = SpacedRepetitionAlgorithm.calculate_mastery_level(reviews)

        # 计算期望值: 0.4*1.0 + 0.3*1.0 + 0.15*0.5 + 0.1*1.0 + 0.05*0.0
        expected = 0.4 + 0.3 + 0.075 + 0.1 + 0.0
        assert mastery == round(expected, 2)

    def test_calculate_mastery_level_more_than_five(self):
        """测试超过5次复习只取最近5次"""
        reviews = []
        # 创建10次复习，都是正确
        for _ in range(10):
            review = MagicMock()
            review.review_result = "correct"
            reviews.append(review)

        mastery = SpacedRepetitionAlgorithm.calculate_mastery_level(reviews)

        # 只使用前5次，每次权重相加 = 0.4 + 0.3 + 0.15 + 0.1 + 0.05 = 1.0
        assert mastery == 1.0

    @pytest.mark.parametrize(
        "mastery_level,consecutive_correct,min_reviews,expected",
        [
            (0.9, 3, 3, True),  # 达到阈值
            (0.95, 5, 3, True),  # 超过阈值
            (0.8, 3, 3, False),  # 掌握度不足
            (0.9, 2, 3, False),  # 连续次数不足
            (0.85, 2, 3, False),  # 两者都不足
            (1.0, 0, 3, False),  # 连续次数为0
        ],
    )
    def test_is_mastered(
        self, mastery_level, consecutive_correct, min_reviews, expected
    ):
        """测试掌握判定"""
        result = SpacedRepetitionAlgorithm.is_mastered(
            mastery_level=mastery_level,
            consecutive_correct=consecutive_correct,
            min_reviews=min_reviews,
        )

        assert result == expected

    @pytest.mark.parametrize(
        "interval_days,expected_name",
        [
            (1, "1天后"),
            (2, "2天后"),
            (4, "4天后"),
            (7, "1周后"),
            (15, "半月后"),
            (30, "1月后"),
            (45, "45天后"),
        ],
    )
    def test_get_interval_name(self, interval_days, expected_name):
        """测试间隔友好名称"""
        name = SpacedRepetitionAlgorithm.get_interval_name(interval_days)
        assert name == expected_name
