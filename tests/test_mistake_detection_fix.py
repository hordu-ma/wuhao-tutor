"""
测试错题识别修复效果

验证修复后的错题自动识别逻辑：
1. 普通问答不会被误判为错题
2. 真正的错题仍能被正确识别
3. 带图片的题目仍能被识别
"""

import pytest
from src.services.learning_service import LearningService


class TestMistakeDetectionFix:
    """测试错题识别修复"""

    @pytest.fixture
    def learning_service(self, db_session):
        """创建LearningService实例"""
        return LearningService(db_session)

    # ========== 测试1：普通问答不应被识别为错题 ==========

    def test_normal_conversation_not_detected_as_mistake(self, learning_service):
        """测试普通对话不会被误判为错题"""
        test_cases = [
            "告诉我你最长的学科名称是什么？",
            "什么是光合作用？",
            "介绍一下勾股定理",
            "讲解一下牛顿第一定律",
            "说说中国的四大发明",
            "解释一下DNA的结构",
            "最长的河流是哪一条？",
            "举例说明比喻的修辞手法",
            "优点和缺点有什么区别？",
        ]

        for content in test_cases:
            result = learning_service._detect_mistake_keywords(content)
            assert result["is_mistake"] is False, f"普通问答被误判为错题: {content}"
            print(f"✅ 通过: {content} -> {result['reason']}")

    def test_knowledge_query_with_question_mark(self, learning_service):
        """测试知识查询（带问号）不会被误判"""
        test_cases = [
            "光合作用的定义是什么？",
            "有哪些常见的化学元素？",
            "这个概念怎么理解？",
            "这两个概念有什么联系？",
        ]

        for content in test_cases:
            result = learning_service._detect_mistake_keywords(content)
            # 应该要么返回False，要么返回None（不确定）
            assert result["is_mistake"] != True, f"知识查询被误判为错题: {content}"
            print(f"✅ 通过: {content} -> is_mistake={result['is_mistake']}")

    # ========== 测试2：真正的错题应被正确识别 ==========

    def test_real_mistake_detected_correctly(self, learning_service):
        """测试真正的错题能被正确识别"""
        test_cases = [
            ("这道题不会做", True, 0.9),  # (内容, 应该被识别, 最低置信度)
            ("我不懂这个题目", True, 0.9),
            ("怎么解这道题？", True, 0.9),
            ("做错了，帮我看看", True, 0.9),
            ("这题看不懂", True, 0.9),
            ("求解这道题", True, 0.9),
            ("帮我做一下", True, 0.9),
            ("不会做怎么办", True, 0.9),
        ]

        for content, should_detect, min_confidence in test_cases:
            result = learning_service._detect_mistake_keywords(content)
            assert result["is_mistake"] is True, f"真正的错题未被识别: {content}"
            assert (
                result["confidence"] >= min_confidence
            ), f"置信度过低: {content}, confidence={result['confidence']}"
            print(
                f"✅ 通过: {content} -> is_mistake={result['is_mistake']}, confidence={result['confidence']:.2f}"
            )

    def test_mistake_with_multiple_keywords(self, learning_service):
        """测试包含多个关键词的错题"""
        content = "这道题的解题步骤是什么？我解不出来。"
        result = learning_service._detect_mistake_keywords(content)
        assert result["is_mistake"] is True, "多个关键词的错题未被识别"
        print(f"✅ 通过: {content} -> confidence={result['confidence']:.2f}")

    # ========== 测试3：边界情况 ==========

    def test_single_medium_confidence_keyword_uncertain(self, learning_service):
        """测试单个中置信度关键词返回不确定（None）"""
        test_cases = [
            "解题步骤是什么？",
            "这道难题怎么办？",
            "解题方法有哪些？",
        ]

        for content in test_cases:
            result = learning_service._detect_mistake_keywords(content)
            # 单个中置信度关键词应返回None（不确定），而非True
            assert result["is_mistake"] is None, f"单个中置信度关键词应返回不确定: {content}"
            print(f"✅ 通过: {content} -> is_mistake=None (不确定，需要更多证据)")

    def test_multiple_medium_confidence_keywords_detected(self, learning_service):
        """测试多个中置信度关键词可以被识别"""
        content = "请问这道难题的解题步骤是什么？"
        result = learning_service._detect_mistake_keywords(content)
        assert result["is_mistake"] is True, "多个中置信度关键词未被识别"
        assert result["confidence"] >= 0.7, "多个中置信度关键词置信度应≥0.7"
        print(f"✅ 通过: {content} -> confidence={result['confidence']:.2f}")

    # ========== 测试4：综合判断逻辑 ==========

    def test_combined_analysis_high_confidence_keyword(self, learning_service):
        """测试综合判断：关键词高置信度"""
        keyword_result = {
            "is_mistake": True,
            "confidence": 0.9,
            "mistake_type": "empty_question",
        }
        ai_intent_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}
        image_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}

        is_mistake, metadata = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )

        assert is_mistake is True, "关键词高置信度应判定为错题"
        print(f"✅ 通过: 关键词高置信度 -> is_mistake=True, reason={metadata['reason']}")

    def test_combined_analysis_image_with_keyword_support(self, learning_service):
        """测试综合判断：图片高置信度 + 关键词支持"""
        keyword_result = {
            "is_mistake": None,
            "confidence": 0.6,
            "mistake_type": None,
        }  # 中等置信度
        ai_intent_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}
        image_result = {
            "is_mistake": True,
            "confidence": 0.85,
            "mistake_type": "empty_question",
        }

        is_mistake, metadata = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )

        assert is_mistake is True, "图片高置信度+关键词支持应判定为错题"
        print(
            f"✅ 通过: 图片高置信度+关键词支持 -> is_mistake=True, reason={metadata['reason']}"
        )

    def test_combined_analysis_insufficient_evidence(self, learning_service):
        """测试综合判断：证据不足时不应判定为错题"""
        keyword_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}
        ai_intent_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}
        image_result = {"is_mistake": True, "confidence": 0.7, "mistake_type": None}

        is_mistake, metadata = learning_service._combine_mistake_analysis(
            keyword_result, ai_intent_result, image_result
        )

        assert is_mistake is False, "证据不足时不应判定为错题"
        print(f"✅ 通过: 证据不足 -> is_mistake=False, reason={metadata['reason']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
