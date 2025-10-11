"""
学习问答相关的Pydantic Schema模型
包含请求、响应、会话管理等数据结构
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, validator


class QuestionType(str, Enum):
    """问题类型枚举"""

    CONCEPT = "concept"
    PROBLEM_SOLVING = "problem_solving"
    STUDY_GUIDANCE = "study_guidance"
    HOMEWORK_HELP = "homework_help"
    EXAM_PREPARATION = "exam_preparation"
    GENERAL_INQUIRY = "general_inquiry"


class SessionStatus(str, Enum):
    """会话状态枚举"""

    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class DifficultyLevel(int, Enum):
    """难度级别枚举"""

    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class SubjectType(str, Enum):
    """学科类型枚举"""

    MATH = "math"
    CHINESE = "chinese"
    ENGLISH = "english"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"


# ========== 基础Schema模型 ==========


class LearningContextBase(BaseModel):
    """学习上下文基础模型"""

    user_id: Optional[str] = None
    subject: Optional[SubjectType] = None
    grade_level: Optional[str] = None
    session_id: Optional[str] = None
    related_homework_ids: Optional[List[str]] = Field(default_factory=list)
    knowledge_points: Optional[List[str]] = Field(default_factory=list)


class QuestionBase(BaseModel):
    """问题基础模型"""

    content: str = Field(..., min_length=1, max_length=5000, description="问题内容")
    question_type: Optional[QuestionType] = Field(
        default=QuestionType.GENERAL_INQUIRY, description="问题类型"
    )
    subject: Optional[SubjectType] = Field(None, description="学科")
    topic: Optional[str] = Field(None, max_length=100, description="话题/知识点")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="难度级别")
    image_urls: Optional[List[str]] = Field(
        default_factory=list, description="图片URL列表"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="上下文数据"
    )


class AnswerBase(BaseModel):
    """答案基础模型"""

    content: str = Field(..., description="答案内容")
    confidence_score: Optional[int] = Field(
        None, ge=0, le=100, description="置信度分数"
    )
    related_topics: Optional[List[str]] = Field(
        default_factory=list, description="相关话题"
    )
    suggested_questions: Optional[List[str]] = Field(
        default_factory=list, description="推荐问题"
    )


class SessionBase(BaseModel):
    """会话基础模型"""

    title: str = Field(..., min_length=1, max_length=200, description="会话标题")
    subject: Optional[SubjectType] = Field(None, description="学科")
    grade_level: Optional[str] = Field(None, description="学段")
    context_enabled: bool = Field(default=True, description="是否启用上下文")


# ========== 请求Schema模型 ==========


class AskQuestionRequest(QuestionBase):
    """提问请求"""

    session_id: Optional[str] = Field(
        None, description="会话ID，如果不提供则创建新会话"
    )
    use_context: bool = Field(default=True, description="是否使用学习上下文")
    include_history: bool = Field(default=True, description="是否包含历史对话")
    max_history: int = Field(default=10, ge=0, le=50, description="最大历史消息数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "什么是二次函数的顶点式？",
                "question_type": "concept",
                "subject": "math",
                "topic": "二次函数",
                "difficulty_level": 2,
                "session_id": None,
                "use_context": True,
                "include_history": True,
            }
        }
    )


class CreateSessionRequest(SessionBase):
    """创建会话请求"""

    initial_question: Optional[str] = Field(None, description="初始问题")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "数学学习讨论",
                "subject": "math",
                "grade_level": "junior_2",
                "context_enabled": True,
                "initial_question": "请帮我复习二次函数",
            }
        }
    )


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[SessionStatus] = None
    context_enabled: Optional[bool] = None


class FeedbackRequest(BaseModel):
    """反馈请求"""

    question_id: str = Field(..., description="问题ID")
    rating: int = Field(..., ge=1, le=5, description="评分(1-5)")
    feedback: Optional[str] = Field(None, max_length=1000, description="反馈内容")
    is_helpful: bool = Field(..., description="是否有帮助")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "rating": 4,
                "feedback": "解释很清楚，但希望有更多例题",
                "is_helpful": True,
            }
        }
    )


# ========== 响应Schema模型 ==========


class QuestionResponse(QuestionBase):
    """问题响应"""

    id: str
    session_id: str
    user_id: str
    is_processed: bool
    processing_time: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "session_id", "user_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将UUID对象转换为字符串"""
        if v is None:
            return None
        return str(v)

    @field_validator("image_urls", mode="before")
    @classmethod
    def parse_image_urls(cls, v):
        """解析image_urls字段，将JSON字符串转换为列表"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except (json.JSONDecodeError, ValueError):
                return []
        if isinstance(v, list):
            return v
        return []

    @field_validator("context_data", mode="before")
    @classmethod
    def parse_context_data(cls, v):
        """解析context_data字段，将JSON字符串转换为字典"""
        if v is None:
            return {}
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        if isinstance(v, dict):
            return v
        return {}

    model_config = ConfigDict(from_attributes=True)


class AnswerResponse(AnswerBase):
    """答案响应"""

    id: str
    question_id: str
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    generation_time: Optional[int] = None
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    is_helpful: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "question_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将UUID对象转换为字符串"""
        if v is None:
            return None
        return str(v)

    @field_validator("related_topics", mode="before")
    @classmethod
    def parse_related_topics(cls, v):
        """解析相关话题JSON字符串"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(v, list):
            return v
        return []

    @field_validator("suggested_questions", mode="before")
    @classmethod
    def parse_suggested_questions(cls, v):
        """解析推荐问题JSON字符串"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(v, list):
            return v
        return []

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(SessionBase):
    """会话响应"""

    id: str
    user_id: str
    status: SessionStatus
    question_count: int
    total_tokens: int
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将UUID对象转换为字符串"""
        if v is None:
            return None
        return str(v)

    model_config = ConfigDict(from_attributes=True)


class QuestionAnswerPair(BaseModel):
    """问答对"""

    question: QuestionResponse
    answer: Optional[AnswerResponse] = None


class AskQuestionResponse(BaseModel):
    """提问响应"""

    question: QuestionResponse
    answer: AnswerResponse
    session: SessionResponse
    processing_time: int = Field(..., description="总处理时间(毫秒)")
    tokens_used: int = Field(..., description="本次消耗的token数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "content": "什么是二次函数的顶点式？",
                    "question_type": "concept",
                    "subject": "math",
                },
                "answer": {
                    "id": "456e7890-e89b-12d3-a456-426614174001",
                    "content": "二次函数的顶点式是y=a(x-h)²+k...",
                    "confidence_score": 95,
                },
                "session": {
                    "id": "789e1234-e89b-12d3-a456-426614174002",
                    "title": "数学学习讨论",
                    "status": "active",
                },
                "processing_time": 1500,
                "tokens_used": 245,
            }
        }
    )


# ========== 查询和分页Schema模型 ==========


class SessionListQuery(BaseModel):
    """会话列表查询"""

    status: Optional[str] = None
    subject: Optional[str] = None
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")

    @validator("status", pre=True)
    def validate_status(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return SessionStatus(v)
            except ValueError:
                raise ValueError(f"Invalid status: {v}")
        return v

    @validator("subject", pre=True)
    def validate_subject(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return SubjectType(v)
            except ValueError:
                raise ValueError(f"Invalid subject: {v}")
        return v


class QuestionHistoryQuery(BaseModel):
    """问题历史查询"""

    session_id: Optional[str] = None
    subject: Optional[str] = None
    question_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator("subject", pre=True)
    def validate_subject(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return SubjectType(v)
            except ValueError:
                raise ValueError(f"Invalid subject: {v}")
        return v

    @validator("question_type", pre=True)
    def validate_question_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return QuestionType(v)
            except ValueError:
                raise ValueError(f"Invalid question_type: {v}")
        return v


class PaginatedResponse(BaseModel):
    """分页响应基础模型"""

    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class SessionListResponse(PaginatedResponse):
    """会话列表响应"""

    items: List[SessionResponse] = Field(..., description="会话列表")


class QuestionHistoryResponse(PaginatedResponse):
    """问题历史响应"""

    items: List[QuestionAnswerPair] = Field(..., description="问答对列表")


# ========== 学习分析Schema模型 ==========


class SubjectStats(BaseModel):
    """学科统计"""

    subject: SubjectType
    question_count: int
    avg_difficulty: float
    mastery_level: int = Field(..., ge=0, le=100, description="掌握度百分比")


class LearningPattern(BaseModel):
    """学习模式"""

    most_active_hour: int = Field(..., ge=0, le=23, description="最活跃小时")
    most_active_day: int = Field(..., ge=0, le=6, description="最活跃星期(0=周日)")
    avg_session_length: int = Field(..., description="平均会话时长(分钟)")
    preferred_difficulty: DifficultyLevel


class LearningAnalyticsResponse(BaseModel):
    """学习分析响应"""

    user_id: str
    total_questions: int
    total_sessions: int
    subject_stats: List[SubjectStats]
    learning_pattern: LearningPattern
    avg_rating: float
    positive_feedback_rate: int = Field(..., ge=0, le=100)
    improvement_suggestions: List[str]
    knowledge_gaps: List[str]
    last_analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 推荐和建议Schema模型 ==========


class RecommendedQuestion(BaseModel):
    """推荐问题"""

    content: str
    subject: SubjectType
    topic: str
    difficulty_level: DifficultyLevel
    reason: str = Field(..., description="推荐理由")


class StudyPlan(BaseModel):
    """学习计划"""

    title: str
    description: str
    subjects: List[SubjectType]
    estimated_hours: int
    tasks: List[str]
    priority: int = Field(..., ge=1, le=5)


class RecommendationResponse(BaseModel):
    """推荐响应"""

    recommended_questions: List[RecommendedQuestion]
    study_plans: List[StudyPlan]
    focus_areas: List[str]
    next_topics: List[str]


# ========== 统计和报表Schema模型 ==========


class DailyStats(BaseModel):
    """日统计"""

    date: str
    question_count: int
    session_count: int
    total_tokens: int
    avg_rating: float


class WeeklyReport(BaseModel):
    """周报告"""

    week_start: str
    week_end: str
    daily_stats: List[DailyStats]
    top_subjects: List[str]
    total_study_time: int = Field(..., description="总学习时间(分钟)")
    progress_summary: str


class MonthlyReport(BaseModel):
    """月报告"""

    month: str
    weekly_reports: List[WeeklyReport]
    monthly_goals: List[str]
    achievements: List[str]
    areas_for_improvement: List[str]
