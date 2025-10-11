"""
错题本相关的Pydantic模式定义
用于API请求和响应的数据验证和序列化
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from src.models.error_book import ErrorType, MasteryStatus, SourceType, ReviewResult


class ErrorQuestionBase(BaseModel):
    """错题基础模式"""
    subject: str = Field(..., description="学科", max_length=50)
    question_content: str = Field(..., description="题目内容")
    student_answer: Optional[str] = Field(None, description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    error_type: str = Field(ErrorType.CONCEPT_ERROR, description="错误类型")
    error_subcategory: Optional[str] = Field(None, description="错误子分类", max_length=100)
    knowledge_points: List[str] = Field(default_factory=list, description="关联知识点")
    difficulty_level: int = Field(2, description="难度等级(1-5)", ge=1, le=5)
    source_type: str = Field(SourceType.MANUAL, description="来源类型")
    source_id: Optional[str] = Field(None, description="来源ID")
    is_starred: bool = Field(False, description="是否标星")
    tags: List[str] = Field(default_factory=list, description="自定义标签")

    @validator('error_type')
    def validate_error_type(cls, v):
        if v not in [e.value for e in ErrorType]:
            raise ValueError(f'错误类型必须是: {[e.value for e in ErrorType]}')
        return v

    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in [s.value for s in SourceType]:
            raise ValueError(f'来源类型必须是: {[s.value for s in SourceType]}')
        return v


class ErrorQuestionCreate(ErrorQuestionBase):
    """创建错题的请求模式"""
    pass


class ErrorQuestionUpdate(BaseModel):
    """更新错题的请求模式"""
    subject: Optional[str] = Field(None, description="学科", max_length=50)
    question_content: Optional[str] = Field(None, description="题目内容")
    student_answer: Optional[str] = Field(None, description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    error_type: Optional[str] = Field(None, description="错误类型")
    error_subcategory: Optional[str] = Field(None, description="错误子分类")
    knowledge_points: Optional[List[str]] = Field(None, description="关联知识点")
    difficulty_level: Optional[int] = Field(None, description="难度等级", ge=1, le=5)
    mastery_status: Optional[str] = Field(None, description="掌握状态")
    is_starred: Optional[bool] = Field(None, description="是否标星")
    tags: Optional[List[str]] = Field(None, description="自定义标签")

    @validator('error_type')
    def validate_error_type(cls, v):
        if v and v not in [e.value for e in ErrorType]:
            raise ValueError(f'错误类型必须是: {[e.value for e in ErrorType]}')
        return v

    @validator('mastery_status')
    def validate_mastery_status(cls, v):
        if v and v not in [s.value for s in MasteryStatus]:
            raise ValueError(f'掌握状态必须是: {[s.value for s in MasteryStatus]}')
        return v


class ErrorQuestionResponse(ErrorQuestionBase):
    """错题响应模式"""
    id: str
    user_id: str
    mastery_status: str
    review_count: int
    correct_count: int
    last_review_at: Optional[datetime]
    next_review_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # 计算属性
    mastery_rate: float = Field(..., description="掌握率")
    is_overdue: bool = Field(..., description="是否逾期复习")
    overdue_days: int = Field(..., description="逾期天数")

    class Config:
        from_attributes = True


class ErrorQuestionDetail(ErrorQuestionResponse):
    """错题详情响应模式（包含复习记录）"""
    review_records: List['ReviewRecordResponse'] = Field(default_factory=list, description="复习记录")


class ReviewRecordBase(BaseModel):
    """复习记录基础模式"""
    review_result: str = Field(..., description="复习结果")
    score: int = Field(0, description="得分(0-100)", ge=0, le=100)
    time_spent: Optional[int] = Field(None, description="用时(秒)", ge=0)
    student_answer: Optional[str] = Field(None, description="本次学生答案")
    notes: Optional[str] = Field(None, description="复习笔记")

    @validator('review_result')
    def validate_review_result(cls, v):
        if v not in [r.value for r in ReviewResult]:
            raise ValueError(f'复习结果必须是: {[r.value for r in ReviewResult]}')
        return v


class ReviewRecordCreate(ReviewRecordBase):
    """创建复习记录的请求模式"""
    error_question_id: str = Field(..., description="错题ID")


class ReviewRecordResponse(ReviewRecordBase):
    """复习记录响应模式"""
    id: str
    error_question_id: str
    user_id: str
    reviewed_at: datetime
    next_review_at: Optional[datetime]
    performance_score: float = Field(..., description="性能得分")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ErrorQuestionListQuery(BaseModel):
    """错题列表查询参数"""
    subject: Optional[str] = Field(None, description="学科筛选")
    status: Optional[str] = Field(None, description="掌握状态筛选")
    category: Optional[str] = Field(None, description="错误分类筛选")
    difficulty: Optional[int] = Field(None, description="难度筛选", ge=1, le=5)
    sort: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    page: int = Field(1, description="页码", ge=1)
    limit: int = Field(20, description="每页数量", ge=1, le=100)

    @validator('status')
    def validate_status(cls, v):
        if v and v not in [s.value for s in MasteryStatus]:
            raise ValueError(f'状态必须是: {[s.value for s in MasteryStatus]}')
        return v

    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是: asc 或 desc')
        return v.lower()


class ErrorQuestionListResponse(BaseModel):
    """错题列表响应模式"""
    items: List[ErrorQuestionResponse]
    total: int
    page: int
    limit: int
    pages: int

    @validator('pages', pre=True, always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        limit = values.get('limit', 20)
        return (total + limit - 1) // limit if total > 0 else 0


class ErrorBookStats(BaseModel):
    """错题本统计响应模式"""
    overview: Dict[str, Any] = Field(..., description="总体统计")
    by_subject: List[Dict[str, Any]] = Field(..., description="按学科统计")
    by_category: List[Dict[str, Any]] = Field(..., description="按分类统计")


class CategoryStats(BaseModel):
    """分类统计响应模式"""
    category: str
    count: int
    percentage: float
    recent_trend: Optional[str] = None


class WeakAreaRecommendation(BaseModel):
    """薄弱区域推荐"""
    knowledge_point: str = Field(..., description="知识点")
    error_count: int = Field(..., description="错误次数")
    mastery_rate: float = Field(..., description="掌握率")
    suggestion: str = Field(..., description="建议")


class ReviewRecommendation(BaseModel):
    """复习推荐项"""
    error_question_id: str = Field(..., description="错题ID")
    question_preview: str = Field(..., description="题目预览")
    subject: str = Field(..., description="学科")
    overdue_days: int = Field(..., description="逾期天数")
    importance_score: float = Field(..., description="重要性评分")
    difficulty_level: int = Field(..., description="难度等级")


class DailyReviewPlan(BaseModel):
    """每日复习计划"""
    target_count: int = Field(..., description="目标复习数量")
    estimated_time: int = Field(..., description="预估时间(分钟)")
    subjects: List[str] = Field(..., description="涉及学科")
    priority_items: List[str] = Field(..., description="优先项目ID")


class ReviewRecommendations(BaseModel):
    """复习推荐响应模式"""
    urgent_reviews: List[ReviewRecommendation] = Field(..., description="紧急复习")
    daily_plan: DailyReviewPlan = Field(..., description="每日计划")
    weak_areas: List[WeakAreaRecommendation] = Field(..., description="薄弱区域")


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    error_question_ids: List[str] = Field(..., description="错题ID列表", min_items=1)
    action: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="更新数据")

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['update_status', 'delete', 'star', 'unstar', 'add_tags', 'remove_tags']
        if v not in allowed_actions:
            raise ValueError(f'操作类型必须是: {allowed_actions}')
        return v


class SuccessResponse(BaseModel):
    """成功响应模式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应模式"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class ErrorAnalysisRequest(BaseModel):
    """错题分析请求"""
    question_content: str = Field(..., description="题目内容")
    student_answer: str = Field(..., description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    subject: Optional[str] = Field(None, description="学科")


class ErrorAnalysisResponse(BaseModel):
    """错题分析响应"""
    error_type: str = Field(..., description="错误类型")
    error_subcategory: Optional[str] = Field(None, description="错误子分类")
    confidence: float = Field(..., description="置信度")
    analysis: str = Field(..., description="分析结果")
    suggestions: List[str] = Field(..., description="改进建议")
    knowledge_points: List[str] = Field(..., description="相关知识点")


# 更新前向引用
ErrorQuestionDetail.model_rebuild()