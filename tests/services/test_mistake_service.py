"""
错题服务单元测试
测试 MistakeService 核心功能

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.models.study import MistakeRecord, ReviewSchedule
from src.services.mistake_service import MistakeService


class TestMistakeService:
    """错题服务测试类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return MistakeService()

    def test_ebbinghaus_intervals(self, service):
        """测试艾宾浩斯复习间隔常量"""
        assert service.EBBINGHAUS_INTERVALS == [1, 2, 4, 7, 15]

    def test_mastery_correct_count(self, service):
        """测试掌握判定标准"""
        assert service.MASTERY_CORRECT_COUNT == 3

    # 注意：完整的集成测试需要数据库环境，这里只做基础验证
    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service is not None
        assert isinstance(service.EBBINGHAUS_INTERVALS, list)
        assert len(service.EBBINGHAUS_INTERVALS) == 5


# ============================================================================
# 艾宾浩斯算法逻辑测试（无需数据库）
# ============================================================================


class TestEbbinghausAlgorithm:
    """测试艾宾浩斯遗忘曲线算法逻辑"""

    def test_interval_calculation(self):
        """测试复习间隔计算逻辑"""
        service = MistakeService()
        intervals = service.EBBINGHAUS_INTERVALS

        # 第1次复习：1天后
        assert intervals[0] == 1

        # 第2次复习：2天后
        assert intervals[1] == 2

        # 第3次复习：4天后
        assert intervals[2] == 4

        # 第4次复习：7天后
        assert intervals[3] == 7

        # 第5次复习：15天后
        assert intervals[4] == 15

    def test_mastery_threshold(self):
        """测试掌握判定阈值"""
        service = MistakeService()

        # 连续3次正确即认为掌握
        assert service.MASTERY_CORRECT_COUNT == 3

        # 模拟复习过程
        correct_count = 0

        # 第1次正确
        correct_count += 1
        assert correct_count < service.MASTERY_CORRECT_COUNT  # 未掌握

        # 第2次正确
        correct_count += 1
        assert correct_count < service.MASTERY_CORRECT_COUNT  # 未掌握

        # 第3次正确
        correct_count += 1
        assert correct_count >= service.MASTERY_CORRECT_COUNT  # 已掌握


if __name__ == "__main__":
    """直接运行测试"""
    pytest.main([__file__, "-v", "-s"])
