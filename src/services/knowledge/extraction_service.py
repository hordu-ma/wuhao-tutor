"""
知识点提取服务

提供基于规则和 AI 的混合知识点提取能力。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from collections import defaultdict

import jieba
import jieba.posseg as pseg

from src.services.bailian_service import BailianService

logger = logging.getLogger(__name__)


class KnowledgePoint:
    """知识点数据模型"""

    def __init__(
        self,
        name: str,
        confidence: float,
        method: str,
        matched_keywords: Optional[List[str]] = None,
        context: Optional[str] = None,
        related: Optional[List[str]] = None,
    ):
        self.name = name
        self.confidence = confidence  # 置信度 0-1
        self.method = method  # 提取方法: rule/ai/hybrid
        self.matched_keywords = matched_keywords or []
        self.context = context
        self.related = related or []

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "method": self.method,
            "matched_keywords": self.matched_keywords,
            "context": self.context,
            "related": self.related,
        }


class KnowledgeExtractionService:
    """知识点提取服务"""

    def __init__(self, bailian_service: Optional[BailianService] = None):
        self.bailian_service = bailian_service
        self.knowledge_dict = {}
        self._load_knowledge_dict()

        # 初始化 jieba 自定义词典
        self._init_jieba_dict()

    def _load_knowledge_dict(self):
        """加载知识点词典"""
        dict_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_dict"

        if not dict_dir.exists():
            logger.warning(f"知识点词典目录不存在: {dict_dir}")
            return

        for dict_file in dict_dir.glob("*.json"):
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    subject_dict = json.load(f)

                # 从文件名提取学科信息 (如 math_grade_9.json -> math)
                subject = dict_file.stem.split("_")[0]
                if subject not in self.knowledge_dict:
                    self.knowledge_dict[subject] = {}

                self.knowledge_dict[subject].update(subject_dict)
                logger.info(f"加载知识点词典: {dict_file.name}, 包含 {len(subject_dict)} 个知识点")

            except Exception as e:
                logger.error(f"加载知识点词典失败 {dict_file}: {e}")

    def _init_jieba_dict(self):
        """初始化 jieba 自定义词典"""
        # 将所有知识点名称和关键词加入 jieba 词典
        for subject_dict in self.knowledge_dict.values():
            for kp_name, kp_data in subject_dict.items():
                jieba.add_word(kp_name, freq=1000)  # 高频词
                for keyword in kp_data.get("keywords", []):
                    jieba.add_word(keyword, freq=500)

        logger.info("jieba 自定义词典初始化完成")

    async def extract_from_homework(
        self, content: str, subject: str, grade: Optional[str] = None
    ) -> List[KnowledgePoint]:
        """
        从作业内容提取知识点

        Args:
            content: 作业内容
            subject: 学科 (数学/语文/英语)
            grade: 年级 (可选)

        Returns:
            知识点列表
        """
        logger.info(f"开始提取知识点: subject={subject}, content_len={len(content)}")

        # 方案 A: 基于规则的提取 (快速)
        rule_based = self._rule_based_extraction(content, subject)
        logger.info(f"规则提取结果: {len(rule_based)} 个知识点")

        # 方案 B: 基于 AI 的提取 (准确，但较慢)
        ai_based = []
        if self.bailian_service:
            try:
                ai_based = await self._ai_extraction(content, subject)
                logger.info(f"AI 提取结果: {len(ai_based)} 个知识点")
            except Exception as e:
                logger.error(f"AI 提取失败: {e}")

        # 方案 C: 融合结果
        merged = self._merge_results(rule_based, ai_based)
        logger.info(f"融合后结果: {len(merged)} 个知识点")

        # 排序: 按置信度降序
        merged.sort(key=lambda x: x.confidence, reverse=True)

        # 限制数量 (最多返回 10 个)
        return merged[:10]

    def _rule_based_extraction(self, content: str, subject: str) -> List[KnowledgePoint]:
        """基于规则的知识点提取"""
        knowledge_points = []

        # 获取学科词典
        subject_dict = self.knowledge_dict.get(subject, {})
        if not subject_dict:
            logger.warning(f"未找到学科词典: {subject}")
            return knowledge_points

        # 1. 分词
        words = [word for word, _ in pseg.cut(content)]

        # 2. 知识点名称直接匹配
        for kp_name, kp_data in subject_dict.items():
            if kp_name in content:
                knowledge_points.append(
                    KnowledgePoint(
                        name=kp_name,
                        confidence=0.9,  # 名称直接匹配，高置信度
                        method="rule",
                        matched_keywords=[kp_name],
                        related=kp_data.get("related", []),
                    )
                )

        # 3. 关键词匹配
        keyword_matches: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "keywords": [], "related": []}
        )

        for kp_name, kp_data in subject_dict.items():
            keywords = kp_data.get("keywords", [])
            matched_keywords: List[str] = []

            for keyword in keywords:
                if keyword in content:
                    matched_keywords.append(keyword)

            if matched_keywords:
                keyword_matches[kp_name]["count"] = len(matched_keywords)
                keyword_matches[kp_name]["keywords"] = matched_keywords
                keyword_matches[kp_name]["related"] = kp_data.get("related", [])

        # 将关键词匹配转换为 KnowledgePoint
        for kp_name, match_data in keyword_matches.items():
            # 避免重复 (如果名称已匹配)
            if any(kp.name == kp_name for kp in knowledge_points):
                continue

            # 计算置信度: 匹配关键词数量 / 总关键词数量
            total_keywords = len(subject_dict[kp_name].get("keywords", []))
            confidence = min(match_data["count"] / total_keywords, 0.85)  # 最高 0.85

            knowledge_points.append(
                KnowledgePoint(
                    name=kp_name,
                    confidence=confidence,
                    method="rule",
                    matched_keywords=match_data["keywords"],
                    related=match_data["related"],
                )
            )

        return knowledge_points

    async def _ai_extraction(self, content: str, subject: str) -> List[KnowledgePoint]:
        """基于 AI 的知识点提取"""
        if not self.bailian_service:
            return []

        # 构建提示词
        prompt = f"""请从以下{subject}题目中提取涉及的知识点，按重要性排序。

