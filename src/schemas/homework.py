"""
作业相关的Pydantic Schema模型
定义API请求和响应的数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import UUID4, BaseModel, Field, validator


class SubjectType(str, Enum):
    """学科类型枚举"""

    CHINESE = "chinese"
    MATH = "math"
    ENGLISH = "english"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"
    OTHER = "other"


class HomeworkType(str, Enum):
    """作业类型枚举"""

    DAILY = "daily"
    EXAM = "exam"
    EXERCISE = "exercise"
    TEST = "test"
    REVIEW = "review"


class DifficultyLevel(str, Enum):
    """难度级别枚举"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SubmissionStatus(str, Enum):
    """提交状态枚举"""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ReviewStatus(str, Enum):
    """批改状态枚举"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# 作业模板相关Schema
# ============================================================================


class HomeworkCreate(BaseModel):
    """创建作业模板请求"""

    title: str = Field(..., min_length=1, max_length=200, description="作业标题")
    description: Optional[str] = Field(None, max_length=2000, description="作业描述")
    subject: SubjectType = Field(..., description="学科")
    homework_type: HomeworkType = Field(HomeworkType.DAILY, description="作业类型")
    difficulty_level: Union[DifficultyLevel, int] = Field(
        2, description="难度级别 (字符串枚举或整数: 1=easy, 2=medium, 3=hard)"
    )
    grade_level: str = Field(..., min_length=1, max_length=20, description="适用学段")
    chapter: Optional[str] = Field(None, max_length=100, description="章节")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    estimated_duration: Optional[int] = Field(
        None, ge=1, le=300, description="预计完成时间（分钟）"
    )
    deadline: Optional[datetime] = Field(None, description="截止时间")


class HomeworkUpdate(BaseModel):
    """更新作业模板请求"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="作业标题"
    )
    description: Optional[str] = Field(None, max_length=2000, description="作业描述")
    subject: Optional[SubjectType] = Field(None, description="学科")
    homework_type: Optional[HomeworkType] = Field(None, description="作业类型")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="难度级别")
    grade_level: Optional[str] = Field(
        None, min_length=1, max_length=20, description="适用学段"
    )
    chapter: Optional[str] = Field(None, max_length=100, description="章节")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    estimated_duration: Optional[int] = Field(
        None, ge=1, le=300, description="预计完成时间（分钟）"
    )
    deadline: Optional[datetime] = Field(None, description="截止时间")
    is_active: Optional[bool] = Field(None, description="是否激活")


class HomeworkResponse(BaseModel):
    """作业模板响应"""

    id: UUID4 = Field(..., description="作业ID")
    title: str = Field(..., description="作业标题")
    description: Optional[str] = Field(None, description="作业描述")
    subject: SubjectType = Field(..., description="学科")
    homework_type: HomeworkType = Field(..., description="作业类型")
    difficulty_level: DifficultyLevel = Field(..., description="难度级别")
    grade_level: str = Field(..., description="适用学段")
    chapter: Optional[str] = Field(None, description="章节")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点列表")
    estimated_duration: Optional[int] = Field(None, description="预计完成时间（分钟）")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    creator_id: Optional[UUID4] = Field(None, description="创建者ID")
    creator_name: Optional[str] = Field(None, description="创建者姓名")
    is_active: bool = Field(..., description="是否激活")
    is_template: bool = Field(..., description="是否为模板")
    total_submissions: int = Field(..., description="总提交数")
    avg_score: Optional[float] = Field(None, description="平均分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============================================================================
# 作业图片相关Schema
# ============================================================================


class HomeworkImageUpload(BaseModel):
    """作业图片上传请求"""

    display_order: int = Field(0, ge=0, description="显示顺序")
    is_primary: bool = Field(False, description="是否为主图")


class HomeworkImageResponse(BaseModel):
    """作业图片响应"""

    id: UUID4 = Field(..., description="图片ID")
    submission_id: UUID4 = Field(..., description="提交ID")
    original_filename: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件存储路径")
    file_url: Optional[str] = Field(None, description="文件访问URL")
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="MIME类型")
    image_width: Optional[int] = Field(None, description="图片宽度")
    image_height: Optional[int] = Field(None, description="图片高度")
    display_order: int = Field(..., description="显示顺序")
    is_primary: bool = Field(..., description="是否为主图")
    ocr_text: Optional[str] = Field(None, description="OCR识别文本")
    ocr_confidence: Optional[float] = Field(None, description="OCR识别置信度")
    is_processed: bool = Field(..., description="是否已处理")
    processing_error: Optional[str] = Field(None, description="处理错误信息")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


# ============================================================================
# 作业提交相关Schema
# ============================================================================


