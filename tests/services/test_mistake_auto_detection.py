"""
错题自动识别功能的单元测试

验证修复后的4策略判断逻辑:正常问答不应被误判为错题
"""

import pytest

from src.services.learning_service import LearningService


@pytest.fixture
def learning_service(db_session):
    """创建LearningService实例"""
    return LearningService(db=db_session)


class TestMistakeAutoDetection:
    """错题自动识别功能测试"""

    @pytest.mark.asyncio
    async def test_normal_question_should_not_create_mistake(self, learning_service):
        """测试：正常问答不应创建错题"""
        # 场景：用户只是普通提问，AI正常回答
        question_content = "当然以! 我可以帮助你: 1. 解析数学、物理等学科的概念..."
        ai_answer = "好的，我可以帮你解答数学问题。请告诉我具体的题目。"

        # 策略1：关键词检测
        keyword_result = learning_service._detect_mistake_keywords(question_content)
        assert keyword_result["is_mistake"] is False, "正常问答不应匹配错题关键词"

        # 策略2：AI意图识别（修复后应该返回None）
        ai_intent_result = learning_service._extract_ai_mistake_metadata(ai_answer)
        assert ai_intent_result["is_mistake"] is None, "AI意图识别不应误判正常回答"

        # 策略3：图片分析（无图片）
        image_result = await learning_service._analyze_question_images(
            [], question_content
        )
        assert image_result["is_mistake"] is None, "无图片时不应判定为错题"

        # 策略4：综合判断
        should_create, meta = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )
        assert should_create is False, "综合判断不应创建错题"

    @pytest.mark.asyncio
    async def test_clear_mistake_with_keywords_should_create(self, learning_service):
        """测试：明确的错题关键词应创建错题"""
        question_content = "这道题不会做，帮我看看"
        ai_answer = "这是一道关于二次函数的题目..."

        # 策略1：关键词检测（高置信度）
        keyword_result = learning_service._detect_mistake_keywords(question_content)
        assert keyword_result["is_mistake"] is True
        assert keyword_result["confidence"] >= 0.85, "应返回高置信度"

        # 综合判断（单个高置信度证据应该足够）
        ai_intent_result = learning_service._extract_ai_mistake_metadata(ai_answer)
        image_result = await learning_service._analyze_question_images(
            [], question_content
        )

        should_create, meta = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )
        assert should_create is True, "单个高置信度证据应创建错题"
        assert meta["confidence"] >= 0.85

    @pytest.mark.asyncio
    async def test_mistake_with_image_should_create(self, learning_service):
        """测试：有图片上传且提问简短应创建错题"""
        question_content = "这题怎么做"  # 短提问
        image_urls = ["https://example.com/question.jpg"]

        # 策略3：图片分析（有图片+短提问）
        image_result = await learning_service._analyze_question_images(
            image_urls, question_content
        )
        assert image_result["is_mistake"] is True
        assert image_result["confidence"] >= 0.75

    @pytest.mark.asyncio
    async def test_ai_answer_with_solution_not_trigger_mistake(self, learning_service):
        """测试：AI回答包含"这道题"等词不应误判（修复前的bug）"""
        question_content = "帮我理解一下概念"  # 正常提问
        ai_answer = "这道题目考查的是二次函数的性质。解题步骤如下：1. 先配方..."

        # AI意图识别不应因回答内容误判
        ai_intent_result = learning_service._extract_ai_mistake_metadata(ai_answer)
        assert ai_intent_result["is_mistake"] is None, (
            "修复后：AI回答内容不应触发错题判断"
        )

        # 综合判断
        keyword_result = learning_service._detect_mistake_keywords(question_content)
        image_result = await learning_service._analyze_question_images(
            [], question_content
        )

        should_create, meta = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )
        assert should_create is False, "修复验证：不应因AI回答内容误判"

    def test_threshold_confidence_check(self, learning_service):
        """测试：单个中等置信度证据不应创建错题（阈值检查）"""
        # 模拟中等置信度关键词（0.7）
        keyword_result = {
            "is_mistake": True,
            "confidence": 0.7,
            "mistake_type": "concept_question",
            "matched_keywords": ["怎么做"],
            "reason": "匹配到中等置信度关键词",
        }
        ai_intent_result = {"is_mistake": None, "confidence": 0.5}
        image_result = {"is_mistake": None, "confidence": 0.5}

        should_create, meta = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )
        # 0.7 < 0.85 不应通过单证据门槛
        assert should_create is False, "单个中等置信度(0.7)不应创建错题"

    def test_multiple_evidences_lower_threshold(self, learning_service):
        """测试：多个证据可以降低阈值要求"""
        # 两个中等证据
        keyword_result = {
            "is_mistake": True,
            "confidence": 0.75,
            "mistake_type": "concept_question",
        }
        ai_intent_result = {"is_mistake": True, "confidence": 0.75}
        image_result = {"is_mistake": None, "confidence": 0.5}

        should_create, meta = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )
        # 2票且平均0.75应该通过
        assert should_create is True, "多证据(2票, 平均≥0.75)应创建错题"
        assert 0.75 <= meta["confidence"] < 0.85
