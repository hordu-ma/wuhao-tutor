"""
知识图谱相关数据模型
支持错题-知识点关联、知识图谱快照和学习轨迹追踪
"""

import enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel, is_sqlite


class ErrorType(enum.Enum):
    """错误类型枚举"""

    CONCEPT_MISUNDERSTANDING = "concept_misunderstanding"  # 概念理解错误
    CALCULATION_ERROR = "calculation_error"  # 计算错误
    FORMULA_MISUSE = "formula_misuse"  # 公式使用错误
    LOGIC_ERROR = "logic_error"  # 逻辑推理错误
    CARELESS_MISTAKE = "careless_mistake"  # 粗心大意
    KNOWLEDGE_GAP = "knowledge_gap"  # 知识盲区
    METHOD_CONFUSION = "method_confusion"  # 方法混淆
    OTHER = "other"  # 其他


class WeakChainType(enum.Enum):
    """薄弱知识链类型枚举"""

    PREREQUISITE_GAP = "prerequisite_gap"  # 前置知识缺失
    CONCEPT_CLUSTER = "concept_cluster"  # 概念簇薄弱
    METHOD_CHAIN = "method_chain"  # 方法链薄弱
    COMPREHENSIVE_APPLICATION = "comprehensive_application"  # 综合应用薄弱


class MistakeKnowledgePoint(BaseModel):
    """
    错题-知识点关联模型
    实现多对多关联，记录每个错题关联的知识点及详细信息
    """

    __tablename__ = "mistake_knowledge_points"

    # 关联字段
    if is_sqlite:
        mistake_id = Column(
            String(36),
            ForeignKey("mistake_records.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="错题记录ID",
        )
        knowledge_point_id = Column(
            String(36),
            ForeignKey("knowledge_mastery.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="知识点ID",
        )
    else:
        mistake_id = Column(
            UUID(as_uuid=True),
            ForeignKey("mistake_records.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="错题记录ID",
        )
        knowledge_point_id = Column(
            UUID(as_uuid=True),
            ForeignKey("knowledge_mastery.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="知识点ID",
        )

    # 关联属性
    relevance_score = Column(
        Numeric(3, 2),
        nullable=False,
        default=0.5,
        comment="关联度评分（0.0-1.0）",
    )

    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为主要考查知识点",
    )

    error_type = Column(
        String(50),
        nullable=False,
        comment="错误类型（枚举：概念理解/计算/公式使用等）",
    )

    error_reason = Column(
        Text,
        nullable=True,
        comment="错误原因详细描述（AI分析）",
    )

    # AI分析结果
    ai_diagnosis = Column(
        JSON,
        nullable=True,
        comment="AI诊断结果（包含薄弱点、改进建议等）",
    )

    improvement_suggestions = Column(
        JSON,
        nullable=True,
        comment="改进建议列表",
    )

    # 学习状态
    mastered_after_review = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="复习后是否已掌握",
    )

    review_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="针对此知识点的复习次数",
    )

    last_review_result = Column(
        String(20),
        nullable=True,
        comment="最后一次复习结果（correct/incorrect/partial）",
    )

    # 时间信息
    first_error_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="首次出错时间",
    )

    last_review_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后复习时间",
    )

    mastered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="掌握时间",
    )

    def __repr__(self) -> str:
        return f"<MistakeKnowledgePoint(mistake_id='{self.mistake_id}', knowledge_point_id='{self.knowledge_point_id}', error_type='{self.error_type}')>"