class HomeworkSubmissionCreate(BaseModel):
    """创建作业提交请求"""

    homework_id: UUID4 = Field(..., description="作业ID")
    submission_title: Optional[str] = Field(
        None, max_length=200, description="提交标题"
    )
    submission_note: Optional[str] = Field(
        None, max_length=1000, description="提交备注"
    )
    completion_time: Optional[int] = Field(None, ge=1, description="完成时间（分钟）")


class HomeworkSubmissionUpdate(BaseModel):
    """更新作业提交请求"""

    submission_title: Optional[str] = Field(
        None, max_length=200, description="提交标题"
    )
    submission_note: Optional[str] = Field(
        None, max_length=1000, description="提交备注"
    )
    completion_time: Optional[int] = Field(None, ge=1, description="完成时间（分钟）")


class KnowledgePointAnalysis(BaseModel):
    """知识点分析"""

    knowledge_point: str = Field(..., description="知识点名称")
    mastery_level: float = Field(..., ge=0, le=1, description="掌握程度(0-1)")
    correct_count: int = Field(..., ge=0, description="正确题目数")
    total_count: int = Field(..., ge=1, description="总题目数")
    difficulty_level: DifficultyLevel = Field(..., description="难度级别")


class ImprovementSuggestion(BaseModel):
    """改进建议"""

    category: str = Field(..., description="建议类别")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    priority: int = Field(..., ge=1, le=5, description="优先级(1-5)")


class HomeworkSubmissionResponse(BaseModel):
    """作业提交响应"""

    id: UUID4 = Field(..., description="提交ID")
    homework_id: UUID4 = Field(..., description="作业ID")
    student_id: UUID4 = Field(..., description="学生ID")
    student_name: str = Field(..., description="学生姓名")
    submission_title: Optional[str] = Field(None, description="提交标题")
    submission_note: Optional[str] = Field(None, description="提交备注")
    status: SubmissionStatus = Field(..., description="提交状态")
    submitted_at: Optional[datetime] = Field(None, description="提交时间")
    total_score: Optional[float] = Field(None, description="总分")
    accuracy_rate: Optional[float] = Field(None, description="正确率")
    completion_time: Optional[int] = Field(None, description="完成时间（分钟）")
    weak_knowledge_points: Optional[List[KnowledgePointAnalysis]] = Field(
        None, description="薄弱知识点"
    )
    improvement_suggestions: Optional[List[ImprovementSuggestion]] = Field(
        None, description="改进建议"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class HomeworkSubmissionDetail(HomeworkSubmissionResponse):
    """作业提交详情响应（包含图片和批改结果）"""

    homework: HomeworkResponse = Field(..., description="作业信息")
    images: List[HomeworkImageResponse] = Field(..., description="作业图片")
    reviews: List["HomeworkReviewResponse"] = Field(..., description="批改结果")


# ============================================================================
# 作业批改相关Schema
# ============================================================================


class QuestionReview(BaseModel):
    """题目批改结果"""

    question_number: int = Field(..., ge=1, description="题目编号")
    question_text: Optional[str] = Field(None, description="题目内容")
    student_answer: Optional[str] = Field(None, description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    is_correct: bool = Field(..., description="是否正确")
    score: float = Field(..., ge=0, description="得分")
    max_score: float = Field(..., ge=0, description="满分")
    comment: Optional[str] = Field(None, description="批改评语")
    knowledge_points: List[str] = Field(default_factory=list, description="涉及知识点")
    difficulty_level: DifficultyLevel = Field(..., description="题目难度")


class HomeworkReviewCreate(BaseModel):
    """创建批改请求"""

    submission_id: UUID4 = Field(..., description="提交ID")
    review_type: str = Field("ai_auto", description="批改类型")
    max_score: float = Field(100.0, gt=0, description="满分")


class HomeworkReviewResponse(BaseModel):
    """作业批改响应"""

    id: UUID4 = Field(..., description="批改ID")
    submission_id: UUID4 = Field(..., description="提交ID")
    review_type: str = Field(..., description="批改类型")
    reviewer_id: Optional[UUID4] = Field(None, description="批改者ID")
    reviewer_name: Optional[str] = Field(None, description="批改者姓名")
    status: ReviewStatus = Field(..., description="批改状态")
    started_at: Optional[datetime] = Field(None, description="开始批改时间")
    completed_at: Optional[datetime] = Field(None, description="完成批改时间")
    processing_duration: Optional[int] = Field(None, description="处理时长（秒）")
    total_score: Optional[float] = Field(None, description="总分")
    max_score: float = Field(..., description="满分")
    accuracy_rate: Optional[float] = Field(None, description="正确率")
    overall_comment: Optional[str] = Field(None, description="总体评价")
    strengths: Optional[List[str]] = Field(None, description="优点列表")
    weaknesses: Optional[List[str]] = Field(None, description="不足列表")
    suggestions: Optional[List[ImprovementSuggestion]] = Field(
        None, description="改进建议"
    )
    knowledge_point_analysis: Optional[List[KnowledgePointAnalysis]] = Field(
        None, description="知识点分析"
    )
    question_reviews: Optional[List[QuestionReview]] = Field(
        None, description="题目级别评价"
    )
    ai_model_version: Optional[str] = Field(None, description="AI模型版本")
    ai_confidence_score: Optional[float] = Field(None, description="AI置信度分数")
    quality_score: Optional[float] = Field(None, description="批改质量分数")
    needs_manual_review: bool = Field(..., description="是否需要人工复核")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============================================================================
# 查询和分页相关Schema
# ============================================================================


class HomeworkQuery(BaseModel):
    """作业查询参数"""

    subject: Optional[SubjectType] = Field(None, description="学科筛选")
    homework_type: Optional[HomeworkType] = Field(None, description="作业类型筛选")
    difficulty_level: Optional[DifficultyLevel] = Field(
        None, description="难度级别筛选"
    )
    grade_level: Optional[str] = Field(None, description="学段筛选")
    creator_id: Optional[UUID4] = Field(None, description="创建者ID筛选")
    is_active: Optional[bool] = Field(None, description="是否激活筛选")
    keyword: Optional[str] = Field(
        None, min_length=1, max_length=100, description="关键词搜索"
    )


class SubmissionQuery(BaseModel):
    """提交查询参数"""

    homework_id: Optional[UUID4] = Field(None, description="作业ID筛选")
    student_id: Optional[UUID4] = Field(None, description="学生ID筛选")
    status: Optional[SubmissionStatus] = Field(None, description="状态筛选")
    subject: Optional[SubjectType] = Field(None, description="学科筛选")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="最低分数")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="最高分数")

    @validator("end_date")
    def validate_date_range(cls, v, values):
        if v and values.get("start_date") and v < values["start_date"]:
            raise ValueError("结束日期不能早于开始日期")
        return v


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序顺序")


