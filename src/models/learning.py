"""
学习问答相关数据模型
包含会话、问题、答案等模型
"""

import enum

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.core.config import get_settings

from .base import BaseModel

# 获取配置以确定数据库类型
settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI and "sqlite" in str(
    settings.SQLALCHEMY_DATABASE_URI
)  # type: ignore

# 根据数据库类型选择合适的UUID字段类型
if is_sqlite:
    # SQLite使用字符串类型
    UUID_TYPE = String(36)
else:
    # PostgreSQL使用UUID类型
    UUID_TYPE = PG_UUID(as_uuid=True)


class QuestionType(enum.Enum):
    """问题类型枚举"""

    CONCEPT = "concept"  # 概念解释
    PROBLEM_SOLVING = "problem_solving"  # 题目求解
    STUDY_GUIDANCE = "study_guidance"  # 学习指导
    HOMEWORK_HELP = "homework_help"  # 作业辅导
    EXAM_PREPARATION = "exam_preparation"  # 考试准备
    GENERAL_INQUIRY = "general_inquiry"  # 一般询问


class SessionStatus(enum.Enum):
    """会话状态枚举"""

    ACTIVE = "active"  # 活跃
    CLOSED = "closed"  # 已关闭
    ARCHIVED = "archived"  # 已归档


class QuestionStatus(enum.Enum):
    """问题状态枚举"""

    PENDING = "pending"  # 待回答
    ANSWERED = "answered"  # 已回答
    FAILED = "failed"  # 回答失败


class ChatSession(BaseModel):
    """
    学习问答会话模型
    管理用户与AI的对话会话
    """

    __tablename__ = "chat_sessions"

    # 用户信息 - 兼容SQLite和PostgreSQL
    if is_sqlite:
        user_id = Column(
            String(36),
            ForeignKey("users.id"),
            nullable=False,
            index=True,
            comment="用户ID",
        )
    else:
        user_id = Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=False,
            index=True,
            comment="用户ID",
        )

    # 会话基础信息
    title = Column(String(200), nullable=False, comment="会话标题")

    subject = Column(String(50), nullable=True, comment="学科（数学、语文、英语等）")

    grade_level = Column(String(20), nullable=True, comment="学段（初一、高二等）")

    # 会话状态
    status = Column(String(20), default="active", nullable=False, comment="会话状态")

    # 统计信息
    question_count = Column(Integer, default=0, nullable=False, comment="问题总数")

    total_tokens = Column(Integer, default=0, nullable=False, comment="总token消耗")

    # 会话配置
    context_enabled = Column(
        Boolean, default=True, nullable=False, comment="是否启用上下文"
    )

    # 最后活跃时间
    last_active_at = Column(String(50), nullable=True, comment="最后活跃时间")

    # 关联关系
    questions = relationship(
        "Question", back_populates="session", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_chat_session_user_status", "user_id", "status"),
        Index("idx_chat_session_subject_grade", "subject", "grade_level"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}', title='{self.title}')>"


class Question(BaseModel):
    """
    问题模型
    存储用户提出的问题
    """

    __tablename__ = "questions"

    # 会话信息 - 兼容SQLite和PostgreSQL
    if is_sqlite:
        session_id = Column(
            String(36),
            ForeignKey("chat_sessions.id"),
            nullable=False,
            index=True,
            comment="会话ID",
        )
        user_id = Column(
            String(36),
            ForeignKey("users.id"),
            nullable=False,
            index=True,
            comment="用户ID",
        )
    else:
        session_id = Column(
            PG_UUID(as_uuid=True),
            ForeignKey("chat_sessions.id"),
            nullable=False,
            index=True,
            comment="会话ID",
        )
        user_id = Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=False,
            index=True,
            comment="用户ID",
        )

    # 问题内容
    content = Column(Text, nullable=False, comment="问题内容")

    question_type = Column(String(30), nullable=True, comment="问题类型")

    # 问题分类
    subject = Column(String(50), nullable=True, comment="学科")

    topic = Column(String(100), nullable=True, comment="话题/知识点")

    difficulty_level = Column(Integer, nullable=True, comment="难度级别(1-5)")

    # 上下文信息
    context_data = Column(Text, nullable=True, comment="上下文数据(JSON格式)")

    # 图片相关
    has_images = Column(Boolean, default=False, nullable=False, comment="是否包含图片")

    image_urls = Column(Text, nullable=True, comment="图片URL列表(JSON格式)")

    # 处理状态
    is_processed = Column(Boolean, default=False, nullable=False, comment="是否已处理")

    processing_time = Column(Integer, nullable=True, comment="处理耗时(毫秒)")

    # 关联关系
    session = relationship("ChatSession", back_populates="questions")
    answer = relationship(
        "Answer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_question_session_created", "session_id", "created_at"),
        Index("idx_question_user_subject", "user_id", "subject"),
        Index("idx_question_type_topic", "question_type", "topic"),
    )

    def __repr__(self) -> str:
        return f"<Question(id='{self.id}', session_id='{self.session_id}', type='{self.question_type}')>"


