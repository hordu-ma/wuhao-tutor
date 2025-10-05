"""
学情分析相关的 Pydantic 模型和响应 Schema
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class LearningProgressItem(BaseModel):
    """学习进度项"""

    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    study_duration: int = Field(0, description="学习时长(分钟)")
    completion_rate: float = Field(0.0, description="完成率(0-1)")
    accuracy_rate: float = Field(0.0, description="正确率(0-1)")
    homework_count: int = Field(0, description="作业数量")
    question_count: int = Field(0, description="问题数量")


class LearningProgress(BaseModel):
    """学习进度响应"""

    period: str = Field(..., description="时间周期 (daily/weekly/monthly)")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    data: List[LearningProgressItem] = Field(
        default_factory=list, description="进度数据"
    )
    summary: Dict[str, Union[int, float]] = Field(
        default_factory=dict, description="摘要统计"
    )


class KnowledgePointMastery(BaseModel):
    """知识点掌握情况"""

    id: str = Field(..., description="知识点ID")
    name: str = Field(..., description="知识点名称")
    subject: str = Field(..., description="学科")
    mastery_level: float = Field(0.0, description="掌握度(0-1)")
    accuracy_rate: float = Field(0.0, description="正确率(0-1)")
    total_attempts: int = Field(0, description="尝试次数")
    correct_attempts: int = Field(0, description="正确次数")
    last_practice: Optional[datetime] = Field(None, description="最近练习时间")
    trend: str = Field("stable", description="趋势 (improving/stable/declining)")


class KnowledgePointsResponse(BaseModel):
    """知识点掌握响应"""

    subject: Optional[str] = Field(None, description="学科筛选")
    total_count: int = Field(0, description="总知识点数")
    mastered_count: int = Field(0, description="已掌握数量")
    improving_count: int = Field(0, description="提升中数量")
    weak_count: int = Field(0, description="薄弱知识点数量")
    knowledge_points: List[KnowledgePointMastery] = Field(
        default_factory=list, description="知识点列表"
    )


class SubjectStatistics(BaseModel):
    """学科统计数据"""

    subject: str = Field(..., description="学科名称")
    study_duration: int = Field(0, description="学习时长(分钟)")
    homework_count: int = Field(0, description="作业数量")
    question_count: int = Field(0, description="问题数量")
    avg_score: float = Field(0.0, description="平均分")
    accuracy_rate: float = Field(0.0, description="正确率")
    improvement_rate: float = Field(0.0, description="进步率(%)")
    last_study: Optional[datetime] = Field(None, description="最近学习时间")
    weak_knowledge_points: List[str] = Field(
        default_factory=list, description="薄弱知识点"
    )
    rank: int = Field(0, description="排名")


class SubjectStatsResponse(BaseModel):
    """学科统计响应"""

    time_range: str = Field("30d", description="时间范围")
    total_subjects: int = Field(0, description="总学科数")
    most_active_subject: Optional[str] = Field(None, description="最活跃学科")
    strongest_subject: Optional[str] = Field(None, description="最强学科")
    subjects: List[SubjectStatistics] = Field(
        default_factory=list, description="学科列表"
    )
    recommendations: List[str] = Field(default_factory=list, description="学习建议")


class LearningTrend(BaseModel):
    """学习趋势"""

    metric: str = Field(..., description="指标名称")
    current_value: float = Field(0.0, description="当前值")
    previous_value: float = Field(0.0, description="前期值")
    change_rate: float = Field(0.0, description="变化率(%)")
    trend_direction: str = Field("stable", description="趋势方向 (up/down/stable)")


class AnalyticsOverview(BaseModel):
    """学情分析概览"""

    user_id: UUID = Field(..., description="用户ID")
    generated_at: datetime = Field(..., description="生成时间")
    total_study_days: int = Field(0, description="总学习天数")
    total_study_hours: float = Field(0.0, description="总学习小时数")
    total_homework: int = Field(0, description="总作业数")
    total_questions: int = Field(0, description="总问题数")
    overall_accuracy: float = Field(0.0, description="整体正确率")
    trends: List[LearningTrend] = Field(default_factory=list, description="学习趋势")
    weak_subjects: List[str] = Field(default_factory=list, description="薄弱学科")
    strong_subjects: List[str] = Field(default_factory=list, description="优势学科")