题目内容:
{content}

要求:
1. 只返回知识点名称，每行一个
2. 最多返回 5 个最相关的知识点
3. 知识点要准确、具体
4. 不要返回解释和多余的文字

示例格式:
二次函数
函数图象
坐标系
"""

        try:
            response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 低温度，更确定的输出
                max_tokens=200,
            )

            # 解析响应
            lines = response.content.strip().split("\n")
            knowledge_points = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 移除可能的序号 (1. 或 - )
                line = line.lstrip("0123456789.-、 ")

                if line:
                    knowledge_points.append(
                        KnowledgePoint(
                            name=line,
                            confidence=0.8,  # AI 提取基础置信度
                            method="ai",
                        )
                    )

            return knowledge_points

        except Exception as e:
            logger.error(f"AI 提取失败: {e}")
            return []

    def _merge_results(
        self, rule_based: List[KnowledgePoint], ai_based: List[KnowledgePoint]
    ) -> List[KnowledgePoint]:
        """融合规则和 AI 提取结果"""
        merged = {}

        # 1. 添加规则提取结果
        for kp in rule_based:
            merged[kp.name] = kp

        # 2. 融合 AI 提取结果
        for kp in ai_based:
            if kp.name in merged:
                # 如果已存在，提升置信度并标记为混合方法
                existing = merged[kp.name]
                existing.confidence = min(existing.confidence + 0.1, 1.0)
                existing.method = "hybrid"
            else:
                # 新知识点
                merged[kp.name] = kp

        return list(merged.values())

    def extract_from_question(
        self, content: str, subject: str, grade: Optional[str] = None
    ) -> List[KnowledgePoint]:
        """
        从问题内容提取知识点 (同步版本，仅使用规则)

        Args:
            content: 问题内容
            subject: 学科
            grade: 年级

        Returns:
            知识点列表
        """
        return self._rule_based_extraction(content, subject)
