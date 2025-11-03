"""
数据模型包
导出所有数据模型供其他模块使用
"""

# 基础模型
from .base import BaseModel

# 作业相关模型
from .homework import DifficultyLevel as HomeworkDifficultyLevel
from .homework import (
    Homework,
    HomeworkImage,
    HomeworkReview,
    HomeworkSubmission,
    HomeworkType,
    ReviewStatus,
    SubjectType,
    SubmissionStatus,
)

# 知识图谱模型
from .knowledge import (
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeRelation,
    LearningPath,
    NodeType,
    RelationType,
    UserLearningPath,
)

# 知识图谱增强模型（新）
from .knowledge_graph import (
    ErrorType,
    KnowledgePointLearningTrack,
    MistakeKnowledgePoint,
    UserKnowledgeGraphSnapshot,
    WeakChainType,
)

# 学习问答模型
from .learning import (
    Answer,
    ChatSession,
    LearningAnalytics,
    Question,
    QuestionType,
    SessionStatus,
)

# 学习记录模型
from .study import (
    DifficultyLevel,
    KnowledgeMastery,
    MasteryStatus,
    MistakeRecord,
    ReviewSchedule,
    StudySession,
    Subject,
)

# 用户相关模型
from .user import GradeLevel, User, UserRole, UserSession

# 导出所有模型类
__all__ = [
    # 基础模型
    "BaseModel",
    # 用户模型
    "User",
    "UserSession",
    "GradeLevel",
    "UserRole",
    # 学习问答模型
    "ChatSession",
    "Question",
    "Answer",
    "LearningAnalytics",
    "QuestionType",
    "SessionStatus",
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
    # 知识图谱增强模型
    "MistakeKnowledgePoint",
    "UserKnowledgeGraphSnapshot",
    "KnowledgePointLearningTrack",
    "ErrorType",
    "WeakChainType",
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
