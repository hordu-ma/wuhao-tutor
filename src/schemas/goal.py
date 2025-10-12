"""
目标相关的数据模型
"""

from typing import Optional

from pydantic import BaseModel, Field


class DailyGoal(BaseModel):
    """每日目标数据模型"""

    id: int = Field(..., description="目标ID")
    title: str = Field(..., description="目标标题")
    type: str = Field(
        ...,
        description="目标类型: review_mistakes, questions, study_time, record_mistakes",
    )
    target: int = Field(..., description="目标值")
    current: int = Field(..., description="当前进度")
    completed: bool = Field(..., description="是否完成")
    progress: int = Field(..., description="完成百分比 0-100")
    action_link: Optional[str] = Field(None, description="操作链接")
    description: Optional[str] = Field(None, description="目标描述")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "复习 5 道错题",
                "type": "review_mistakes",
                "target": 5,
                "current": 2,
                "completed": False,
                "progress": 40,
                "action_link": "/mistakes/today-review",
                "description": "基于遗忘曲线的智能复习",
            }
        }
