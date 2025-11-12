"""
知识图谱相关 Pydantic Schema
用于 API 请求和响应的数据验证

作者: AI Agent
创建时间: 2025-11-03
版本: v1.0
更新: 2025-11-12 - 统一使用 learning.SubjectType 枚举
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# 🔧 High Fix #2: 统一使用 learning.SubjectType,避免重复定义
from src.schemas.learning import SubjectType

# ============================================================================
# 学科枚举定义
# ============================================================================


# ============================================================================
# 知识点关联相关 Schema
# ============================================================================


class KnowledgePointAssociation(BaseModel):
    """知识点关联信息"""

    id: UUID = Field(..., description="关联ID")
    knowledge_point_id: UUID = Field(..., description="知识点ID")
    knowledge_point_name: str = Field(..., description="知识点名称")
    relevance_score: float = Field(..., description="关联度评分 0.0-1.0")
    is_primary: bool = Field(..., description="是否为主要知识点")
    error_type: str = Field(..., description="错误类型")
    error_reason: Optional[str] = Field(None, description="错误原因")
    mastery_level: float = Field(..., description="掌握度 0.0-1.0")
    mastered: bool = Field(..., description="是否已掌握")
    review_count: int = Field(..., description="复习次数")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "knowledge_point_id": "123e4567-e89b-12d3-a456-426614174001",
                "knowledge_point_name": "二次函数图像",
                "relevance_score": 0.9,
                "is_primary": True,
                "error_type": "concept_misunderstanding",
                "error_reason": "对函数图像的对称轴理解有误",
                "mastery_level": 0.5,
                "mastered": False,
                "review_count": 3,
            }
        }


class MistakeKnowledgePointsResponse(BaseModel):
    """错题关联的知识点列表响应"""

    mistake_id: UUID = Field(..., description="错题ID")
    knowledge_points: List[KnowledgePointAssociation] = Field(
        default_factory=list, description="关联的知识点列表"
    )
    total_count: int = Field(..., description="知识点总数")

    class Config:
        json_schema_extra = {
            "example": {
                "mistake_id": "123e4567-e89b-12d3-a456-426614174000",
                "knowledge_points": [],
                "total_count": 3,
            }
        }


class KnowledgePointItem(BaseModel):
    """知识点列表项（用于筛选）"""

    name: str = Field(..., description="知识点名称")
    mistake_count: int = Field(..., description="错题数量")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "二次函数图像",
                "mistake_count": 5,
            }
        }


class KnowledgePointListResponse(BaseModel):
    """知识点列表响应（用于筛选）"""

    subject: str = Field(..., description="学科")
    knowledge_points: List[KnowledgePointItem] = Field(
        default_factory=list, description="知识点列表"
    )
    total_count: int = Field(..., description="知识点总数")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "math",
                "knowledge_points": [
                    {"name": "二次函数图像", "mistake_count": 5},
                    {"name": "三角函数", "mistake_count": 3},
                ],
                "total_count": 2,
            }
        }


# ============================================================================
# 薄弱知识链相关 Schema
# ============================================================================


class WeakKnowledgeChain(BaseModel):
    """薄弱知识链"""

    knowledge_point: str = Field(..., description="知识点名称")
    mastery_level: float = Field(..., description="掌握度 0.0-1.0")
    mistake_count: int = Field(..., description="错误次数")
    review_count: int = Field(..., description="复习次数")
    error_type: str = Field(..., description="主要错误类型")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_point": "二次函数图像",
                "mastery_level": 0.3,
                "mistake_count": 5,
                "review_count": 8,
                "error_type": "concept_misunderstanding",
                "suggestions": ["加强对称轴的理解", "多做配方法练习"],
            }
        }


class WeakKnowledgeChainsResponse(BaseModel):
    """薄弱知识链列表响应"""

    subject: str = Field(..., description="学科")
    chains: List[WeakKnowledgeChain] = Field(
        default_factory=list, description="薄弱知识链列表"
    )
    total_count: int = Field(..., description="薄弱知识链总数")

    class Config:
        json_schema_extra = {
            "example": {"subject": "math", "chains": [], "total_count": 5}
        }


# ============================================================================
# 知识图谱快照相关 Schema
# ============================================================================


class GraphNode(BaseModel):
    """图谱节点"""

    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="知识点名称")
    mastery: float = Field(..., description="掌握度 0.0-1.0")
    mistake_count: int = Field(..., description="错误次数")
    correct_count: int = Field(..., description="正确次数")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "二次函数图像",
                "mastery": 0.65,
                "mistake_count": 3,
                "correct_count": 7,
            }
        }


class GraphEdge(BaseModel):
    """图谱边（知识点关系）"""

    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relation: str = Field(..., description="关系类型")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "123e4567-e89b-12d3-a456-426614174000",
                "target": "123e4567-e89b-12d3-a456-426614174001",
                "relation": "prerequisite",
            }
        }


class GraphData(BaseModel):
    """图谱数据"""

    nodes: List[GraphNode] = Field(default_factory=list, description="节点列表")
    edges: List[GraphEdge] = Field(default_factory=list, description="边列表")

    class Config:
        json_schema_extra = {"example": {"nodes": [], "edges": []}}


class MasteryDistribution(BaseModel):
    """掌握度分布"""

    weak: int = Field(..., description="薄弱知识点数量 (< 0.4)")
    learning: int = Field(..., description="学习中知识点数量 (0.4-0.7)")
    mastered: int = Field(..., description="已掌握知识点数量 (>= 0.7)")

    class Config:
        json_schema_extra = {"example": {"weak": 5, "learning": 8, "mastered": 12}}


class KnowledgeGraphSnapshot(BaseModel):
    """知识图谱快照"""

    id: UUID = Field(..., description="快照ID")
    user_id: UUID = Field(..., description="用户ID")
    subject: str = Field(..., description="学科")
    snapshot_date: datetime = Field(..., description="快照时间")
    graph_data: GraphData = Field(..., description="图谱数据")
    mastery_distribution: MasteryDistribution = Field(..., description="掌握度分布")
    weak_knowledge_chains: List[WeakKnowledgeChain] = Field(
        default_factory=list, description="薄弱知识链"
    )
    total_knowledge_points: int = Field(..., description="知识点总数")
    mastered_count: int = Field(..., description="已掌握数量")
    learning_count: int = Field(..., description="学习中数量")
    weak_count: int = Field(..., description="薄弱数量")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "subject": "math",
                "snapshot_date": "2025-11-03T10:00:00",
                "graph_data": {"nodes": [], "edges": []},
                "mastery_distribution": {"weak": 5, "learning": 8, "mastered": 12},
                "weak_knowledge_chains": [],
                "total_knowledge_points": 25,
                "mastered_count": 12,
                "learning_count": 8,
                "weak_count": 5,
            }
        }


class CreateSnapshotRequest(BaseModel):
    """创建快照请求"""

    subject: str = Field(..., description="学科")
    period_type: str = Field(
        "manual", description="周期类型 (daily/weekly/monthly/manual)"
    )

    class Config:
        json_schema_extra = {"example": {"subject": "math", "period_type": "manual"}}


# ============================================================================
# 学习轨迹相关 Schema
# ============================================================================


class LearningTrackPoint(BaseModel):
    """学习轨迹点"""

    date: datetime = Field(..., description="活动时间")
    activity_type: str = Field(..., description="活动类型")
    result: str = Field(..., description="结果")
    mastery_after: float = Field(..., description="活动后掌握度")
    improvement: bool = Field(..., description="是否有进步")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-03T10:00:00",
                "activity_type": "review",
                "result": "correct",
                "mastery_after": 0.75,
                "improvement": True,
            }
        }


class LearningCurveResponse(BaseModel):
    """学习曲线响应"""

    knowledge_point_id: UUID = Field(..., description="知识点ID")
    knowledge_point_name: str = Field(..., description="知识点名称")
    current_mastery: float = Field(..., description="当前掌握度")
    curve: List[LearningTrackPoint] = Field(
        default_factory=list, description="学习曲线数据点"
    )
    total_activities: int = Field(..., description="总活动次数")

    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_point_id": "123e4567-e89b-12d3-a456-426614174000",
                "knowledge_point_name": "二次函数图像",
                "current_mastery": 0.75,
                "curve": [],
                "total_activities": 10,
            }
        }


# ============================================================================
# 知识点掌握度相关 Schema
# ============================================================================


class KnowledgeMasteryItem(BaseModel):
    """知识点掌握度项"""

    id: UUID = Field(..., description="掌握度记录ID")
    knowledge_point: str = Field(..., description="知识点名称")
    subject: str = Field(..., description="学科")
    mastery_level: float = Field(..., description="掌握度 0.0-1.0")
    confidence_level: float = Field(..., description="置信度 0.0-1.0")
    mistake_count: int = Field(..., description="错误次数")
    correct_count: int = Field(..., description="正确次数")
    total_attempts: int = Field(..., description="总尝试次数")
    last_practiced_at: Optional[datetime] = Field(None, description="最后练习时间")
    first_mastered_at: Optional[datetime] = Field(None, description="首次掌握时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "knowledge_point": "二次函数图像",
                "subject": "math",
                "mastery_level": 0.75,
                "confidence_level": 0.8,
                "mistake_count": 3,
                "correct_count": 7,
                "total_attempts": 10,
                "last_practiced_at": "2025-11-03T10:00:00",
                "first_mastered_at": None,
            }
        }


class UserKnowledgeMasteryResponse(BaseModel):
    """用户知识点掌握度列表响应"""

    subject: str = Field(..., description="学科")
    items: List[KnowledgeMasteryItem] = Field(
        default_factory=list, description="掌握度列表"
    )
    total_count: int = Field(..., description="总数")
    avg_mastery: float = Field(..., description="平均掌握度")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "math",
                "items": [],
                "total_count": 25,
                "avg_mastery": 0.65,
            }
        }


# ============================================================================
# 学科知识图谱响应 Schema (Phase 8.2)
# ============================================================================


class SubjectKnowledgeGraphResponse(BaseModel):
    """学科知识图谱完整响应"""

    subject: str = Field(..., description="学科")
    nodes: List[GraphNode] = Field(
        default_factory=list, description="知识点节点列表（按掌握度升序排列）"
    )
    weak_chains: List[WeakKnowledgeChain] = Field(
        default_factory=list, description="薄弱知识链列表"
    )
    mastery_distribution: MasteryDistribution = Field(..., description="掌握度分布统计")
    total_points: int = Field(..., description="知识点总数")
    avg_mastery: float = Field(..., description="平均掌握度")
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="复习推荐列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "math",
                "nodes": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "二次函数",
                        "mastery": 0.3,
                        "mistake_count": 5,
                        "correct_count": 2,
                    },
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "三角函数",
                        "mastery": 0.6,
                        "mistake_count": 2,
                        "correct_count": 5,
                    },
                ],
                "weak_chains": [],
                "mastery_distribution": {"weak": 1, "learning": 1, "mastered": 0},
                "total_points": 2,
                "avg_mastery": 0.45,
                "recommendations": [],
            }
        }
