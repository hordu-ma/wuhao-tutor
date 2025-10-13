"""
间隔重复算法 (Spaced Repetition Algorithm)
基于艾宾浩斯遗忘曲线实现的智能复习时间计算

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime, timedelta
from typing import List, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


class SpacedRepetitionAlgorithm:
    """
    间隔重复算法
    
    基于艾宾浩斯遗忘曲线，结合用户掌握度动态调整复习间隔
    """

    # 艾宾浩斯复习间隔（天）
    EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

    @staticmethod
    def calculate_next_review(
        review_count: int,
        review_result: str,
        current_mastery: float,
        last_review_date: datetime,
    ) -> Tuple[datetime, int]:
        """
        计算下次复习时间

        参数:
            review_count: 已复习次数
            review_result: 'correct' | 'incorrect' | 'partial'
            current_mastery: 当前掌握度 0.0-1.0
            last_review_date: 上次复习时间

        返回:
            (next_review_date, interval_days)

        算法逻辑:
        1. 如果 review_result == 'incorrect': 重置为第 1 次间隔 (1天)
        2. 如果 review_result == 'partial': 重复当前间隔
        3. 如果 review_result == 'correct': 进入下一间隔
        4. 根据 current_mastery 调整间隔:
           - mastery < 0.5: 间隔 * 0.8
           - mastery > 0.8: 间隔 * 1.2
        """
        intervals = SpacedRepetitionAlgorithm.EBBINGHAUS_INTERVALS

        # 1. 根据复习结果确定基础间隔
        if review_result == "incorrect":
            # 答错：重置到第一个间隔
            interval_days = intervals[0]
            logger.debug(
                f"Review result incorrect, reset to first interval: {interval_days} days"
            )
        elif review_result == "partial":
            # 部分正确：重复当前间隔
            current_index = min(review_count, len(intervals) - 1)
            interval_days = intervals[current_index]
            logger.debug(
                f"Review result partial, repeat current interval: {interval_days} days"
            )
        else:  # correct
            # 答对：进入下一个间隔
            next_index = min(review_count + 1, len(intervals) - 1)
            interval_days = intervals[next_index]
            logger.debug(
                f"Review result correct, move to next interval: {interval_days} days"
            )

        # 2. 根据掌握度调整间隔
        original_interval = interval_days
        if current_mastery < 0.5:
            # 掌握度低，缩短间隔
            interval_days = int(interval_days * 0.8)
            logger.debug(
                f"Low mastery ({current_mastery}), adjusted interval: {original_interval} -> {interval_days} days"
            )
        elif current_mastery > 0.8:
            # 掌握度高，延长间隔
            interval_days = int(interval_days * 1.2)
            logger.debug(
                f"High mastery ({current_mastery}), adjusted interval: {original_interval} -> {interval_days} days"
            )

        # 确保至少间隔1天
        interval_days = max(interval_days, 1)

        # 3. 计算下次复习时间
        next_review = last_review_date + timedelta(days=interval_days)

        logger.info(
            f"Calculated next review: {interval_days} days from {last_review_date}, next date: {next_review}"
        )

        return next_review, interval_days

    @staticmethod
    def calculate_mastery_level(review_history: List) -> float:
        """
        计算掌握度

        算法:
        1. 最近 5 次复习加权平均
        2. 权重: 最近的复习权重更高 [0.4, 0.3, 0.15, 0.1, 0.05]
        3. 正确 = 1.0, 部分正确 = 0.5, 错误 = 0.0

        参数:
            review_history: 复习历史列表（已按时间倒序排列）

        返回:
            掌握度 0.0 - 1.0
        """
        if not review_history:
            logger.debug("No review history, mastery level = 0.0")
            return 0.0

        # 取最近 5 次
        recent = review_history[:5]
        weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # 权重递减

        # 结果分数映射
        result_scores = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}

        score = 0.0
        for i, review in enumerate(recent):
            # 获取复习结果
            review_result = (
                review.review_result
                if hasattr(review, "review_result")
                else "incorrect"
            )
            result_score = result_scores.get(review_result, 0.0)

            # 应用权重
            weight = weights[i] if i < len(weights) else 0.05
            score += result_score * weight

            logger.debug(
                f"Review {i+1}: result={review_result}, score={result_score}, weight={weight}"
            )

        mastery = round(score, 2)

        logger.info(
            f"Calculated mastery level from {len(recent)} reviews: {mastery}"
        )

        return mastery

    @staticmethod
    def is_mastered(
        mastery_level: float, consecutive_correct: int, min_reviews: int = 3
    ) -> bool:
        """
        判断是否已掌握

        条件:
        1. 掌握度 >= 0.9
        2. 连续正确次数 >= min_reviews (默认3次)

        参数:
            mastery_level: 当前掌握度
            consecutive_correct: 连续正确次数
            min_reviews: 最少复习次数

        返回:
            是否已掌握
        """
        is_mastered = mastery_level >= 0.9 and consecutive_correct >= min_reviews

        logger.debug(
            f"Mastery check: level={mastery_level}, consecutive={consecutive_correct}, "
            f"min_reviews={min_reviews}, result={is_mastered}"
        )

        return is_mastered

    @staticmethod
    def get_interval_name(interval_days: int) -> str:
        """
        获取间隔的友好名称

        参数:
            interval_days: 间隔天数

        返回:
            间隔名称，如 "1天后", "2天后", "1周后", "半月后", "1月后"
        """
        if interval_days == 1:
            return "1天后"
        elif interval_days == 2:
            return "2天后"
        elif interval_days == 4:
            return "4天后"
        elif interval_days == 7:
            return "1周后"
        elif interval_days == 15:
            return "半月后"
        elif interval_days == 30:
            return "1月后"
        else:
            return f"{interval_days}天后"
