"""
答案质量评估服务

提供多维度答案质量评分功能
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from src.models.answer_quality import AnswerQualityScore
from src.repositories.answer_quality_repository import AnswerQualityRepository
from src.services.bailian_service import BailianService

logger = logging.getLogger(__name__)


class AnswerQualityService:
    """答案质量评估服务"""

    def __init__(
        self,
        bailian_service: BailianService,
        repository: AnswerQualityRepository,
    ):
        """
        初始化答案质量评估服务

        Args:
            bailian_service: 百炼 AI 服务
            repository: 答案质量评分仓库
        """
        self.bailian_service = bailian_service
        self.repository = repository

        # 默认评分权重
        self.default_weights = {
            "accuracy": 0.30,  # 准确性最重要
            "completeness": 0.25,  # 完整性次之
            "relevance": 0.20,  # 相关性
            "clarity": 0.15,  # 清晰度
            "usefulness": 0.10,  # 有用性
        }

    async def evaluate_answer(
        self,
        question_id: UUID,
        answer_id: UUID,
        question_text: str,
        answer_text: str,
        method: str = "hybrid",
        weights: Optional[Dict[str, float]] = None,
    ) -> AnswerQualityScore:
        """
        评估答案质量

        Args:
            question_id: 问题ID
            answer_id: 答案ID
            question_text: 问题文本
            answer_text: 答案文本
            method: 评估方法 (rule/ai/hybrid)
            weights: 自定义权重

        Returns:
            答案质量评分
        """
        logger.info(f"开始评估答案质量: answer_id={answer_id}, method={method}")

        # 检查是否已有评分
        existing_score = await self.repository.get_by_answer_id(answer_id)
        if existing_score:
            logger.info(f"答案 {answer_id} 已有评分，返回现有评分")
            return existing_score

        # 根据方法选择评估策略
        if method == "rule":
            scores, details, confidence = self._evaluate_by_rules(
                question_text, answer_text
            )
            ai_response = None
        elif method == "ai":
            scores, details, confidence, ai_response = await self._evaluate_by_ai(
                question_text, answer_text
            )
        else:  # hybrid
            rule_scores, rule_details, rule_conf = self._evaluate_by_rules(
                question_text, answer_text
            )
            ai_scores, ai_details, ai_conf, ai_response = await self._evaluate_by_ai(
                question_text, answer_text
            )

            # 融合两种评分 (AI 权重更高)
            scores = self._merge_scores(rule_scores, ai_scores, ai_weight=0.7)
            details = {"rule": rule_details, "ai": ai_details}
            confidence = rule_conf * 0.3 + ai_conf * 0.7

        # 使用权重
        if weights is None:
            weights = self.default_weights

        # 计算总分
        total_score = AnswerQualityScore.calculate_total_score(
            accuracy=scores["accuracy"],
            completeness=scores["completeness"],
            clarity=scores["clarity"],
            usefulness=scores["usefulness"],
            relevance=scores["relevance"],
            weights=weights,
        )

        # 创建评分记录
        score_record = AnswerQualityScore(
            answer_id=answer_id,
            question_id=question_id,
            accuracy=scores["accuracy"],
            completeness=scores["completeness"],
            clarity=scores["clarity"],
            usefulness=scores["usefulness"],
            relevance=scores["relevance"],
            total_score=total_score,
            evaluation_method=method,
            evaluation_details=details,
            ai_raw_response=ai_response,
            confidence=confidence,
        )

        # 保存到数据库
        saved_score = await self.repository.create(score_record)

        logger.info(
            f"答案质量评估完成: answer_id={answer_id}, "
            f"total_score={total_score}, confidence={confidence}"
        )

        return saved_score

    def _evaluate_by_rules(
        self, question: str, answer: str
    ) -> Tuple[Dict[str, float], Dict, float]:
        """
        基于规则的评估

        Returns:
            (评分字典, 详情, 置信度)
        """
        scores = {}
        details = {}

        # 1. 准确性 - 基于关键词匹配
        question_keywords = self._extract_keywords(question)
        answer_keywords = self._extract_keywords(answer)
        keyword_match_ratio = len(question_keywords & answer_keywords) / max(
            len(question_keywords), 1
        )
        scores["accuracy"] = min(keyword_match_ratio * 1.2, 1.0)
        details["accuracy"] = {
            "question_keywords": list(question_keywords),
            "answer_keywords": list(answer_keywords),
            "match_ratio": keyword_match_ratio,
        }

        # 2. 完整性 - 基于答案长度
        answer_length = len(answer)
        if answer_length < 50:
            completeness = 0.3
        elif answer_length < 150:
            completeness = 0.6
        elif answer_length < 300:
            completeness = 0.8
        else:
            completeness = 1.0
        scores["completeness"] = completeness
        details["completeness"] = {
            "length": answer_length,
            "score_basis": "基于答案长度分段评分",
        }

        # 3. 清晰度 - 基于结构化程度
        has_steps = bool(re.search(r"[1-9]\.|第[一二三四五六七八九十]+步|步骤", answer))
        has_summary = bool(re.search(r"总结|综上|因此|所以", answer))
        has_examples = bool(re.search(r"例如|比如|举例", answer))

        clarity_score = 0.5  # 基础分
        if has_steps:
            clarity_score += 0.2
        if has_summary:
            clarity_score += 0.2
        if has_examples:
            clarity_score += 0.1
        scores["clarity"] = min(clarity_score, 1.0)
        details["clarity"] = {
            "has_steps": has_steps,
            "has_summary": has_summary,
            "has_examples": has_examples,
        }

        # 4. 有用性 - 基于实用元素
        has_formula = bool(re.search(r"[=+\-*/^()]|\d+x|\dx", answer))
        has_code = bool(re.search(r"```|`[^`]+`|def |class ", answer))
        has_reference = bool(re.search(r"参考|详见|查看|链接", answer))

        usefulness_score = 0.6  # 基础分
        if has_formula:
            usefulness_score += 0.2
        if has_code:
            usefulness_score += 0.1
        if has_reference:
            usefulness_score += 0.1
        scores["usefulness"] = min(usefulness_score, 1.0)
        details["usefulness"] = {
            "has_formula": has_formula,
            "has_code": has_code,
            "has_reference": has_reference,
        }

        # 5. 相关性 - 基于问题类型匹配
        # 检查是否回答了问题
        if "如何" in question or "怎么" in question or "怎样" in question:
            # 方法类问题应该有步骤
            relevance = 0.8 if has_steps else 0.5
        elif "是什么" in question or "什么是" in question:
            # 定义类问题应该有解释
            relevance = 0.8 if len(answer) > 100 else 0.6
        elif "为什么" in question:
            # 原因类问题应该有解释
            has_because = bool(re.search(r"因为|由于|原因", answer))
            relevance = 0.9 if has_because else 0.6
        else:
            # 通用问题
            relevance = 0.7

        scores["relevance"] = relevance
        details["relevance"] = {
            "question_type": "通用",
            "match_logic": "基于问题类型匹配",
        }

        # 规则评估的置信度相对较低
        confidence = 0.7

        return scores, details, confidence

    async def _evaluate_by_ai(
        self, question: str, answer: str
    ) -> Tuple[Dict[str, float], Dict, float, str]:
        """
        基于 AI 的评估

        Returns:
            (评分字典, 详情, 置信度, AI原始响应)
        """
        # 构建评估提示词
        prompt = f"""请作为教育专家，评估以下学习答疑的答案质量。

