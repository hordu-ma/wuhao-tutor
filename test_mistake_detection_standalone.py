#!/usr/bin/env python3
"""
错题识别修复验证脚本（独立运行，无需数据库）

使用方法:
    python test_mistake_detection_standalone.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Mock一个最小的LearningService，只包含我们修复的方法
class MockLearningService:
    """模拟LearningService，只用于测试关键词检测和综合判断"""

    def __init__(self):
        pass

    def _detect_mistake_keywords(self, question_content: str):
        """
        策略1：关键词检测（从修复后的代码复制）
        """
        # 🛡️ 排除关键词：明确的非错题场景（纯知识查询、闲聊）
        EXCLUSION_KEYWORDS = [
            "告诉我",
            "什么是",
            "介绍一下",
            "讲解一下",
            "说说",
            "解释一下",
            "最长的",
            "最短的",
            "最大的",
            "最小的",
            "有哪些",
            "举例",
            "比如",
            "区别",
            "联系",
            "关系",
            "定义",
            "概念",
            "特点",
            "优点",
            "缺点",
            "好处",
            "坏处",
        ]

        # 🎯 高置信度关键词：强烈暗示错题的词汇
        HIGH_CONFIDENCE_KEYWORDS = [
            "不会做",
            "不会",
            "不懂",
            "不理解",
            "不明白",
            "怎么做",
            "如何解答",
            "怎么解",
            "怎么算",
            "做错了",
            "答错了",
            "错在哪",
            "看不懂",
            "求解",
            "求答案",
            "帮我做",
            "帮我看看这道题",
        ]

        # 🔸 中置信度关键词：可能是错题，但需要更多证据
        MEDIUM_CONFIDENCE_KEYWORDS = [
            "解题步骤",
            "解题思路",
            "解题过程",
            "解题方法",
            "难题",
            "有难度",
            "解不出",
            "没学过",
        ]

        # 1. 先检查排除关键词
        matched_exclusion = [
            kw for kw in EXCLUSION_KEYWORDS if kw in question_content
        ]
        if matched_exclusion:
            return {
                "is_mistake": False,
                "confidence": 0.2,
                "mistake_type": None,
                "reason": f'检测到非错题关键词: {", ".join(matched_exclusion[:2])}',
                "matched_keywords": [],
            }

        # 2. 检查高置信度关键词
        matched_high = [
            kw for kw in HIGH_CONFIDENCE_KEYWORDS if kw in question_content
        ]

        # 3. 检查中置信度关键词
        matched_medium = [
            kw for kw in MEDIUM_CONFIDENCE_KEYWORDS if kw in question_content
        ]

        # 判断错题类型
        mistake_type = "hard_question"
        if any(kw in question_content for kw in ["错", "做错", "答错"]):
            mistake_type = "wrong_answer"
        elif any(kw in question_content for kw in ["不会", "不懂", "看不懂"]):
            mistake_type = "empty_question"

        # 高置信度关键词
        if matched_high:
            return {
                "is_mistake": True,
                "confidence": 0.9,
                "mistake_type": mistake_type,
                "reason": f'检测到高置信度关键词: {", ".join(matched_high[:2])}',
                "matched_keywords": matched_high,
            }

        # 多个中置信度关键词
        if len(matched_medium) >= 2:
            return {
                "is_mistake": True,
                "confidence": 0.7,
                "mistake_type": mistake_type,
                "reason": f'检测到多个中置信度关键词: {", ".join(matched_medium[:2])}',
                "matched_keywords": matched_medium,
            }

        # 单个中置信度关键词
        if matched_medium:
            return {
                "is_mistake": None,
                "confidence": 0.5,
                "mistake_type": None,
                "reason": f"检测到单个中置信度关键词（不足以判定）: {matched_medium[0]}",
                "matched_keywords": matched_medium,
            }

        return {
            "is_mistake": False,
            "confidence": 0.3,
            "mistake_type": None,
            "reason": "未检测到错题关键词",
            "matched_keywords": [],
        }

    def _combine_mistake_analysis(self, keyword_result, ai_intent_result, image_result):
        """
        策略4：综合判断（从修复后的代码复制）
        """
        evidences = []
        total_confidence = 0
        vote_for_mistake = 0
        vote_total = 0
        high_confidence_count = 0

        # 收集证据
        if keyword_result["is_mistake"] is not None:
            vote_total += 1
            if keyword_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += keyword_result["confidence"]
                evidences.append(f"关键词({keyword_result['confidence']:.2f})")
                if keyword_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        if ai_intent_result["is_mistake"] is not None:
            vote_total += 1
            if ai_intent_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += ai_intent_result["confidence"]
                evidences.append(f"AI意图({ai_intent_result['confidence']:.2f})")
                if ai_intent_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        if image_result["is_mistake"] is not None:
            vote_total += 1
            if image_result["is_mistake"]:
                vote_for_mistake += 1
                total_confidence += image_result["confidence"]
                evidences.append(f"图片({image_result['confidence']:.2f})")
                if image_result["confidence"] >= 0.85:
                    high_confidence_count += 1

        # 计算平均置信度
        avg_confidence = (
            total_confidence / vote_for_mistake if vote_for_mistake > 0 else 0
        )

        # 最终判断
        is_mistake = False
        decision_reason = ""

        if vote_total > 0 and vote_for_mistake > 0:
            # 场景1：关键词高置信度
            if keyword_result.get("is_mistake") and keyword_result.get(
                "confidence", 0
            ) >= 0.9:
                is_mistake = True
                decision_reason = "关键词高置信度（≥0.9）"

            # 场景2：图片高置信度 + 关键词支持
            elif (
                image_result.get("is_mistake")
                and image_result.get("confidence", 0) >= 0.85
                and keyword_result.get("is_mistake") is not False
                and keyword_result.get("confidence", 0) >= 0.6
            ):
                is_mistake = True
                decision_reason = "图片高置信度 + 关键词支持"

            # 场景3：多个高置信度证据
            elif high_confidence_count >= 2 and avg_confidence >= 0.8:
                is_mistake = True
                decision_reason = f"多个高置信度证据({high_confidence_count}个)"

            # 场景4：多维度支持
            elif vote_for_mistake >= 3 and avg_confidence >= 0.75:
                is_mistake = True
                decision_reason = "多维度证据支持（≥3个）"

            else:
                decision_reason = (
                    f"证据不足：高置信度证据{high_confidence_count}个，"
                    f"平均置信度{avg_confidence:.2f}"
                )

        mistake_type = (
            keyword_result.get("mistake_type")
            or ai_intent_result.get("mistake_type")
            or image_result.get("mistake_type")
            or "empty_question"
        )

        return is_mistake, {
            "is_mistake": is_mistake,
            "confidence": avg_confidence,
            "mistake_type": mistake_type,
            "reason": f'综合判断: {decision_reason}, 证据=[{", ".join(evidences)}]',
            "evidences": evidences,
            "vote_for_mistake": vote_for_mistake,
            "vote_total": vote_total,
            "high_confidence_count": high_confidence_count,
        }


def run_tests():
    """运行所有测试"""
    service = MockLearningService()
    
    print("=" * 80)
    print("错题识别修复验证测试")
    print("=" * 80)
    print()

    # ========== 测试1：普通问答不应被识别为错题 ==========
    print("【测试1】普通问答不应被识别为错题")
    print("-" * 80)
    
    test_cases = [
        "告诉我你最长的学科名称是什么？",  # 截图中的例子
        "什么是光合作用？",
        "介绍一下勾股定理",
        "讲解一下牛顿第一定律",
        "说说中国的四大发明",
        "解释一下DNA的结构",
        "最长的河流是哪一条？",
        "举例说明比喻的修辞手法",
        "优点和缺点有什么区别？",
    ]

    passed = 0
    failed = 0
    for content in test_cases:
        result = service._detect_mistake_keywords(content)
        if result["is_mistake"] is False:
            print(f"✅ {content}")
            print(f"   结果: is_mistake=False, reason={result['reason']}")
            passed += 1
        else:
            print(f"❌ {content}")
            print(f"   结果: is_mistake={result['is_mistake']}, reason={result['reason']}")
            failed += 1
        print()

    print(f"结果: {passed}个通过, {failed}个失败")
    print()

    # ========== 测试2：真正的错题应被正确识别 ==========
    print("【测试2】真正的错题应被正确识别")
    print("-" * 80)
    
    test_cases = [
        "这道题不会做",
        "我不懂这个题目",
        "怎么解这道题？",
        "做错了，帮我看看",
        "这题看不懂",
        "求解这道题",
        "帮我做一下",
        "不会做怎么办",
    ]

    passed = 0
    failed = 0
    for content in test_cases:
        result = service._detect_mistake_keywords(content)
        if result["is_mistake"] is True and result["confidence"] >= 0.9:
            print(f"✅ {content}")
            print(f"   结果: is_mistake=True, confidence={result['confidence']:.2f}")
            passed += 1
        else:
            print(f"❌ {content}")
            print(
                f"   结果: is_mistake={result['is_mistake']}, confidence={result.get('confidence', 0):.2f}"
            )
            failed += 1
        print()

    print(f"结果: {passed}个通过, {failed}个失败")
    print()

    # ========== 测试3：边界情况 ==========
    print("【测试3】边界情况：单个中置信度关键词应返回不确定")
    print("-" * 80)
    
    test_cases = [
        "解题步骤是什么？",
        "这道难题怎么办？",
        "解题方法有哪些？",
    ]

    passed = 0
    failed = 0
    for content in test_cases:
        result = service._detect_mistake_keywords(content)
        if result["is_mistake"] is None:
            print(f"✅ {content}")
            print(f"   结果: is_mistake=None (不确定), confidence={result['confidence']:.2f}")
            passed += 1
        else:
            print(f"❌ {content}")
            print(f"   结果: is_mistake={result['is_mistake']} (应该是None)")
            failed += 1
        print()

    print(f"结果: {passed}个通过, {failed}个失败")
    print()

    # ========== 测试4：综合判断 ==========
    print("【测试4】综合判断：图片高置信度 + 关键词支持")
    print("-" * 80)
    
    keyword_result = {
        "is_mistake": None,
        "confidence": 0.6,
        "mistake_type": None,
    }
    ai_intent_result = {"is_mistake": None, "confidence": 0.5, "mistake_type": None}
    image_result = {
        "is_mistake": True,
        "confidence": 0.85,
        "mistake_type": "empty_question",
    }

    is_mistake, metadata = service._combine_mistake_analysis(
        keyword_result, ai_intent_result, image_result
    )

    if is_mistake is True:
        print(f"✅ 综合判断通过")
        print(f"   结果: is_mistake=True, reason={metadata['reason']}")
    else:
        print(f"❌ 综合判断失败")
        print(f"   结果: is_mistake={is_mistake}, reason={metadata['reason']}")
    print()

    print("=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
