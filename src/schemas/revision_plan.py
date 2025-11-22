"""
复习计划 Schema 定义
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RevisionPlanBase(BaseModel):
    """复习计划基础模型"""

    title: str
    description: Optional[str] = None
    cycle_type: str
    status: str
    mistake_count: int
    knowledge_points: List[Any] = Field(default_factory=list)
    date_range: Optional[Dict[str, Any]] = None
    pdf_url: Optional[str] = None
    pdf_size: Optional[int] = None
    expired_at: Optional[datetime] = None


class RevisionPlanResponse(RevisionPlanBase):
    """复习计划响应模型（列表用）"""

    id: UUID
    user_id: UUID
    download_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RevisionPlanDetailResponse(RevisionPlanResponse):
    """复习计划详情响应模型"""

    plan_content: Optional[Dict[str, Any]] = None


class RevisionPlanGenerateRequest(BaseModel):
    """生成复习计划请求"""

    title: Optional[str] = Field(None, description="计划标题")
    cycle_type: str = Field("7days", description="周期类型: 7days, 14days, 30days")
    days_lookback: int = Field(30, description="回顾过去多少天的错题")
    force_regenerate: bool = Field(False, description="是否强制重新生成")


class RevisionPlanListResponse(BaseModel):
    """复习计划列表响应"""

    total: int
    items: List[RevisionPlanResponse]
    limit: int
    offset: int
