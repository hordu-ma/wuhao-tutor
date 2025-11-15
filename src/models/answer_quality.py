"""
答案质量评估模型

提供多维度答案质量评分的数据模型
"""

from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, ForeignKey, Index, Numeric, String, Text

from src.core.config import get_settings
from src.models.base import BaseModel

# 获取配置以确定数据库类型
settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI and "sqlite" in str(
    settings.SQLALCHEMY_DATABASE_URI
)  # type: ignore

# 根据数据库类型导入合适的 UUID 类型
if not is_sqlite:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
else:
    PG_UUID = None  # type: ignore


def get_uuid_column():
    """根据数据库类型返回合适的 UUID 列类型"""
    if is_sqlite:
        return String(36)
    else:
        return PG_UUID(as_uuid=True)  # type: ignore


class AnswerQualityScore(BaseModel):
    """
    答案质量评分模型

    存储对学习答疑答案的多维度质量评估
    """

    __tablename__ = "answer_quality_scores"

    # 关联字段
    answer_id = Column(
        get_uuid_column(),  # type: ignore
        ForeignKey("learning_answers.id"),
        nullable=False,
        unique=True,
        index=True,
        comment="关联的答案ID",
    )

    question_id = Column(
        get_uuid_column(),  # type: ignore
        ForeignKey("learning_questions.id"),
        nullable=False,
        index=True,
        comment="关联的问题ID",
    )

    # 评分维度 (0.0-1.0)
    accuracy = Column(
        Numeric(3, 2),
        nullable=False,
        comment="准确性评分 (0.0-1.0)",
    )

    completeness = Column(
        Numeric(3, 2),
        nullable=False,
        comment="完整性评分 (0.0-1.0)",
    )

    clarity = Column(
        Numeric(3, 2),
        nullable=False,
        comment="清晰度评分 (0.0-1.0)",
    )

    usefulness = Column(
        Numeric(3, 2),
        nullable=False,
        comment="有用性评分 (0.0-1.0)",
    )

    relevance = Column(
        Numeric(3, 2),
        nullable=False,
        comment="相关性评分 (0.0-1.0)",
    )

    # 综合评分
    total_score = Column(
        Numeric(3, 2),
        nullable=False,
        index=True,
        comment="总分 (加权平均)",
    )

    # 评估方法
    evaluation_method = Column(
        String(20),
        nullable=False,
        comment="评估方法: rule/ai/hybrid/manual",
    )

    # 评估详情
    evaluation_details = Column(
        JSON,
        nullable=True,
        comment="评估详细信息 (JSON)",
    )

    # AI 评估原始输出
    ai_raw_response = Column(
        Text,
        nullable=True,
        comment="AI 评估的原始响应",
    )

    # 人工反馈
    manual_feedback = Column(
        Text,
        nullable=True,
        comment="人工反馈意见",
    )

    manual_override_score = Column(
        Numeric(3, 2),
        nullable=True,
        comment="人工修正后的总分",
    )

    # 置信度
    confidence = Column(
        Numeric(3, 2),
        default=0.8,
        nullable=False,
        comment="评分置信度 (0.0-1.0)",
    )

    # 索引优化
    __table_args__ = (
        Index("idx_quality_answer", "answer_id"),
        Index("idx_quality_score", "total_score"),
        Index("idx_quality_method", "evaluation_method"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "answer_id": str(self.answer_id),
            "question_id": str(self.question_id),
            "scores": {
                "accuracy": float(self.accuracy),  # type: ignore
                "completeness": float(self.completeness),  # type: ignore
                "clarity": float(self.clarity),  # type: ignore
                "usefulness": float(self.usefulness),  # type: ignore
                "relevance": float(self.relevance),  # type: ignore
            },
            "total_score": float(self.total_score),  # type: ignore
            "evaluation_method": self.evaluation_method,
            "evaluation_details": self.evaluation_details,
            "confidence": float(self.confidence),  # type: ignore
            "manual_feedback": self.manual_feedback,
            "manual_override_score": (
                float(self.manual_override_score)  # type: ignore
                if self.manual_override_score is not None  # type: ignore
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,  # type: ignore
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,  # type: ignore
        }

    def get_final_score(self) -> float:
        """获取最终评分 (考虑人工修正)"""
        if self.manual_override_score is not None:  # type: ignore
            return float(self.manual_override_score)  # type: ignore
        return float(self.total_score)  # type: ignore

    @classmethod
    def calculate_total_score(
        cls,
        accuracy: float,
        completeness: float,
        clarity: float,
        usefulness: float,
        relevance: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        计算加权总分

        Args:
            accuracy: 准确性评分
            completeness: 完整性评分
            clarity: 清晰度评分
            usefulness: 有用性评分
            relevance: 相关性评分
            weights: 各维度权重 (可选)

        Returns:
            加权总分
        """
        if weights is None:
            # 默认权重
            weights = {
                "accuracy": 0.30,  # 准确性最重要
                "completeness": 0.25,  # 完整性次之
                "relevance": 0.20,  # 相关性
                "clarity": 0.15,  # 清晰度
                "usefulness": 0.10,  # 有用性
            }

        total = (
            accuracy * weights["accuracy"]
            + completeness * weights["completeness"]
            + clarity * weights["clarity"]
            + usefulness * weights["usefulness"]
            + relevance * weights["relevance"]
        )

        return round(total, 2)
