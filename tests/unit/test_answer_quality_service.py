"""
答案质量评估服务单元测试
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.answer_quality import AnswerQualityScore
from src.services.answer_quality_service import AnswerQualityService
from src.services.bailian_service import ChatCompletionResponse


class TestAnswerQualityService:
    """答案质量评估服务测试"""

    @pytest.fixture
    def mock_bailian_service(self):
        """模拟百炼服务"""
        service = AsyncMock()
        return service

    @pytest.fixture
    def mock_repository(self):
        """模拟仓库"""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_bailian_service, mock_repository):
        """创建测试服务实例"""
        return AnswerQualityService(mock_bailian_service, mock_repository)

    def test_extract_keywords(self, service):
        """测试关键词提取"""
        text = "二次函数的顶点坐标是什么？"
        keywords = service._extract_keywords(text)

        # 检查提取了关键词（注意：简单实现会返回整个词组）
        assert len(keywords) > 0
        assert (
            any("二次函数" in kw for kw in keywords)
            or "二次函数的顶点坐标是什么" in keywords
        )
        # 停用词应被过滤（如果是独立的）
        assert "是" not in keywords

    def test_evaluate_by_rules_basic(self, service):
        """测试基于规则的基础评估"""
        question = "如何求二次函数的顶点坐标？"
        answer = """
        求二次函数顶点坐标的步骤如下：
        1. 将方程写成标准形式 y = a(x-h)^2 + k
        2. 顶点坐标就是 (h, k)
        
        例如：y = x^2 - 4x + 3
        配方后：y = (x-2)^2 - 1
        因此顶点坐标是 (2, -1)
        """

        scores, details, confidence = service._evaluate_by_rules(question, answer)

        # 检查评分维度
        assert "accuracy" in scores
        assert "completeness" in scores
        assert "clarity" in scores
        assert "usefulness" in scores
        assert "relevance" in scores

        # 检查评分范围
        for score in scores.values():
            assert 0 <= score <= 1

        # 检查置信度
        assert 0 <= confidence <= 1

        # 因为有步骤和例子，clarity 应该较高
        assert scores["clarity"] > 0.7

    def test_evaluate_by_rules_short_answer(self, service):
        """测试短答案的评估"""
        question = "什么是函数？"
        answer = "函数是映射关系。"

        scores, details, confidence = service._evaluate_by_rules(question, answer)

        # 短答案的完整性应该较低
        assert scores["completeness"] < 0.5

    def test_evaluate_by_rules_with_formula(self, service):
        """测试包含公式的答案"""
        question = "什么是勾股定理？"
        answer = "勾股定理：直角三角形中，a^2 + b^2 = c^2"

        scores, details, confidence = service._evaluate_by_rules(question, answer)

        # 有公式的答案 usefulness 应该较高
        assert scores["usefulness"] > 0.6
        assert details["usefulness"]["has_formula"] is True

    @pytest.mark.asyncio
    async def test_parse_ai_response_success(self, service):
        """测试成功解析 AI 响应"""
        ai_response = """{
            "accuracy": 0.85,
            "completeness": 0.90,
            "clarity": 0.80,
            "usefulness": 0.85,
            "relevance": 0.95,
            "reasons": {
                "accuracy": "答案准确无误",
                "completeness": "覆盖了所有要点",
                "clarity": "表达清晰",
                "usefulness": "实用性强",
                "relevance": "高度相关"
            },
            "confidence": 0.9
        }"""

        scores, details, confidence = service._parse_ai_response(ai_response)

        assert scores["accuracy"] == 0.85
        assert scores["completeness"] == 0.90
        assert scores["clarity"] == 0.80
        assert scores["usefulness"] == 0.85
        assert scores["relevance"] == 0.95
        assert confidence == 0.9
        assert "accuracy" in details

    @pytest.mark.asyncio
    async def test_parse_ai_response_invalid_json(self, service):
        """测试解析无效 JSON 响应"""
        ai_response = "这不是有效的 JSON"

        scores, details, confidence = service._parse_ai_response(ai_response)

        # 应返回默认评分
        assert scores["accuracy"] == 0.7
        assert "parse_error" in details

    def test_merge_scores(self, service):
        """测试评分融合"""
        rule_scores = {
            "accuracy": 0.6,
            "completeness": 0.7,
            "clarity": 0.8,
            "usefulness": 0.6,
            "relevance": 0.7,
        }

        ai_scores = {
            "accuracy": 0.9,
            "completeness": 0.9,
            "clarity": 0.8,
            "usefulness": 0.9,
            "relevance": 0.9,
        }

        # AI 权重 0.7
        merged = service._merge_scores(rule_scores, ai_scores, ai_weight=0.7)

        # 检查融合结果
        assert 0.6 < merged["accuracy"] < 0.9
        assert merged["accuracy"] == 0.6 * 0.3 + 0.9 * 0.7

    @pytest.mark.asyncio
    async def test_evaluate_answer_rule_method(self, service, mock_repository):
        """测试使用规则方法评估答案"""
        question_id = uuid4()
        answer_id = uuid4()
        question = "如何学习Python？"
        answer = "学习Python的步骤：1. 安装Python 2. 学习基础语法 3. 做项目"

        # 模拟仓库返回 None（未有评分）
        mock_repository.get_by_answer_id.return_value = None

        # 模拟创建评分
        mock_score = MagicMock(spec=AnswerQualityScore)
        mock_score.total_score = 0.75
        mock_repository.create.return_value = mock_score

        score = await service.evaluate_answer(
            question_id=question_id,
            answer_id=answer_id,
            question_text=question,
            answer_text=answer,
            method="rule",
        )

        # 验证仓库调用
        mock_repository.get_by_answer_id.assert_called_once_with(answer_id)
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_answer_existing_score(self, service, mock_repository):
        """测试答案已有评分的情况"""
        question_id = uuid4()
        answer_id = uuid4()

        # 模拟已有评分
        existing_score = MagicMock(spec=AnswerQualityScore)
        existing_score.total_score = 0.85
        mock_repository.get_by_answer_id.return_value = existing_score

        score = await service.evaluate_answer(
            question_id=question_id,
            answer_id=answer_id,
            question_text="test question",
            answer_text="test answer",
        )

        # 应返回现有评分，不创建新评分
        assert score == existing_score
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_answer_ai_method(
        self, service, mock_bailian_service, mock_repository
    ):
        """测试使用 AI 方法评估答案"""
        question_id = uuid4()
        answer_id = uuid4()

        # 模拟 AI 响应
        mock_response = MagicMock(spec=ChatCompletionResponse)
        mock_response.content = """{
            "accuracy": 0.9,
            "completeness": 0.9,
            "clarity": 0.8,
            "usefulness": 0.9,
            "relevance": 0.9,
            "reasons": {},
            "confidence": 0.9
        }"""
        mock_bailian_service.chat_completion.return_value = mock_response

        # 模拟仓库
        mock_repository.get_by_answer_id.return_value = None
        mock_score = MagicMock(spec=AnswerQualityScore)
        mock_repository.create.return_value = mock_score

        score = await service.evaluate_answer(
            question_id=question_id,
            answer_id=answer_id,
            question_text="test question",
            answer_text="test answer",
            method="ai",
        )

        # 验证 AI 服务被调用
        mock_bailian_service.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_manual_feedback(self, service, mock_repository):
        """测试添加人工反馈"""
        answer_id = uuid4()

        # 模拟现有评分
        existing_score = MagicMock(spec=AnswerQualityScore)
        existing_score.total_score = 0.75
        mock_repository.get_by_answer_id.return_value = existing_score

        # 模拟更新后的评分
        updated_score = MagicMock(spec=AnswerQualityScore)
        updated_score.total_score = 0.75
        updated_score.manual_feedback = "很好的答案"
        updated_score.manual_override_score = 0.90
        mock_repository.update.return_value = updated_score

        result = await service.add_manual_feedback(
            answer_id=answer_id,
            feedback="很好的答案",
            override_score=0.90,
        )

        # 验证仓库调用
        mock_repository.get_by_answer_id.assert_called_once_with(answer_id)

    def test_calculate_total_score_default_weights(self):
        """测试使用默认权重计算总分"""
        total = AnswerQualityScore.calculate_total_score(
            accuracy=0.8,
            completeness=0.9,
            clarity=0.7,
            usefulness=0.8,
            relevance=0.9,
        )

        # 计算期望值
        expected = (
            0.8 * 0.30  # accuracy
            + 0.9 * 0.25  # completeness
            + 0.7 * 0.15  # clarity
            + 0.8 * 0.10  # usefulness
            + 0.9 * 0.20  # relevance
        )

        assert abs(total - expected) < 0.01

    def test_calculate_total_score_custom_weights(self):
        """测试使用自定义权重计算总分"""
        custom_weights = {
            "accuracy": 0.40,
            "completeness": 0.30,
            "clarity": 0.10,
            "usefulness": 0.10,
            "relevance": 0.10,
        }

        total = AnswerQualityScore.calculate_total_score(
            accuracy=1.0,
            completeness=1.0,
            clarity=1.0,
            usefulness=1.0,
            relevance=1.0,
            weights=custom_weights,
        )

        # 所有维度都是 1.0，总分应该是 1.0
        assert total == 1.0
