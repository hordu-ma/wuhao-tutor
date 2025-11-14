"""
作业相关数据模型
包含作业、提交、批改等核心业务模型
"""

import enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class SubjectType(enum.Enum):
    """学科类型枚举"""

    CHINESE = "chinese"  # 语文
    MATH = "math"  # 数学
    ENGLISH = "english"  # 英语
    PHYSICS = "physics"  # 物理
    CHEMISTRY = "chemistry"  # 化学
    BIOLOGY = "biology"  # 生物
    HISTORY = "history"  # 历史
    GEOGRAPHY = "geography"  # 地理
    POLITICS = "politics"  # 政治
    OTHER = "other"  # 其他


class HomeworkType(enum.Enum):
    """作业类型枚举"""

    DAILY = "daily"  # 日常作业
    EXAM = "exam"  # 考试
    EXERCISE = "exercise"  # 练习题
    TEST = "test"  # 测验
    REVIEW = "review"  # 复习作业


class DifficultyLevel(enum.Enum):
    """难度级别枚举"""

    EASY = "easy"  # 简单
    MEDIUM = "medium"  # 中等
    HARD = "hard"  # 困难


class SubmissionStatus(enum.Enum):
    """提交状态枚举"""

    UPLOADED = "uploaded"  # 已上传
    PROCESSING = "processing"  # 处理中
    REVIEWED = "reviewed"  # 已批改
    FAILED = "failed"  # 失败
    ARCHIVED = "archived"  # 已归档


class ReviewStatus(enum.Enum):
    """批改状态枚举"""

    PENDING = "pending"  # 待批改
    IN_PROGRESS = "in_progress"  # 批改中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 批改失败


