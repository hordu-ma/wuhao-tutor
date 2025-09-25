"""
学习记录相关数据模型
包含错题记录、复习计划、知识点掌握度等
"""

from typing import Optional
import enum

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, 
    Numeric, String, Text, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class Subject(enum.Enum):
    """学科枚举"""
    MATH = "math"           # 数学
    PHYSICS = "physics"     # 物理
    CHEMISTRY = "chemistry" # 化学
    ENGLISH = "english"     # 英语
    CHINESE = "chinese"     # 语文
    BIOLOGY = "biology"     # 生物
    HISTORY = "history"     # 历史
    GEOGRAPHY = "geography" # 地理
    POLITICS = "politics"   # 政治


class DifficultyLevel(enum.Enum):
    """题目难度等级"""
    BASIC = 1      # 基础
    INTERMEDIATE = 2  # 中等
    ADVANCED = 3   # 困雾
    CHALLENGING = 4   # 挑战
    EXPERT = 5     # 专家级


class MasteryStatus(enum.Enum):
    """掌握状态枚举"""
    LEARNING = "learning"     # 学习中
    REVIEWING = "reviewing"   # 复习中
    MASTERED = "mastered"     # 已掌握
    FORGOTTEN = "forgotten"   # 遗忘


class MistakeRecord(BaseModel):
    """
    错题记录模型
    存储学生的错题信息和AI分析结果
    """
    __tablename__ = "mistake_records"
    
    # 用户关联
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 学科信息
    subject = Column(
        String(20),
        nullable=False,
        index=True,
        comment="学科"
    )
    
    chapter = Column(
        String(100),
        nullable=True,
        comment="章节"
    )
    
    # 题目内容
    title = Column(
        String(200),
        nullable=True,
        comment="题目标题"
    )
    
    image_urls = Column(
        JSON,
        nullable=True,
        comment="题目图片URL列表"
    )
    
    ocr_text = Column(
        Text,
        nullable=True,
        comment="OCR识别的文本内容"
    )
    
    # AI分析结果
    ai_feedback = Column(
        JSON,
        nullable=True,
        comment="AI批改和反馈结果"
    )
    
    knowledge_points = Column(
        JSON,
        nullable=True,
        comment="涉及的知识点列表"
    )
    
    error_reasons = Column(
        JSON,
        nullable=True,
        comment="错误原因分析"
    )
    
    # 题目属性
    difficulty_level = Column(
        Integer,
        default=2,  # INTERMEDIATE
        nullable=False,
        comment="难度等级(1-5)"
    )
    
    estimated_time = Column(
        Integer,
        nullable=True,
        comment="预估解题时间（分钟）"
    )
    
    # 学习状态
    mastery_status = Column(
        String(20),
        default="learning",
        nullable=False,
        comment="掌握状态"
    )
    
    review_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="复习次数"
    )
    
    correct_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="正确次数"
    )
    
    # 时间信息
    last_review_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后复习时间"
    )
    
    next_review_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次复习时间"
    )
    
    # 元数据
    source = Column(
        String(50),
        default="upload",
        nullable=False,
        comment="来源（upload/import/generate）"
    )
    
    tags = Column(
        JSON,
        nullable=True,
        comment="标签列表"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="学生备注"
    )
    
    def __repr__(self) -> str:
        return f"<MistakeRecord(id='{self.id}', subject='{self.subject}', user_id='{self.user_id}')>"


class KnowledgeMastery(BaseModel):
    """
    知识点掌握度模型
    记录学生对各个知识点的掌握情况
    """
    __tablename__ = "knowledge_mastery"
    
    # 用户关联
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 知识点信息
    subject = Column(
        String(20),
        nullable=False,
        index=True,
        comment="学科"
    )
    
    knowledge_point = Column(
        String(100),
        nullable=False,
        comment="知识点名称"
    )
    
    knowledge_point_code = Column(
        String(50),
        nullable=True,
        comment="知识点编码"
    )
    
    # 掌握度指标
    mastery_level = Column(
        Numeric(3, 2),
        default=0.0,
        nullable=False,
        comment="掌握度（0.0-1.0）"
    )
    
    confidence_level = Column(
        Numeric(3, 2),
        default=0.5,
        nullable=False,
        comment="置信度（0.0-1.0）"
    )
    
    # 统计数据
    mistake_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="错误次数"
    )
    
    correct_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="正确次数"
    )
    
    total_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总尝试次数"
    )
    
    # 时间信息
    last_practiced_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后练习时间"
    )
    
    first_mastered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="首次掌握时间"
    )
    
    # 学习轨迹
    learning_curve = Column(
        JSON,
        nullable=True,
        comment="学习曲线数据"
    )
    
    def __repr__(self) -> str:
        return f"<KnowledgeMastery(user_id='{self.user_id}', knowledge_point='{self.knowledge_point}', mastery_level={self.mastery_level})>"


class ReviewSchedule(BaseModel):
    """
    复习计划模型
    基于艾宾浩斯遗忘曲线的复习安排
    """
    __tablename__ = "review_schedule"
    
    # 用户关联
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 关联错题
    mistake_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mistake_records.id"),
        nullable=False,
        index=True,
        comment="错题记录ID"
    )
    
    # 复习安排
    scheduled_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="计划复习时间"
    )
    
    review_type = Column(
        String(20),
        default="ebbinghaus",
        nullable=False,
        comment="复习类型（ebbinghaus/spaced/manual）"
    )
    
    interval_days = Column(
        Integer,
        nullable=False,
        comment="间隔天数"
    )
    
    priority = Column(
        Integer,
        default=3,
        nullable=False,
        comment="优先级（1-5）"
    )
    
    # 完成状态
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="实际完成时间"
    )
    
    result = Column(
        String(20),
        nullable=True,
        comment="复习结果（correct/incorrect/skipped）"
    )
    
    duration_seconds = Column(
        Integer,
        nullable=True,
        comment="花费时长（秒）"
    )
    
    # 下次复习
    next_review_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次复习时间"
    )
    
    # 元数据
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="复习备注"
    )
    
    def __repr__(self) -> str:
        return f"<ReviewSchedule(user_id='{self.user_id}', scheduled_at='{self.scheduled_at}')>"


class StudySession(BaseModel):
    """
    学习会话模型
    记录学生每次的学习活动
    """
    __tablename__ = "study_sessions"
    
    # 用户关联
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 会话信息
    session_type = Column(
        String(20),
        default="practice",
        nullable=False,
        comment="会话类型（practice/review/test）"
    )
    
    subject = Column(
        String(20),
        nullable=True,
        comment="主要学科"
    )
    
    # 时间统计
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="开始时间"
    )
    
    ended_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="结束时间"
    )
    
    duration_seconds = Column(
        Integer,
        nullable=True,
        comment="持续时长（秒）"
    )
    
    # 学习统计
    questions_attempted = Column(
        Integer,
        default=0,
        nullable=False,
        comment="尝试题目数"
    )
    
    questions_correct = Column(
        Integer,
        default=0,
        nullable=False,
        comment="正确题目数"
    )
    
    knowledge_points_practiced = Column(
        JSON,
        nullable=True,
        comment="练习的知识点列表"
    )
    
    # 设备信息
    device_type = Column(
        String(20),
        nullable=True,
        comment="设备类型"
    )
    
    platform = Column(
        String(20),
        nullable=True,
        comment="平台（web/mobile/mini_program）"
    )
    
    def __repr__(self) -> str:
        return f"<StudySession(user_id='{self.user_id}', session_type='{self.session_type}')>"