class Answer(BaseModel):
    """
    答案模型
    存储AI生成的答案
    """

    __tablename__ = "answers"

    # 问题关联 - 兼容SQLite和PostgreSQL
    if is_sqlite:
        question_id = Column(
            String(36),
            ForeignKey("questions.id"),
            nullable=False,
            unique=True,
            index=True,
            comment="问题ID",
        )
    else:
        question_id = Column(
            PG_UUID(as_uuid=True),
            ForeignKey("questions.id"),
            nullable=False,
            unique=True,
            index=True,
            comment="问题ID",
        )

    # 答案内容
    content = Column(Text, nullable=False, comment="答案内容")

    # AI生成信息
    model_name = Column(String(50), nullable=True, comment="使用的AI模型")

    tokens_used = Column(Integer, nullable=True, comment="消耗的token数")

    generation_time = Column(Integer, nullable=True, comment="生成耗时(毫秒)")

    # 质量评估
    confidence_score = Column(Integer, nullable=True, comment="置信度分数(0-100)")

    # 用户反馈
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")

    user_feedback = Column(Text, nullable=True, comment="用户反馈")

    is_helpful = Column(Boolean, nullable=True, comment="是否有帮助")

    # 推荐相关
    related_topics = Column(Text, nullable=True, comment="相关话题(JSON格式)")

    suggested_questions = Column(Text, nullable=True, comment="推荐问题(JSON格式)")

    # 关联关系
    question = relationship("Question", back_populates="answer")

    def __repr__(self) -> str:
        return f"<Answer(id='{self.id}', question_id='{self.question_id}', model='{self.model_name}')>"


class LearningAnalytics(BaseModel):
    """
    学习分析模型
    分析用户的学习模式和进度
    """

    __tablename__ = "learning_analytics"

    # 用户信息 - 兼容SQLite和PostgreSQL
    if is_sqlite:
        user_id = Column(
            String(36),
            ForeignKey("users.id"),
            nullable=False,
            unique=True,
            index=True,
            comment="用户ID",
        )
    else:
        user_id = Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=False,
            unique=True,
            index=True,
            comment="用户ID",
        )

    # 统计数据
    total_questions = Column(Integer, default=0, nullable=False, comment="总提问数")

    total_sessions = Column(Integer, default=0, nullable=False, comment="总会话数")

    active_subjects = Column(Text, nullable=True, comment="活跃学科统计(JSON格式)")

    question_types_stats = Column(Text, nullable=True, comment="问题类型统计(JSON格式)")

    # 学习特征
    preferred_subjects = Column(Text, nullable=True, comment="偏好学科(JSON格式)")

    difficulty_preference = Column(Integer, nullable=True, comment="难度偏好(1-5)")

    learning_style = Column(String(50), nullable=True, comment="学习风格")

    # 学习质量
    avg_rating = Column(Integer, nullable=True, comment="平均评分")

    positive_feedback_rate = Column(Integer, nullable=True, comment="正面反馈率(%)")

    # 时间模式
    most_active_time = Column(String(20), nullable=True, comment="最活跃时间段")

    weekly_pattern = Column(Text, nullable=True, comment="周学习模式(JSON格式)")

    # 学习进度
    knowledge_mastery = Column(Text, nullable=True, comment="知识掌握度(JSON格式)")

    improvement_areas = Column(Text, nullable=True, comment="待提升领域(JSON格式)")

    # 最后更新时间
    last_analyzed_at = Column(String(50), nullable=True, comment="最后分析时间")

    def __repr__(self) -> str:
        return f"<LearningAnalytics(user_id='{self.user_id}', total_questions={self.total_questions})>"