class PaginatedResponse(BaseModel):
    """分页响应"""

    items: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页数量")
    pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# ============================================================================
# 统计和分析相关Schema
# ============================================================================


class ScoreDistribution(BaseModel):
    """分数分布"""

    score_range: str = Field(..., description="分数区间")
    count: int = Field(..., ge=0, description="数量")
    percentage: float = Field(..., ge=0, le=100, description="百分比")


class SubjectPerformance(BaseModel):
    """学科表现统计"""

    subject: SubjectType = Field(..., description="学科")
    total_submissions: int = Field(..., ge=0, description="总提交数")
    avg_score: float = Field(..., ge=0, le=100, description="平均分")
    pass_rate: float = Field(..., ge=0, le=100, description="及格率")
    excellent_rate: float = Field(..., ge=0, le=100, description="优秀率")


class HomeworkStatistics(BaseModel):
    """作业统计信息"""

    total_homeworks: int = Field(..., ge=0, description="总作业数")
    active_homeworks: int = Field(..., ge=0, description="激活的作业数")
    total_submissions: int = Field(..., ge=0, description="总提交数")
    reviewed_submissions: int = Field(..., ge=0, description="已批改提交数")
    avg_score: float = Field(..., ge=0, le=100, description="平均分")
    score_distribution: List[ScoreDistribution] = Field(..., description="分数分布")
    subject_performance: List[SubjectPerformance] = Field(..., description="各学科表现")


# ============================================================================
# 批量操作相关Schema
# ============================================================================


class BatchHomeworkCreate(BaseModel):
    """批量创建作业请求"""

    homeworks: List[HomeworkCreate] = Field(
        ..., min_length=1, max_length=10, description="作业列表"
    )


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    success_count: int = Field(..., ge=0, description="成功数量")
    failed_count: int = Field(..., ge=0, description="失败数量")
    total_count: int = Field(..., ge=0, description="总数量")
    success_ids: List[UUID4] = Field(..., description="成功的ID列表")
    failed_items: List[Dict[str, Any]] = Field(..., description="失败的项目详情")


# 解决前向引用问题
HomeworkSubmissionDetail.model_rebuild()


# ============================================================================
# API端点别名 - 为了兼容API端点的命名约定
# ============================================================================

# 模板相关别名
HomeworkTemplateCreate = HomeworkCreate
HomeworkTemplateUpdate = HomeworkUpdate
HomeworkTemplateResponse = HomeworkResponse

# 提交相关别名
HomeworkSubmissionListResponse = PaginatedResponse

# 批改相关别名
HomeworkCorrectionResponse = HomeworkReviewResponse

# 查询相关别名
HomeworkListQuery = HomeworkQuery


# 模板列表响应
class HomeworkTemplateListResponse(BaseModel):
    """作业模板列表响应"""

    success: bool = Field(True, description="是否成功")
    data: List[HomeworkTemplateResponse] = Field(..., description="模板列表")
    message: str = Field(..., description="响应消息")
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, description="每页数量")