class UserKnowledgeGraphSnapshot(BaseModel):
    """
    用户知识图谱快照模型
    定期保存用户的知识图谱状态，用于学情分析和进步追踪
    """

    __tablename__ = "user_knowledge_graph_snapshots"

    # 用户关联
    if is_sqlite:
        user_id = Column(
            String(36),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="用户ID",
        )
    else:
        user_id = Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="用户ID",
        )

    # 快照基本信息
    subject = Column(
        String(20),
        nullable=False,
        index=True,
        comment="学科",
    )

    snapshot_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="快照时间",
    )

    period_type = Column(
        String(20),
        nullable=False,
        comment="周期类型（daily/weekly/monthly/manual）",
    )

    # 知识图谱数据
    graph_data = Column(
        JSON,
        nullable=False,
        comment="知识图谱结构数据（节点+边的JSON）",
    )

    mastery_distribution = Column(
        JSON,
        nullable=False,
        comment="掌握度分布统计（各掌握度区间的知识点数量）",
    )

    weak_knowledge_chains = Column(
        JSON,
        nullable=True,
        comment="识别的薄弱知识链列表",
    )

    # 统计指标
    total_knowledge_points = Column(
        Integer,
        default=0,
        nullable=False,
        comment="知识点总数",
    )

    mastered_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="已掌握知识点数",
    )

    learning_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="学习中知识点数",
    )

    weak_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="薄弱知识点数",
    )

    # AI分析结果
    ai_analysis = Column(
        JSON,
        nullable=True,
        comment="AI学情分析结果（学习画像、建议等）",
    )

    learning_profile = Column(
        JSON,
        nullable=True,
        comment="学习画像（优势/劣势/学习特点等）",
    )

    recommended_focus = Column(
        JSON,
        nullable=True,
        comment="推荐重点学习的知识点列表",
    )

    # 进步追踪
    previous_snapshot_id = Column(
        String(36) if is_sqlite else UUID(as_uuid=True),  # type: ignore[arg-type]
        nullable=True,
        comment="上一次快照ID（用于进步对比）",
    )

    progress_metrics = Column(
        JSON,
        nullable=True,
        comment="进步指标（相比上次快照的变化）",
    )

    def __repr__(self) -> str:
        return f"<UserKnowledgeGraphSnapshot(user_id='{self.user_id}', subject='{self.subject}', snapshot_date='{self.snapshot_date}')>"


class KnowledgePointLearningTrack(BaseModel):
    """
    知识点学习轨迹模型
    记录知识点的详细学习历程，包括每次练习、复习的结果
    """

    __tablename__ = "knowledge_point_learning_tracks"

    # 关联字段
    if is_sqlite:
        user_id = Column(
            String(36),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="用户ID",
        )
        knowledge_point_id = Column(
            String(36),
            ForeignKey("knowledge_mastery.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="知识点ID",
        )
        mistake_id = Column(
            String(36),
            ForeignKey("mistake_records.id", ondelete="SET NULL"),
            nullable=True,
            comment="关联的错题ID（如有）",
        )
    else:
        user_id = Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="用户ID",
        )
        knowledge_point_id = Column(
            UUID(as_uuid=True),
            ForeignKey("knowledge_mastery.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="知识点ID",
        )
        mistake_id = Column(
            UUID(as_uuid=True),
            ForeignKey("mistake_records.id", ondelete="SET NULL"),
            nullable=True,
            comment="关联的错题ID（如有）",
        )

    # 学习活动信息
    activity_type = Column(
        String(20),
        nullable=False,
        comment="活动类型（practice/review/test/mistake_creation）",
    )

    activity_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="活动时间",
    )

    # 学习结果
    result = Column(
        String(20),
        nullable=False,
        comment="结果（correct/incorrect/partial/skipped）",
    )

    mastery_before = Column(
        Numeric(3, 2),
        nullable=True,
        comment="活动前掌握度",
    )

    mastery_after = Column(
        Numeric(3, 2),
        nullable=True,
        comment="活动后掌握度",
    )

    confidence_level = Column(
        Integer,
        nullable=True,
        comment="学生自评信心等级（1-5）",
    )

    # 详细信息
    time_spent = Column(
        Integer,
        nullable=True,
        comment="花费时间（秒）",
    )

    difficulty_level = Column(
        Integer,
        nullable=True,
        comment="题目难度（1-5）",
    )

    error_details = Column(
        JSON,
        nullable=True,
        comment="错误详情（如果有错误）",
    )

    # AI分析
    ai_feedback = Column(
        JSON,
        nullable=True,
        comment="AI即时反馈",
    )

    improvement_detected = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否检测到进步",
    )

    # 元数据
    notes = Column(
        Text,
        nullable=True,
        comment="学生备注",
    )

    def __repr__(self) -> str:
        return f"<KnowledgePointLearningTrack(user_id='{self.user_id}', knowledge_point_id='{self.knowledge_point_id}', activity_type='{self.activity_type}')>"