class Homework(BaseModel):
    """
    作业模板模型
    定义作业的基本信息和要求
    """

    __tablename__ = "homework"

    # 基础信息
    title = Column(String(200), nullable=False, comment="作业标题")

    description = Column(Text, nullable=True, comment="作业描述")

    subject = Column(String(20), nullable=False, index=True, comment="学科")

    homework_type = Column(
        String(20), default="daily", nullable=False, comment="作业类型"
    )

    difficulty_level = Column(
        Integer, default=2, nullable=False, comment="难度级别: 1=easy, 2=medium, 3=hard"
    )

    # 学段和范围
    grade_level = Column(String(20), nullable=False, index=True, comment="适用学段")

    chapter = Column(String(100), nullable=True, comment="章节")

    knowledge_points = Column(JSON, nullable=True, comment="知识点列表（JSON格式）")

    # 时间信息
    estimated_duration = Column(Integer, nullable=True, comment="预计完成时间（分钟）")

    deadline = Column(DateTime(timezone=True), nullable=True, comment="截止时间")

    # 创建者信息
    creator_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="创建者ID（教师）",
    )

    creator_name = Column(String(50), nullable=True, comment="创建者姓名")

    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    is_template = Column(Boolean, default=False, nullable=False, comment="是否为模板")

    # 统计信息
    total_submissions = Column(Integer, default=0, nullable=False, comment="总提交数")

    avg_score = Column(Float, nullable=True, comment="平均分")

    # 关联关系
    submissions = relationship(
        "HomeworkSubmission", back_populates="homework", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_homework_subject_grade", "subject", "grade_level"),
        Index("idx_homework_creator_active", "creator_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Homework(id='{self.id}', title='{self.title}', subject='{self.subject}')>"


class HomeworkSubmission(BaseModel):
    """
    作业提交模型
    学生提交的作业实例
    """

    __tablename__ = "homework_submissions"

    # 关联信息
    homework_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("homework.id"),
        nullable=False,
        index=True,
        comment="作业ID",
    )

    student_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="学生ID",
    )

    student_name = Column(String(50), nullable=False, comment="学生姓名")

    # 提交信息
    submission_title = Column(String(200), nullable=True, comment="提交标题")

    submission_note = Column(Text, nullable=True, comment="提交备注")

    # 状态信息
    status = Column(
        String(20), default="uploaded", nullable=False, index=True, comment="提交状态"
    )

    submitted_at = Column(DateTime(timezone=True), nullable=True, comment="提交时间")

    # 批改信息
    total_score = Column(Float, nullable=True, comment="总分")

    accuracy_rate = Column(Float, nullable=True, comment="正确率")

    completion_time = Column(Integer, nullable=True, comment="完成时间（分钟）")

    # AI批改结果
    ai_review_data = Column(JSON, nullable=True, comment="AI批改详细数据（JSON格式）")

    # 学习分析
    weak_knowledge_points = Column(
        JSON, nullable=True, comment="薄弱知识点（JSON格式）"
    )

    improvement_suggestions = Column(
        JSON, nullable=True, comment="改进建议（JSON格式）"
    )

    # 元数据
    device_info = Column(JSON, nullable=True, comment="提交设备信息（JSON格式）")

    ip_address = Column(String(45), nullable=True, comment="IP地址")

    # 关联关系
    homework = relationship("Homework", back_populates="submissions")
    images = relationship(
        "HomeworkImage", back_populates="submission", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "HomeworkReview", back_populates="submission", cascade="all, delete-orphan"
    )

    # 约束和索引
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_homework_student"),
        Index("idx_submission_student_status", "student_id", "status"),
        Index("idx_submission_homework_submitted", "homework_id", "submitted_at"),
    )

    def __repr__(self) -> str:
        return f"<HomeworkSubmission(id='{self.id}', homework_id='{self.homework_id}', student_name='{self.student_name}')>"

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, "status", "") == SubmissionStatus.REVIEWED.value)

    @property
    def is_processing(self) -> bool:
        """是否正在处理中"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, "status", "") == SubmissionStatus.PROCESSING.value)

    @property
    def score_percentage(self) -> Optional[float]:
        """分数百分比"""
        # 类型检查器修复：强制类型转换
        try:
            total_score = getattr(self, "total_score", None)
            if total_score is not None:
                score_val = float(total_score)
                if score_val > 0:
                    return min(score_val, 100.0)
        except (ValueError, TypeError):
            pass
        return None


class HomeworkImage(BaseModel):
    """
    作业图片模型
    存储作业图片信息和OCR结果
    """

    __tablename__ = "homework_images"

    # 关联信息
    submission_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("homework_submissions.id"),
        nullable=False,
        index=True,
        comment="提交ID",
    )

    # 图片信息
    original_filename = Column(String(255), nullable=False, comment="原始文件名")

    file_path = Column(String(500), nullable=False, comment="文件存储路径")

    file_url = Column(String(500), nullable=True, comment="文件访问URL")

    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")

    mime_type = Column(String(100), nullable=False, comment="MIME类型")

    # 图片属性
    image_width = Column(Integer, nullable=True, comment="图片宽度")

    image_height = Column(Integer, nullable=True, comment="图片高度")

    # 排序和展示
    display_order = Column(Integer, default=0, nullable=False, comment="显示顺序")

    is_primary = Column(Boolean, default=False, nullable=False, comment="是否为主图")

    # OCR处理结果
    ocr_text = Column(Text, nullable=True, comment="OCR识别文本")

    ocr_confidence = Column(Float, nullable=True, comment="OCR识别置信度")

    ocr_data = Column(JSON, nullable=True, comment="OCR详细数据（JSON格式）")

    ocr_processed_at = Column(
        DateTime(timezone=True), nullable=True, comment="OCR处理时间"
    )

    # 状态信息
    is_processed = Column(Boolean, default=False, nullable=False, comment="是否已处理")

    processing_error = Column(Text, nullable=True, comment="处理错误信息")

    # 新增: OCR增强字段
    retry_count = Column(Integer, default=0, nullable=False, comment="OCR重试次数")

    quality_score = Column(Float, nullable=True, comment="图片质量分数(0-100)")

    # 关联关系
    submission = relationship("HomeworkSubmission", back_populates="images")

    # 索引
    __table_args__ = (
        Index("idx_image_submission_order", "submission_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<HomeworkImage(id='{self.id}', filename='{self.original_filename}')>"

    @property
    def is_image(self) -> bool:
        """是否为图片文件"""
        # 类型检查器修复：强制类型转换
        mime_type = str(getattr(self, "mime_type", ""))
        return bool(mime_type.startswith("image/"))

    @property
    def file_extension(self) -> str:
        """文件扩展名"""
        # 类型检查器修复：强制类型转换
        filename = str(getattr(self, "original_filename", ""))
        return filename.split(".")[-1].lower() if "." in filename else ""


class HomeworkReview(BaseModel):
    """
    作业批改结果模型
    存储AI批改的详细结果
    """

    __tablename__ = "homework_reviews"

    # 关联信息
    submission_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("homework_submissions.id"),
        nullable=False,
        index=True,
        comment="提交ID",
    )

    # 批改基本信息
    review_type = Column(
        String(20),
        default="ai_auto",
        nullable=False,
        comment="批改类型（ai_auto/manual/hybrid）",
    )

    reviewer_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="人工批改者ID",
    )

    reviewer_name = Column(String(50), nullable=True, comment="批改者姓名")

    # 批改状态
    status = Column(
        String(20), default="pending", nullable=False, index=True, comment="批改状态"
    )

    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始批改时间")

    completed_at = Column(
        DateTime(timezone=True), nullable=True, comment="完成批改时间"
    )

    processing_duration = Column(Integer, nullable=True, comment="处理时长（秒）")

    # 批改结果
    total_score = Column(Float, nullable=True, comment="总分")

    max_score = Column(Float, default=100.0, nullable=False, comment="满分")

    accuracy_rate = Column(Float, nullable=True, comment="正确率")

    # 详细评价
    overall_comment = Column(Text, nullable=True, comment="总体评价")

    strengths = Column(JSON, nullable=True, comment="优点列表（JSON格式）")

    weaknesses = Column(JSON, nullable=True, comment="不足列表（JSON格式）")

    suggestions = Column(JSON, nullable=True, comment="改进建议（JSON格式）")

    # 知识点分析
    knowledge_point_analysis = Column(
        JSON, nullable=True, comment="知识点分析（JSON格式）"
    )

    difficulty_analysis = Column(JSON, nullable=True, comment="难度分析（JSON格式）")

    # 题目级别评价
    question_reviews = Column(JSON, nullable=True, comment="题目级别评价（JSON格式）")

    # AI服务信息
    ai_model_version = Column(String(50), nullable=True, comment="AI模型版本")

    ai_confidence_score = Column(Float, nullable=True, comment="AI置信度分数")

    ai_processing_tokens = Column(Integer, nullable=True, comment="AI处理token数")

    # 质量控制
    quality_score = Column(Float, nullable=True, comment="批改质量分数")

    needs_manual_review = Column(
        Boolean, default=False, nullable=False, comment="是否需要人工复核"
    )

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")

    error_details = Column(JSON, nullable=True, comment="错误详情（JSON格式）")

    # 关联关系
    submission = relationship("HomeworkSubmission", back_populates="reviews")

    # 索引
    __table_args__ = (
        Index("idx_review_submission_status", "submission_id", "status"),
        Index("idx_review_completed", "completed_at"),
    )

    def __repr__(self) -> str:
        return f"<HomeworkReview(id='{self.id}', submission_id='{self.submission_id}', status='{self.status}')>"

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, "status", "") == ReviewStatus.COMPLETED.value)

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        # 类型检查器修复：强制类型转换
        return bool(getattr(self, "status", "") == ReviewStatus.PENDING.value)

    @property
    def score_percentage(self) -> Optional[float]:
        """分数百分比"""
        # 类型检查器修复：强制类型转换
        try:
            total_score = getattr(self, "total_score", None)
            max_score = getattr(self, "max_score", None)
            if total_score is not None and max_score is not None:
                total_val = float(total_score)
                max_val = float(max_score)
                if max_val > 0:
                    return (total_val / max_val) * 100
        except (ValueError, TypeError):
            pass
        return None

    @property
    def grade_level(self) -> Optional[str]:
        """成绩等级"""
        percentage = self.score_percentage
        if percentage is None:
            return None

        if percentage >= 90:
            return "优秀"
        elif percentage >= 80:
            return "良好"
        elif percentage >= 70:
            return "中等"
        elif percentage >= 60:
            return "及格"
        else:
            return "不及格"
