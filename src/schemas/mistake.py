"""
错题本相关 Pydantic Schema
用于 API 请求和响应的数据验证

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# 今日复习相关 Schema
# ============================================================================


class TodayReviewTask(BaseModel):
    """今日复习任务"""

    schedule_id: UUID = Field(..., description="复习计划ID")
    mistake_id: UUID = Field(..., description="错题ID")
    subject: str = Field(..., description="学科")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    priority: int = Field(..., ge=1, le=5, description="优先级(1-5)")
    interval_days: int = Field(..., description="复习间隔天数")
    ocr_text: Optional[str] = Field(None, description="OCR识别文本")
    image_urls: Optional[List[str]] = Field(
        default_factory=list, description="图片URL列表"
    )
    title: Optional[str] = Field(None, description="错题标题")

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "123e4567-e89b-12d3-a456-426614174000",
                "mistake_id": "123e4567-e89b-12d3-a456-426614174001",
                "subject": "math",
                "knowledge_points": ["二次函数", "函数图像"],
                "priority": 5,
                "interval_days": 1,
                "title": "二次函数综合练习 - 二次函数",
            }
        }


class TodayReviewResponse(BaseModel):
    """今日复习任务列表响应"""

    date: str = Field(..., description="日期 YYYY-MM-DD")
    total_count: int = Field(..., description="今日复习任务总数")
    tasks: List[TodayReviewTask] = Field(
        default_factory=list, description="复习任务列表"
    )

    class Config:
        json_schema_extra = {
            "example": {"date": "2025-10-12", "total_count": 5, "tasks": []}
        }


# ============================================================================
# 复习完成相关 Schema
# ============================================================================


class ReviewCompleteRequest(BaseModel):
    """复习完成请求"""

    result: str = Field(
        ...,
        description="复习结果 (correct/incorrect/skipped)",
        pattern="^(correct|incorrect|skipped)$",
    )
    duration_seconds: Optional[int] = Field(None, ge=0, description="复习耗时（秒）")

    @field_validator("result")
    @classmethod
    def validate_result(cls, v: str) -> str:
        """验证复习结果"""
        if v not in ["correct", "incorrect", "skipped"]:
            raise ValueError("result 必须是 correct, incorrect 或 skipped")
        return v

    class Config:
        json_schema_extra = {"example": {"result": "correct", "duration_seconds": 120}}


class ReviewCompleteResponse(BaseModel):
    """复习完成响应"""

    mistake_id: UUID = Field(..., description="错题ID")
    mastery_status: str = Field(..., description="掌握状态")
    review_count: int = Field(..., description="复习次数")
    correct_count: int = Field(..., description="正确次数")
    next_review_at: Optional[datetime] = Field(None, description="下次复习时间")
    is_mastered: bool = Field(..., description="是否已掌握")

    class Config:
        json_schema_extra = {
            "example": {
                "mistake_id": "123e4567-e89b-12d3-a456-426614174001",
                "mastery_status": "learning",
                "review_count": 2,
                "correct_count": 1,
                "next_review_at": "2025-10-14T10:00:00",
                "is_mastered": False,
            }
        }


# ============================================================================
# 错题列表相关 Schema
# ============================================================================


class MistakeListItem(BaseModel):
    """错题列表项"""

    id: UUID = Field(..., description="错题ID")
    subject: str = Field(..., description="学科")
    title: Optional[str] = Field(None, description="错题标题")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    mastery_status: str = Field(..., description="掌握状态")
    review_count: int = Field(..., description="复习次数")
    correct_count: int = Field(..., description="正确次数")
    difficulty_level: int = Field(..., description="难度级别")
    last_review_at: Optional[str] = Field(None, description="最后复习时间")
    next_review_at: Optional[str] = Field(None, description="下次复习时间")
    created_at: str = Field(..., description="创建时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "subject": "math",
                "title": "二次函数综合练习",
                "knowledge_points": ["二次函数", "函数图像"],
                "mastery_status": "learning",
                "review_count": 2,
                "correct_count": 1,
                "difficulty_level": 2,
                "created_at": "2025-10-10T10:00:00",
            }
        }


class MistakeListResponse(BaseModel):
    """错题列表响应"""

    items: List[MistakeListItem] = Field(default_factory=list, description="错题列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "total_pages": 3,
            }
        }


# ============================================================================
# 错题详情相关 Schema
# ============================================================================


class ReviewHistoryItem(BaseModel):
    """复习历史项"""

    scheduled_at: str = Field(..., description="计划复习时间")
    completed_at: Optional[str] = Field(None, description="实际完成时间")
    result: Optional[str] = Field(None, description="复习结果")
    interval_days: int = Field(..., description="间隔天数")
    priority: int = Field(..., description="优先级")


class MistakeDetailResponse(BaseModel):
    """错题详情响应"""

    id: UUID = Field(..., description="错题ID")
    subject: str = Field(..., description="学科")
    chapter: Optional[str] = Field(None, description="章节")
    title: Optional[str] = Field(None, description="错题标题")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    error_reasons: List[Any] = Field(default_factory=list, description="错误原因列表")
    ocr_text: Optional[str] = Field(None, description="OCR识别文本")
    image_urls: List[str] = Field(default_factory=list, description="图片URL列表")
    ai_feedback: Optional[Dict[str, Any]] = Field(None, description="AI反馈")
    difficulty_level: int = Field(..., description="难度级别")
    mastery_status: str = Field(..., description="掌握状态")
    review_count: int = Field(..., description="复习次数")
    correct_count: int = Field(..., description="正确次数")
    last_review_at: Optional[str] = Field(None, description="最后复习时间")
    next_review_at: Optional[str] = Field(None, description="下次复习时间")
    source: str = Field(..., description="来源")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    notes: Optional[str] = Field(None, description="学生备注")
    created_at: str = Field(..., description="创建时间")
    review_history: List[ReviewHistoryItem] = Field(
        default_factory=list, description="复习历史"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "subject": "math",
                "title": "二次函数综合练习",
                "knowledge_points": ["二次函数"],
                "mastery_status": "learning",
                "review_count": 2,
                "correct_count": 1,
                "difficulty_level": 2,
                "source": "homework",
                "created_at": "2025-10-10T10:00:00",
                "review_history": [],
            }
        }


# ============================================================================
# 错题统计相关 Schema
# ============================================================================


class MistakeStatsResponse(BaseModel):
    """错题统计响应"""

    period: str = Field(..., description="统计周期 (week/month/all)")
    total_mistakes: int = Field(..., description="总错题数")
    mastered_count: int = Field(..., description="已掌握数量")
    learning_count: int = Field(..., description="学习中数量")
    reviewing_count: int = Field(..., description="复习中数量")
    subject_distribution: Dict[str, int] = Field(
        default_factory=dict, description="学科分布"
    )
    avg_review_count: float = Field(..., description="平均复习次数")
    mastery_rate: float = Field(..., description="掌握率(%)")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "week",
                "total_mistakes": 50,
                "mastered_count": 15,
                "learning_count": 30,
                "reviewing_count": 5,
                "subject_distribution": {"math": 30, "english": 15, "chinese": 5},
                "avg_review_count": 2.5,
                "mastery_rate": 30.0,
            }
        }