问题：{question}

答案：{answer}

请从以下5个维度评分（0.0-1.0），并给出简要理由：

1. 准确性 (Accuracy): 答案是否准确无误？
2. 完整性 (Completeness): 答案是否完整覆盖问题要点？
3. 清晰度 (Clarity): 答案是否表达清晰易懂？
4. 有用性 (Usefulness): 答案是否实用有帮助？
5. 相关性 (Relevance): 答案是否切题相关？

请按照以下JSON格式返回评分：
{{
    "accuracy": 0.85,
    "completeness": 0.90,
    "clarity": 0.80,
    "usefulness": 0.85,
    "relevance": 0.95,
    "reasons": {{
        "accuracy": "答案准确...",
        "completeness": "答案完整...",
        "clarity": "表达清晰...",
        "usefulness": "实用性强...",
        "relevance": "高度相关..."
    }},
    "confidence": 0.9
}}"""

        try:
            # 调用 AI 服务
            response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 降低温度以获得更一致的评分
            )

            # 提取内容
            ai_response_text = response.content

            # 解析 AI 响应
            scores, details, confidence = self._parse_ai_response(ai_response_text)

            return scores, details, confidence, ai_response_text

        except Exception as e:
            logger.error(f"AI 评估失败: {str(e)}")
            # AI 失败时返回中等评分
            fallback_scores = {
                "accuracy": 0.7,
                "completeness": 0.7,
                "clarity": 0.7,
                "usefulness": 0.7,
                "relevance": 0.7,
            }
            return fallback_scores, {"error": str(e)}, 0.5, ""

    def _parse_ai_response(
        self, ai_response: str
    ) -> Tuple[Dict[str, float], Dict, float]:
        """
        解析 AI 评估响应

        Returns:
            (评分字典, 详情, 置信度)
        """
        import json

        try:
            # 尝试提取 JSON
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                scores = {
                    "accuracy": float(data.get("accuracy", 0.7)),
                    "completeness": float(data.get("completeness", 0.7)),
                    "clarity": float(data.get("clarity", 0.7)),
                    "usefulness": float(data.get("usefulness", 0.7)),
                    "relevance": float(data.get("relevance", 0.7)),
                }

                details = data.get("reasons", {})
                confidence = float(data.get("confidence", 0.8))

                return scores, details, confidence
            else:
                raise ValueError("无法从响应中提取 JSON")

        except Exception as e:
            logger.warning(f"解析 AI 响应失败: {str(e)}，使用默认评分")
            # 解析失败时返回中等评分
            return (
                {
                    "accuracy": 0.7,
                    "completeness": 0.7,
                    "clarity": 0.7,
                    "usefulness": 0.7,
                    "relevance": 0.7,
                },
                {"parse_error": str(e)},
                0.6,
            )

    def _merge_scores(
        self,
        rule_scores: Dict[str, float],
        ai_scores: Dict[str, float],
        ai_weight: float = 0.7,
    ) -> Dict[str, float]:
        """
        融合规则评分和 AI 评分

        Args:
            rule_scores: 规则评分
            ai_scores: AI 评分
            ai_weight: AI 评分权重

        Returns:
            融合后的评分
        """
        rule_weight = 1 - ai_weight
        merged = {}

        for key in rule_scores:
            merged[key] = (
                rule_scores[key] * rule_weight + ai_scores.get(key, 0.7) * ai_weight
            )

        return merged

    def _extract_keywords(self, text: str) -> set:
        """提取文本关键词"""
        # 简单的关键词提取（移除停用词和标点）
        stopwords = {
            "的",
            "了",
            "和",
            "是",
            "在",
            "有",
            "个",
            "这",
            "那",
            "我",
            "你",
            "他",
        }
        words = re.findall(r"[\u4e00-\u9fa5]+", text)
        keywords = {w for w in words if len(w) > 1 and w not in stopwords}
        return keywords

    async def add_manual_feedback(
        self,
        answer_id: UUID,
        feedback: str,
        override_score: Optional[float] = None,
    ) -> AnswerQualityScore:
        """
        添加人工反馈

        Args:
            answer_id: 答案ID
            feedback: 反馈内容
            override_score: 修正后的总分 (可选)

        Returns:
            更新后的评分
        """
        score = await self.repository.get_by_answer_id(answer_id)
        if not score:
            raise ValueError(f"答案 {answer_id} 没有评分记录")

        # 准备更新数据
        update_data: Dict[str, Any] = {"manual_feedback": feedback}
        if override_score is not None:
            update_data["manual_override_score"] = override_score

        # 使用字典方式更新
        updated_score = await self.repository.update(str(score.id), update_data)  # type: ignore

        logger.info(
            f"添加人工反馈: answer_id={answer_id}, override_score={override_score}"
        )

        return updated_score  # type: ignore
