"""
知识点提取服务单元测试
"""

import pytest
from src.services.knowledge.extraction_service import (
    KnowledgeExtractionService,
    KnowledgePoint,
)


class TestKnowledgeExtractionService:
    """知识点提取服务测试"""

    @pytest.fixture
    def extraction_service(self):
        """创建提取服务实例"""
        return KnowledgeExtractionService()

    def test_load_knowledge_dict(self, extraction_service):
        """测试知识点词典加载"""
        assert len(extraction_service.knowledge_dict) > 0
        assert "math" in extraction_service.knowledge_dict
        assert "english" in extraction_service.knowledge_dict
        assert "chinese" in extraction_service.knowledge_dict

    def test_rule_based_extraction_math(self, extraction_service):
        """测试数学知识点提取"""
        content = "求二次函数 y = x² - 4x + 3 的顶点坐标和对称轴"

        knowledge_points = extraction_service._rule_based_extraction(content, "math")

        # 应该提取到"二次函数"知识点
        assert len(knowledge_points) > 0
        kp_names = [kp.name for kp in knowledge_points]
        assert "二次函数" in kp_names

        # 检查置信度
        for kp in knowledge_points:
            assert 0 <= kp.confidence <= 1
            assert kp.method == "rule"

    def test_rule_based_extraction_english(self, extraction_service):
        """测试英语知识点提取"""
        content = "这句话应该用被动语态，主语是动作的承受者"

        knowledge_points = extraction_service._rule_based_extraction(content, "english")

        # 应该提取到"被动语态"知识点
        kp_names = [kp.name for kp in knowledge_points]
        assert "被动语态" in kp_names

    def test_rule_based_extraction_chinese(self, extraction_service):
        """测试语文知识点提取"""
        content = "这篇记叙文的六要素包括时间、地点、人物、起因、经过、结果"

        knowledge_points = extraction_service._rule_based_extraction(content, "chinese")

        # 应该提取到"记叙文"知识点
        kp_names = [kp.name for kp in knowledge_points]
        assert "记叙文" in kp_names

    def test_keyword_matching(self, extraction_service):
        """测试关键词匹配"""
        content = "抛物线的顶点在对称轴上，开口向上时有最小值"

        knowledge_points = extraction_service._rule_based_extraction(content, "math")

        # 应该通过关键词匹配到"二次函数"
        kp_names = [kp.name for kp in knowledge_points]
        assert "二次函数" in kp_names

        # 找到对应知识点
        二次函数_kp = next(kp for kp in knowledge_points if kp.name == "二次函数")

        # 检查匹配的关键词
        assert len(二次函数_kp.matched_keywords) > 0
        assert any(
            keyword in ["抛物线", "顶点", "对称轴"]
            for keyword in 二次函数_kp.matched_keywords
        )

    def test_extract_from_question_sync(self, extraction_service):
        """测试同步问题提取"""
        question = "请问圆的面积公式是什么？圆周角定理怎么用？"

        knowledge_points = extraction_service.extract_from_question(question, "math")

        assert len(knowledge_points) > 0
        kp_names = [kp.name for kp in knowledge_points]
        assert "圆" in kp_names

    def test_multiple_knowledge_points(self, extraction_service):
        """测试提取多个知识点"""
        content = """
        1. 求二次函数的顶点坐标
        2. 判断圆和直线的位置关系
        3. 计算相似三角形的相似比
        """

        knowledge_points = extraction_service._rule_based_extraction(content, "math")

        # 应该提取到多个知识点
        assert len(knowledge_points) >= 3

        kp_names = [kp.name for kp in knowledge_points]
        assert "二次函数" in kp_names
        assert "圆" in kp_names
        assert "相似三角形" in kp_names

    def test_confidence_scores(self, extraction_service):
        """测试置信度评分"""
        # 完整名称匹配应该有更高置信度
        content1 = "二次函数的定义"
        kp1 = extraction_service._rule_based_extraction(content1, "math")
        confidence1 = next((kp.confidence for kp in kp1 if kp.name == "二次函数"), 0)

        # 关键词匹配应该有较低置信度
        content2 = "抛物线"
        kp2 = extraction_service._rule_based_extraction(content2, "math")
        confidence2 = next((kp.confidence for kp in kp2 if kp.name == "二次函数"), 0)

        # 名称匹配置信度应该高于关键词匹配
        assert confidence1 > confidence2

    def test_merge_results(self, extraction_service):
        """测试结果融合"""
        rule_based = [
            KnowledgePoint(name="二次函数", confidence=0.9, method="rule"),
            KnowledgePoint(name="圆", confidence=0.8, method="rule"),
        ]

        ai_based = [
            KnowledgePoint(name="二次函数", confidence=0.8, method="ai"),
            KnowledgePoint(name="函数图象", confidence=0.7, method="ai"),
        ]

        merged = extraction_service._merge_results(rule_based, ai_based)

        # 检查融合结果
        assert len(merged) == 3  # 二次函数(合并), 圆, 函数图象

        # 二次函数应该被标记为 hybrid 且置信度提升
        二次函数 = next(kp for kp in merged if kp.name == "二次函数")
        assert 二次函数.method == "hybrid"
        assert 二次函数.confidence > 0.9

    def test_knowledge_point_limit(self, extraction_service):
        """测试知识点数量限制"""
        # 创建包含大量关键词的内容
        content = "二次函数 抛物线 圆 半径 相似三角形 锐角三角函数 sin cos tan 概率 反比例函数"

        knowledge_points = extraction_service._rule_based_extraction(content, "math")

        # 原始提取可能很多，但最终返回应该限制数量
        # (在 extract_from_homework 中限制为 10 个)
        assert len(knowledge_points) <= 20  # 规则提取本身可能返回更多

    def test_unknown_subject(self, extraction_service):
        """测试未知学科"""
        content = "这是一些内容"

        knowledge_points = extraction_service._rule_based_extraction(
            content, "unknown_subject"
        )

        # 未知学科应该返回空列表
        assert len(knowledge_points) == 0

    def test_empty_content(self, extraction_service):
        """测试空内容"""
        content = ""

        knowledge_points = extraction_service._rule_based_extraction(content, "math")

        # 空内容应该返回空列表
        assert len(knowledge_points) == 0

    @pytest.mark.asyncio
    async def test_extract_from_homework_integration(self, extraction_service):
        """测试作业提取集成（不使用 AI）"""
        content = "求二次函数 y = x² - 4x + 3 的顶点坐标"

        # 不提供 bailian_service，应该只使用规则提取
        knowledge_points = await extraction_service.extract_from_homework(
            content, "math"
        )

        assert len(knowledge_points) > 0
        kp_names = [kp.name for kp in knowledge_points]
        assert "二次函数" in kp_names

        # 不应超过 10 个
        assert len(knowledge_points) <= 10

        # 应该按置信度降序排列
        confidences = [kp.confidence for kp in knowledge_points]
        assert confidences == sorted(confidences, reverse=True)
