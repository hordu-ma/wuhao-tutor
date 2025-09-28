"""
数据模型包
导出所有数据模型供其他模块使用
"""

# 基础模型
from .base import BaseModel

# 用户相关模型
from .user import User, UserSession, GradeLevel, UserRole

# 学习记录模型
from .study import (
    MistakeRecord, KnowledgeMastery, ReviewSchedule, StudySession,
    Subject, DifficultyLevel, MasteryStatus
)

# 知识图谱模型
from .knowledge import (
    KnowledgeNode, KnowledgeRelation, LearningPath,
    UserLearningPath, KnowledgeGraph,
    NodeType, RelationType
)

# 作业相关模型
from .homework import (
    Homework, HomeworkSubmission, HomeworkImage, HomeworkReview,
    SubjectType, HomeworkType, DifficultyLevel as HomeworkDifficultyLevel,
    SubmissionStatus, ReviewStatus
)

# 导出所有模型类
__all__ = [
    # 基础模型
    "BaseModel",

    # 用户模型
    "User",
    "UserSession",
    "GradeLevel",
    "UserRole",

    # 学习模型
    "MistakeRecord",
    "KnowledgeMastery",
    "ReviewSchedule",
    "StudySession",
    "Subject",
    "DifficultyLevel",
    "MasteryStatus",

    # 知识图谱模型
    "KnowledgeNode",
    "KnowledgeRelation",
    "LearningPath",
    "UserLearningPath",
    "KnowledgeGraph",
    "NodeType",
    "RelationType",

    # 作业模型
    "Homework",
    "HomeworkSubmission",
    "HomeworkImage",
    "HomeworkReview",
    "SubjectType",
    "HomeworkType",
    "HomeworkDifficultyLevel",
    "SubmissionStatus",
    "ReviewStatus",
]
