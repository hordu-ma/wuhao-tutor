"""
知识图谱相关数据模型
包含知识节点、关系、学习路径等
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import BaseModel


class NodeType(enum.Enum):
    """节点类型枚举"""

    SUBJECT = "subject"  # 学科
    CHAPTER = "chapter"  # 章节
    SECTION = "section"  # 小节
    CONCEPT = "concept"  # 概念
    SKILL = "skill"  # 技能
    PROBLEM_TYPE = "problem_type"  # 题型


class RelationType(enum.Enum):
    """关系类型枚举"""

    PREREQUISITE = "prerequisite"  # 前置关系
    CONTAINS = "contains"  # 包含关系
    SIMILAR = "similar"  # 相似关系
    APPLIES_TO = "applies_to"  # 应用关系
    DERIVES_FROM = "derives_from"  # 派生关系


class KnowledgeNode(BaseModel):
    """
    知识节点模型
    表示知识图谱中的各个知识点
    """

    __tablename__ = "knowledge_nodes"

    # 基础信息
    name = Column(String(100), nullable=False, comment="节点名称")

    code = Column(
        String(50), unique=True, nullable=False, comment="节点编码（用于唯一标识）"
    )

    node_type = Column(String(20), nullable=False, comment="节点类型")

    subject = Column(String(20), nullable=False, index=True, comment="所属学科")

    # 层级信息
    level = Column(Integer, default=1, nullable=False, comment="层级（1-10）")

    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id"),
        nullable=True,
        comment="父节点ID",
    )

    # 内容描述
    description = Column(Text, nullable=True, comment="详细描述")

    keywords = Column(JSON, nullable=True, comment="关键词列表")

    examples = Column(JSON, nullable=True, comment="示例列表")

    # 难度和重要性
    difficulty = Column(Integer, default=3, nullable=False, comment="难度等级（1-5）")

    importance = Column(Integer, default=3, nullable=False, comment="重要性（1-5）")

    # 学习统计
    average_mastery = Column(
        Numeric(3, 2), default=0.0, nullable=False, comment="平均掌握度"
    )

    learning_count = Column(Integer, default=0, nullable=False, comment="学习人数")

    mistake_rate = Column(Numeric(3, 2), default=0.0, nullable=False, comment="错误率")

    # 元数据
    tags = Column(JSON, nullable=True, comment="标签列表")

    external_links = Column(JSON, nullable=True, comment="外部链接")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 索引
    __table_args__ = (
        Index("idx_knowledge_nodes_subject_level", "subject", "level"),
        Index("idx_knowledge_nodes_parent", "parent_id"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeNode(id='{self.id}', name='{self.name}', subject='{self.subject}')>"


class KnowledgeRelation(BaseModel):
    """
    知识点关系模型
    表示知识点之间的关联关系
    """

    __tablename__ = "knowledge_relations"

    # 关系端点
    from_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id"),
        nullable=False,
        index=True,
        comment="源节点ID",
    )

    to_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id"),
        nullable=False,
        index=True,
        comment="目标节点ID",
    )

    # 关系类型
    relation_type = Column(String(20), nullable=False, comment="关系类型")

    # 关系强度
    weight = Column(
        Numeric(3, 2), default=1.0, nullable=False, comment="关系权重（0.0-1.0）"
    )

    # 方向性
    is_bidirectional = Column(
        Boolean, default=False, nullable=False, comment="是否双向关系"
    )

    # 元数据
    description = Column(Text, nullable=True, comment="关系描述")

    evidence_count = Column(Integer, default=0, nullable=False, comment="支持证据数量")

    confidence = Column(Numeric(3, 2), default=0.8, nullable=False, comment="置信度")

    # 索引
    __table_args__ = (
        Index("idx_knowledge_relations_from_to", "from_node_id", "to_node_id"),
        Index("idx_knowledge_relations_type", "relation_type"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeRelation(from_node_id='{self.from_node_id}', to_node_id='{self.to_node_id}', type='{self.relation_type}')>"


class LearningPath(BaseModel):
    """
    学习路径模型
    为学生规划个性化的学习顺序
    """

    __tablename__ = "learning_paths"

    # 基础信息
    name = Column(String(100), nullable=False, comment="路径名称")

    description = Column(Text, nullable=True, comment="路径描述")

    subject = Column(String(20), nullable=False, index=True, comment="目标学科")

    # 目标设置
    target_level = Column(
        Integer, default=5, nullable=False, comment="目标掌握水平（1-10）"
    )

    difficulty_preference = Column(
        Integer, default=3, nullable=False, comment="难度偏好（1-5）"
    )

    # 路径内容
    node_sequence = Column(JSON, nullable=False, comment="节点学习序列")

    estimated_hours = Column(Integer, nullable=True, comment="预计学习时长（小时）")

    # 适用条件
    prerequisite_nodes = Column(JSON, nullable=True, comment="前置知识节点")

    target_grade_levels = Column(JSON, nullable=True, comment="适用年级")

    # 统计信息
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")

    average_completion_rate = Column(
        Numeric(3, 2), default=0.0, nullable=False, comment="平均完成率"
    )

    average_satisfaction = Column(
        Numeric(3, 2), default=0.0, nullable=False, comment="平均满意度"
    )

    # 版本控制
    version = Column(String(10), default="1.0", nullable=False, comment="版本号")

    is_published = Column(Boolean, default=False, nullable=False, comment="是否已发布")

    created_by = Column(UUID(as_uuid=True), nullable=True, comment="创建者ID")

    def __repr__(self) -> str:
        return f"<LearningPath(id='{self.id}', name='{self.name}', subject='{self.subject}')>"


class UserLearningPath(BaseModel):
    """
    用户学习路径模型
    记录学生的个性化学习路径进度
    """

    __tablename__ = "user_learning_paths"

    # 用户关联
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 路径关联
    learning_path_id = Column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id"),
        nullable=False,
        index=True,
        comment="学习路径ID",
    )

    # 进度跟踪
    current_node_index = Column(
        Integer, default=0, nullable=False, comment="当前节点索引"
    )

    completed_nodes = Column(JSON, nullable=True, comment="已完成节点列表")

    progress_percentage = Column(
        Numeric(5, 2), default=0.0, nullable=False, comment="完成百分比"
    )

    # 时间统计
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="开始时间",
    )

    last_accessed_at = Column(
        DateTime(timezone=True), nullable=True, comment="最后访问时间"
    )

    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")

    total_study_minutes = Column(
        Integer, default=0, nullable=False, comment="总学习时长（分钟）"
    )

    # 状态信息
    status = Column(
        String(20),
        default="active",
        nullable=False,
        comment="状态（active/paused/completed/abandoned）",
    )

    # 个性化调整
    difficulty_adjustment = Column(
        Numeric(3, 2), default=1.0, nullable=False, comment="难度调整系数"
    )

    custom_sequence = Column(JSON, nullable=True, comment="个性化调整后的序列")

    # 反馈
    satisfaction_rating = Column(Integer, nullable=True, comment="满意度评分（1-5）")

    feedback_notes = Column(Text, nullable=True, comment="反馈备注")

    def __repr__(self) -> str:
        return f"<UserLearningPath(user_id='{self.user_id}', learning_path_id='{self.learning_path_id}', progress={self.progress_percentage}%)>"


class KnowledgeGraph(BaseModel):
    """
    知识图谱模型
    整个知识图谱的元信息
    """

    __tablename__ = "knowledge_graphs"

    # 基础信息
    name = Column(String(100), nullable=False, comment="图谱名称")

    description = Column(Text, nullable=True, comment="图谱描述")

    subject = Column(String(20), nullable=False, index=True, comment="学科")

    # 统计信息
    node_count = Column(Integer, default=0, nullable=False, comment="节点数量")

    relation_count = Column(Integer, default=0, nullable=False, comment="关系数量")

    max_depth = Column(Integer, default=0, nullable=False, comment="最大深度")

    # 版本控制
    version = Column(String(10), default="1.0", nullable=False, comment="版本号")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 元数据
    config = Column(JSON, nullable=True, comment="配置信息")

    created_by = Column(UUID(as_uuid=True), nullable=True, comment="创建者ID")

    def __repr__(self) -> str:
        return f"<KnowledgeGraph(id='{self.id}', name='{self.name}', subject='{self.subject}')>"
