"""
阿里云百炼智能体相关的Pydantic模型

包含：
- AI聊天对话相关模型
- 作业批改请求/响应模型
- 学习问答请求/响应模型
- 学情分析请求/响应模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


# ============================================================================
# 基础枚举和类型定义
# ============================================================================

class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Subject(str, Enum):
    """学科枚举"""
    MATH = "数学"
    CHINESE = "语文"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"


class DifficultyLevel(str, Enum):
    """难度等级枚举"""
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"
    VERY_HARD = "很难"


class GradeLevel(int, Enum):
    """年级枚举"""
    GRADE_7 = 7   # 七年级
    GRADE_8 = 8   # 八年级
    GRADE_9 = 9   # 九年级
    GRADE_10 = 10 # 高一
    GRADE_11 = 11 # 高二
    GRADE_12 = 12 # 高三


# ============================================================================
# 基础Schema
# ============================================================================

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole
    content: str

    class Config:
        use_enum_values = True


class AIContext(BaseModel):
    """AI调用上下文"""
    user_id: Optional[str] = None
    subject: Optional[Subject] = None
    grade_level: Optional[GradeLevel] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


# ============================================================================
# 通用AI响应模型
# ============================================================================

class ChatCompletionRequest(BaseModel):
    """聊天补全请求"""
    messages: List[ChatMessage]
    context: Optional[AIContext] = None
    max_tokens: Optional[int] = Field(default=1500, ge=1, le=4000)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)

    @validator('messages')
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError('messages不能为空')
        return v


class ChatCompletionResponse(BaseModel):
    """聊天补全响应"""
    content: str
    tokens_used: int = 0
    processing_time: float = 0.0
    model: str = ""
    request_id: str = ""
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# 作业批改相关模型
# ============================================================================

class HomeworkCorrectionRequest(BaseModel):
    """作业批改请求"""
    user_id: str = Field(..., description="用户ID")
    subject: Subject = Field(..., description="学科")
    grade_level: GradeLevel = Field(..., description="年级")
    homework_text: str = Field(..., description="OCR识别的题目文本")
    answer_text: str = Field(..., description="学生答案文本")
    image_urls: List[str] = Field(default_factory=list, description="作业图片URL列表")
    context: Optional[str] = Field(None, description="额外上下文信息")

    @validator('homework_text', 'answer_text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('题目文本和答案文本不能为空')
        return v.strip()

    @validator('image_urls')
    def validate_image_urls(cls, v):
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'无效的图片URL: {url}')
        return v

    class Config:
        use_enum_values = True


class CorrectionItem(BaseModel):
    """单个批改项"""
    item_number: int = Field(..., description="题目编号")
    is_correct: bool = Field(..., description="是否正确")
    score: float = Field(..., ge=0, le=100, description="得分(0-100)")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    student_answer: str = Field(..., description="学生答案")
    correction_note: Optional[str] = Field(None, description="批改备注")
    knowledge_points: List[str] = Field(default_factory=list, description="涉及知识点")


class HomeworkCorrectionResponse(BaseModel):
    """作业批改响应"""
    correction_id: str = Field(..., description="批改ID")
    overall_score: float = Field(..., ge=0, le=100, description="总分(0-100)")
    total_items: int = Field(..., ge=0, description="总题数")
    correct_items: int = Field(..., ge=0, description="正确题数")
    corrections: List[CorrectionItem] = Field(..., description="详细批改结果")
    overall_feedback: str = Field(..., description="总体评价")
    knowledge_points: List[str] = Field(default_factory=list, description="涉及的所有知识点")
    difficulty_level: DifficultyLevel = Field(..., description="难度等级")
    study_suggestions: List[str] = Field(default_factory=list, description="学习建议")
    weak_points: List[str] = Field(default_factory=list, description="薄弱知识点")
    processing_info: Optional[Dict[str, Any]] = Field(None, description="处理信息")

    @validator('correct_items')
    def correct_items_not_exceed_total(cls, v, values):
        total = values.get('total_items', 0)
        if v > total:
            raise ValueError('正确题数不能超过总题数')
        return v

    class Config:
        use_enum_values = True


# ============================================================================
# 学习问答相关模型
# ============================================================================

class StudyQARequest(BaseModel):
    """学习问答请求"""
    user_id: str = Field(..., description="用户ID")
    question: str = Field(..., min_length=1, max_length=1000, description="学生问题")
    subject: Optional[Subject] = Field(None, description="问题学科")
    grade_level: Optional[GradeLevel] = Field(None, description="年级")
    context_homework_ids: List[str] = Field(default_factory=list, description="相关作业ID列表")
    session_id: Optional[str] = Field(None, description="会话ID")

    @validator('question')
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError('问题不能为空')
        return v.strip()

    class Config:
        use_enum_values = True


class StudyQAResponse(BaseModel):
    """学习问答响应"""
    answer: str = Field(..., description="AI回答")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="回答置信度")
    knowledge_points: List[str] = Field(default_factory=list, description="相关知识点")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="问题难度")
    follow_up_questions: List[str] = Field(default_factory=list, description="延伸问题")
    learning_resources: List[Dict[str, str]] = Field(default_factory=list, description="学习资源推荐")
    explanation_steps: List[str] = Field(default_factory=list, description="解题步骤")
    similar_problems: List[str] = Field(default_factory=list, description="类似问题")
    session_id: str = Field(..., description="会话ID")

    class Config:
        use_enum_values = True


# ============================================================================
# 学情分析相关模型
# ============================================================================

class AnalysisTimeRange(str, Enum):
    """分析时间范围"""
    WEEK = "week"       # 最近一周
    MONTH = "month"     # 最近一个月
    TERM = "term"       # 本学期
    YEAR = "year"       # 本学年


class LearningAnalysisRequest(BaseModel):
    """学情分析请求"""
    user_id: str = Field(..., description="用户ID")
    time_range: AnalysisTimeRange = Field(default=AnalysisTimeRange.MONTH, description="分析时间范围")
    subjects: List[Subject] = Field(default_factory=list, description="分析学科列表")
    analysis_type: str = Field(default="comprehensive", description="分析类型")
    include_recommendations: bool = Field(default=True, description="是否包含学习建议")

    @validator('subjects')
    def subjects_not_empty_if_specified(cls, v):
        # 如果指定了学科，不能为空
        return v

    class Config:
        use_enum_values = True


class KnowledgePointMastery(BaseModel):
    """知识点掌握情况"""
    knowledge_point: str = Field(..., description="知识点名称")
    mastery_level: float = Field(..., ge=0.0, le=1.0, description="掌握度(0-1)")
    total_exercises: int = Field(..., ge=0, description="总练习次数")
    correct_exercises: int = Field(..., ge=0, description="正确次数")
    last_practice_date: Optional[datetime] = Field(None, description="最后练习时间")
    difficulty_trend: str = Field(default="stable", description="难度趋势")

    @validator('correct_exercises')
    def correct_not_exceed_total(cls, v, values):
        total = values.get('total_exercises', 0)
        if v > total:
            raise ValueError('正确次数不能超过总次数')
        return v


class SubjectAnalysis(BaseModel):
    """学科分析结果"""
    subject: Subject
    overall_score: float = Field(..., ge=0.0, le=100.0, description="学科总分")
    knowledge_mastery: List[KnowledgePointMastery] = Field(..., description="知识点掌握情况")
    strengths: List[str] = Field(default_factory=list, description="优势知识点")
    weaknesses: List[str] = Field(default_factory=list, description="薄弱知识点")
    improvement_trend: str = Field(default="stable", description="进步趋势")
    study_time: int = Field(default=0, description="学习时长(分钟)")

    class Config:
        use_enum_values = True


class LearningAnalysisResponse(BaseModel):
    """学情分析响应"""
    analysis_report: str = Field(..., description="分析报告文本")
    analysis_date: datetime = Field(default_factory=datetime.now, description="分析时间")
    time_range: AnalysisTimeRange = Field(..., description="分析时间范围")

    # 整体情况
    overall_score: float = Field(..., ge=0.0, le=100.0, description="整体得分")
    total_homework_count: int = Field(..., ge=0, description="总作业数量")
    total_study_time: int = Field(..., ge=0, description="总学习时长(分钟)")

    # 学科分析
    subject_analyses: List[SubjectAnalysis] = Field(..., description="各学科分析")

    # 学习建议
    study_suggestions: List[str] = Field(default_factory=list, description="学习建议")
    review_plan: List[Dict[str, Any]] = Field(default_factory=list, description="复习计划")
    next_focus_areas: List[str] = Field(default_factory=list, description="下阶段重点领域")

    # 趋势数据
    progress_trend: Dict[str, Any] = Field(default_factory=dict, description="进步趋势数据")
    performance_comparison: Dict[str, Any] = Field(default_factory=dict, description="表现对比")

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# API调用监控模型
# ============================================================================

class AICallMetrics(BaseModel):
    """AI调用指标"""
    service_type: str = Field(..., description="服务类型")
    user_id: Optional[str] = Field(None, description="用户ID")
    request_time: datetime = Field(default_factory=datetime.now, description="请求时间")
    response_time: Optional[datetime] = Field(None, description="响应时间")
    processing_time: float = Field(default=0.0, description="处理时间(秒)")
    tokens_used: int = Field(default=0, description="消耗Token数")
    success: bool = Field(default=True, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误消息")
    cost_estimation: float = Field(default=0.0, description="预估成本")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# 错误响应模型
# ============================================================================

class AIErrorResponse(BaseModel):
    """AI服务错误响应"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    retry_after: Optional[int] = Field(None, description="重试等待时间(秒)")
    request_id: Optional[str] = Field(None, description="请求ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
