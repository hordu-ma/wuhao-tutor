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
# 枚举类型
# ============================================================================


class MistakeSource(str):
    """错题来源"""

    HOMEWORK = "homework"
    LEARNING = "learning"
    MANUAL = "manual"


class MasteryStatus(str):
    """掌握状态"""

    NOT_MASTERED = "not_mastered"
    REVIEWING = "reviewing"
    MASTERED = "mastered"


# ============================================================================
# 创建错题相关 Schema
# ============================================================================


class CreateMistakeRequest(BaseModel):
    """创建错题请求"""

    title: str = Field(..., description="错题标题")
    description: Optional[str] = Field(None, description="错题描述")
    subject: str = Field(..., description="学科")
    difficulty_level: Optional[int] = Field(1, ge=1, le=5, description="难度级别 1-5")
    question_content: str = Field(..., description="题目内容")
    student_answer: Optional[str] = Field(None, description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    explanation: Optional[str] = Field(None, description="题目解析")
    knowledge_points: Optional[List[str]] = Field(
        default_factory=list, description="知识点列表"
    )
    image_urls: Optional[List[str]] = Field(
        default_factory=list, description="图片URL列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "二次函数综合练习",
                "subject": "math",
                "difficulty_level": 3,
                "question_content": "已知二次函数y=ax²+bx+c经过点(1,0)...",
                "student_answer": "y = x² - 2x + 1",
                "correct_answer": "y = x² - 3x + 2",
                "explanation": "根据题目条件...",
                "knowledge_points": ["二次函数", "函数图像"],
            }
        }


# ============================================================================
# 今日复习相关 Schema
# ============================================================================


class TodayReviewTask(BaseModel):
    """今日复习任务"""

    id: UUID = Field(..., description="复习计划ID")
    mistake_id: UUID = Field(..., description="错题ID")
    title: str = Field(..., description="错题标题")
    subject: str = Field(..., description="学科")
    review_round: int = Field(..., description="复习轮次")
    due_date: str = Field(..., description="到期时间")
    question_content: str = Field(..., description="题目内容")
    image_urls: Optional[List[str]] = Field(
        default_factory=list, description="图片URL列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "mistake_id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "二次函数综合练习",
                "subject": "math",
                "review_round": 2,
                "due_date": "2025-10-12T10:00:00",
                "question_content": "已知二次函数...",
            }
        }


class TodayReviewResponse(BaseModel):
    """今日复习任务列表响应"""

    tasks: List[TodayReviewTask] = Field(
        default_factory=list, description="复习任务列表"
    )
    total_count: int = Field(..., description="今日复习任务总数")
    completed_count: int = Field(0, description="已完成数量")

    class Config:
        json_schema_extra = {
            "example": {"tasks": [], "total_count": 5, "completed_count": 0}
        }


# ============================================================================
# 复习完成相关 Schema
# ============================================================================


class ReviewCompleteRequest(BaseModel):
    """复习完成请求"""

    mistake_id: UUID = Field(..., description="错题ID")
    is_correct: bool = Field(..., description="是否答对")
    time_spent: Optional[int] = Field(None, ge=0, description="复习耗时（秒）")
    notes: Optional[str] = Field(None, description="复习笔记")

    class Config:
        json_schema_extra = {
            "example": {
                "mistake_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_correct": True,
                "time_spent": 120,
                "notes": "这次理解了",
            }
        }


