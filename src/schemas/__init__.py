"""Schemas package for API request/response models"""

# Import all schemas here for easy access
from .knowledge_graph import (
    CreateSnapshotRequest,
    GraphData,
    GraphEdge,
    GraphNode,
    KnowledgeGraphSnapshot,
    KnowledgeMasteryItem,
    KnowledgePointAssociation,
    LearningCurveResponse,
    LearningTrackPoint,
    MasteryDistribution,
    MistakeKnowledgePointsResponse,
    UserKnowledgeMasteryResponse,
    WeakKnowledgeChain,
    WeakKnowledgeChainsResponse,
)

__all__ = [
    # Knowledge Graph Schemas
    "KnowledgePointAssociation",
    "MistakeKnowledgePointsResponse",
    "WeakKnowledgeChain",
    "WeakKnowledgeChainsResponse",
    "GraphNode",
    "GraphEdge",
    "GraphData",
    "MasteryDistribution",
    "KnowledgeGraphSnapshot",
    "CreateSnapshotRequest",
    "LearningTrackPoint",
    "LearningCurveResponse",
    "KnowledgeMasteryItem",
    "UserKnowledgeMasteryResponse",
]
