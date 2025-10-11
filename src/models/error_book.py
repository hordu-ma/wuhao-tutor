"""
错题本数据模型
包含错题记录和复习记录的数据结构定义
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class ErrorType(str, Enum):
    """错误类型枚举"""
    CONCEPT_ERROR = "理解错误"
    METHOD_ERROR = "方法错误"
    CALCULATION_ERROR = "计算错误"
    EXPRESSION_ERROR = "表达错误"


class MasteryStatus(str, Enum):
    """掌握状态枚举"""
    LEARNING = "learning"  # 学习中
    REVIEWING = "reviewing"  # 复习中
    MASTERED = "mastered"  # 已掌握


class SourceType(str, Enum):
    """错题来源类型"""
    HOMEWORK = "homework"  # 作业
    MANUAL = "manual"  # 手动添加


class ReviewResult(str, Enum):
    """复习结果枚举"""
    CORRECT = "correct"  # 正确
    INCORRECT = "incorrect"  # 错误
    PARTIAL = "partial"  # 部分正确


class ErrorQuestion(BaseModel):
    """
    错题记录模型
    存储学生的错题信息和相关分析数据
    """

    __tablename__ = "error_questions"

    # 用户关联
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 基本信息
    subject = Column(
        String(50),
        nullable=False,
        index=True,
        comment="学科"
    )

    question_content = Column(
        Text,
        nullable=False,
        comment="题目内容"
    )

    student_answer = Column(
        Text,
        comment="学生答案"
    )

    correct_answer = Column(
        Text,
        comment="正确答案"
    )

    # 错误分析
    error_type = Column(
        String(100),
        nullable=False,
        default=ErrorType.CONCEPT_ERROR,
        comment="错误类型"
    )

    error_subcategory = Column(
        String(100),
        comment="错误子分类"
    )

    # 知识点关联 - 存储为JSON数组
    knowledge_points = Column(
        JSON,
        default=list,
        comment="关联知识点"
    )

    # 难度和分类
    difficulty_level = Column(
        Integer,
        default=2,
        comment="难度等级(1-5)"
    )

    # 来源信息
    source_type = Column(
        String(20),
        nullable=False,
        default=SourceType.MANUAL,
        comment="来源类型"
    )

    source_id = Column(
        String(36),
        comment="来源ID"
    )

    # 掌握状态
    mastery_status = Column(
        String(20),
        nullable=False,
        default=MasteryStatus.LEARNING,
        comment="掌握状态"
    )

    # 复习统计
    review_count = Column(
        Integer,
        default=0,
        comment="复习次数"
    )

    correct_count = Column(
        Integer,
        default=0,
        comment="答对次数"
    )

    # 时间管理
    last_review_at = Column(
        DateTime,
        comment="最后复习时间"
    )

    next_review_at = Column(
        DateTime,
        comment="下次复习时间"
    )

    # 标记和标签
    is_starred = Column(
        Boolean,
        default=False,
        comment="是否标星"
    )

    tags = Column(
        JSON,
        default=list,
        comment="自定义标签"
    )

    # 关联关系
    review_records = relationship(
        "ReviewRecord",
        back_populates="error_question",
        cascade="all, delete-orphan"
    )

    @hybrid_property
    def mastery_rate(self) -> float:
        """掌握率计算"""
        if self.review_count == 0:
            return 0.0
        return round(self.correct_count / self.review_count, 2)

    @hybrid_property
    def is_overdue(self) -> bool:
        """是否逾期复习"""
        if not self.next_review_at:
            return False
        return datetime.utcnow() > self.next_review_at

    @hybrid_property
    def overdue_days(self) -> int:
        """逾期天数"""
        if not self.is_overdue:
            return 0
        return (datetime.utcnow() - self.next_review_at).days

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算属性"""
        data = super().to_dict()
        data.update({
            "mastery_rate": self.mastery_rate,
            "is_overdue": self.is_overdue,
            "overdue_days": self.overdue_days,
        })
        return data

    def calculate_next_review_interval(self, performance: float) -> int:
        """
        计算下次复习间隔（天数）
        基于遗忘曲线和个人表现
        """
        # 基础间隔序列（天）
        base_intervals = [1, 3, 7, 15, 30, 90, 180]
        
        # 获取当前应用的基础间隔
        base_interval = base_intervals[min(self.review_count, len(base_intervals) - 1)]
        
        # 性能调整因子 (0.5-1.3)
        performance_factor = 0.5 + (performance * 0.8)
        
        # 难度调整因子 (0.6-1.4)
        difficulty_factor = 1.0 + (self.difficulty_level - 3) * 0.2
        
        # 计算最终间隔
        next_interval = int(base_interval * performance_factor * difficulty_factor)
        
        # 限制在合理范围内
        return max(1, min(next_interval, 180))

    def update_review_schedule(self, performance: float):
        """更新复习计划"""
        interval_days = self.calculate_next_review_interval(performance)
        self.next_review_at = datetime.utcnow() + timedelta(days=interval_days)
        
        # 更新掌握状态
        if performance >= 0.9 and self.review_count >= 3:
            self.mastery_status = MasteryStatus.MASTERED
        elif self.review_count > 0:
            self.mastery_status = MasteryStatus.REVIEWING

    def __repr__(self) -> str:
        return f"<ErrorQuestion(id={self.id}, subject='{self.subject}', mastery_status='{self.mastery_status}')>"


class ReviewRecord(BaseModel):
    """
    复习记录模型
    记录每次复习的详细信息和结果
    """

    __tablename__ = "review_records"

    # 关联字段
    error_question_id = Column(
        String(36),
        ForeignKey("error_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="错题ID"
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 复习结果
    review_result = Column(
        String(20),
        nullable=False,
        comment="复习结果"
    )

    score = Column(
        Integer,
        default=0,
        comment="得分(0-100)"
    )

    # 时间统计
    time_spent = Column(
        Integer,
        comment="用时(秒)"
    )

    # 复习内容
    student_answer = Column(
        Text,
        comment="本次学生答案"
    )

    notes = Column(
        Text,
        comment="复习笔记"
    )

    # 时间记录
    reviewed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="复习时间"
    )

    next_review_at = Column(
        DateTime,
        comment="下次复习时间"
    )

    # 关联关系
    error_question = relationship(
        "ErrorQuestion",
        back_populates="review_records"
    )

    @hybrid_property
    def performance_score(self) -> float:
        """性能得分 (0.0-1.0)"""
        if self.review_result == ReviewResult.CORRECT:
            return 1.0
        elif self.review_result == ReviewResult.PARTIAL:
            return 0.6
        else:
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算属性"""
        data = super().to_dict()
        data.update({
            "performance_score": self.performance_score,
        })
        return data

    def __repr__(self) -> str:
        return f"<ReviewRecord(id={self.id}, result='{self.review_result}', score={self.score})>"


class ErrorClassification(BaseModel):
    """
    错题分类模型
    AI自动分类的结果记录
    """

    __tablename__ = "error_classifications"

    # 关联字段
    error_question_id = Column(
        String(36),
        ForeignKey("error_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="错题ID"
    )

    # 分类结果
    category = Column(
        String(100),
        nullable=False,
        comment="主分类"
    )

    subcategory = Column(
        String(100),
        comment="子分类"
    )

    confidence = Column(
        Float,
        default=0.0,
        comment="置信度(0.0-1.0)"
    )

    # 分类详情
    classification_details = Column(
        JSON,
        comment="分类详细信息"
    )

    classified_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="分类时间"
    )

    def __repr__(self) -> str:
        return f"<ErrorClassification(category='{self.category}', confidence={self.confidence})>"