class ReviewCompleteResponse(BaseModel):
    """复习完成响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    mastery_status: str = Field(..., description="掌握状态")
    next_review_date: Optional[str] = Field(None, description="下次复习时间")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "复习完成",
                "mastery_status": "reviewing",
                "next_review_date": "2025-10-14T10:00:00",
            }
        }


# ============================================================================
# 错题列表相关 Schema
# ============================================================================


class MistakeListItem(BaseModel):
    """错题列表项"""

    id: UUID = Field(..., description="错题ID")
    title: str = Field(..., description="错题标题")
    subject: str = Field(..., description="学科")
    difficulty_level: Optional[int] = Field(None, description="难度级别")
    source: str = Field(..., description="来源")
    source_id: Optional[UUID] = Field(None, description="来源ID")
    mastery_status: str = Field(..., description="掌握状态")
    correct_count: int = Field(..., description="正确次数")
    total_reviews: int = Field(..., description="总复习次数")
    next_review_date: Optional[str] = Field(None, description="下次复习时间")
    created_at: str = Field(..., description="创建时间")
    knowledge_points: Optional[List[str]] = Field(
        default_factory=list, description="知识点列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "二次函数综合练习",
                "subject": "math",
                "difficulty_level": 3,
                "source": "homework",
                "mastery_status": "reviewing",
                "correct_count": 2,
                "total_reviews": 3,
                "next_review_date": "2025-10-14T10:00:00",
                "created_at": "2025-10-10T10:00:00",
                "knowledge_points": ["二次函数", "函数图像"],
            }
        }


class MistakeListResponse(BaseModel):
    """错题列表响应"""

    items: List[MistakeListItem] = Field(default_factory=list, description="错题列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")

    class Config:
        json_schema_extra = {
            "example": {"items": [], "total": 50, "page": 1, "page_size": 20}
        }


# ============================================================================
# 错题详情相关 Schema
# ============================================================================


class MistakeDetailResponse(BaseModel):
    """错题详情响应"""

    id: UUID = Field(..., description="错题ID")
    title: str = Field(..., description="错题标题")
    description: Optional[str] = Field(None, description="错题描述")
    subject: str = Field(..., description="学科")
    difficulty_level: Optional[int] = Field(None, description="难度级别")
    source: str = Field(..., description="来源")
    source_id: Optional[UUID] = Field(None, description="来源ID")
    question_content: str = Field(..., description="题目内容")
    student_answer: Optional[str] = Field(None, description="学生答案")
    correct_answer: Optional[str] = Field(None, description="正确答案")
    explanation: Optional[str] = Field(None, description="题目解析")
    knowledge_points: Optional[List[str]] = Field(
        default_factory=list, description="知识点列表"
    )
    mastery_status: str = Field(..., description="掌握状态")
    correct_count: int = Field(..., description="正确次数")
    total_reviews: int = Field(..., description="总复习次数")
    next_review_date: Optional[str] = Field(None, description="下次复习时间")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    image_urls: Optional[List[str]] = Field(
        default_factory=list, description="图片URL列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "二次函数综合练习",
                "subject": "math",
                "difficulty_level": 3,
                "source": "homework",
                "question_content": "已知二次函数...",
                "student_answer": "y = x² - 2x + 1",
                "correct_answer": "y = x² - 3x + 2",
                "explanation": "根据题目条件...",
                "mastery_status": "reviewing",
                "correct_count": 2,
                "total_reviews": 3,
                "next_review_date": "2025-10-14T10:00:00",
                "created_at": "2025-10-10T10:00:00",
                "updated_at": "2025-10-12T10:00:00",
            }
        }


# ============================================================================
# 错题统计相关 Schema
# ============================================================================


class MistakeStatisticsResponse(BaseModel):
    """错题统计响应"""

    total_mistakes: int = Field(..., description="总错题数")
    not_mastered: int = Field(..., description="未掌握数量")
    reviewing: int = Field(..., description="复习中数量")
    mastered: int = Field(..., description="已掌握数量")
    by_subject: Dict[str, int] = Field(default_factory=dict, description="按学科分布")
    by_difficulty: Dict[str, int] = Field(
        default_factory=dict, description="按难度分布"
    )
    review_streak_days: int = Field(0, description="连续复习天数")
    this_week_reviews: int = Field(0, description="本周复习次数")

    class Config:
        json_schema_extra = {
            "example": {
                "total_mistakes": 50,
                "not_mastered": 15,
                "reviewing": 25,
                "mastered": 10,
                "by_subject": {"math": 30, "english": 15, "chinese": 5},
                "by_difficulty": {"1": 5, "2": 15, "3": 20, "4": 8, "5": 2},
                "review_streak_days": 7,
                "this_week_reviews": 25,
            }
        }
