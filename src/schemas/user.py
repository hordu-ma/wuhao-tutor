"""
用户相关的Pydantic Schema模型
包含用户信息、个人资料、学习偏好等数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, validator


class UserRole(str, Enum):
    """用户角色枚举"""

    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


class GradeLevel(str, Enum):
    """学段枚举"""

    JUNIOR_1 = "junior_1"
    JUNIOR_2 = "junior_2"
    JUNIOR_3 = "junior_3"
    SENIOR_1 = "senior_1"
    SENIOR_2 = "senior_2"
    SENIOR_3 = "senior_3"


class SubjectType(str, Enum):
    """学科类型枚举"""

    MATH = "math"
    CHINESE = "chinese"
    ENGLISH = "english"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"


class LearningGoalType(str, Enum):
    """学习目标类型枚举"""

    GRADE_IMPROVEMENT = "grade_improvement"
    KNOWLEDGE_MASTERY = "knowledge_mastery"
    EXAM_PREPARATION = "exam_preparation"
    INTEREST_DEVELOPMENT = "interest_development"


# ========== 基础Schema模型 ==========


class UserBase(BaseModel):
    """用户基础模型"""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    name: str = Field(..., min_length=1, max_length=50, description="真实姓名")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    school: Optional[str] = Field(None, max_length=100, description="学校名称")
    grade_level: Optional[Union[GradeLevel, str]] = Field(None, description="学段")
    class_name: Optional[str] = Field(None, max_length=50, description="班级")
    institution: Optional[str] = Field(None, max_length=100, description="所属机构")
    parent_contact: Optional[str] = Field(
        None, pattern=r"^1[3-9]\d{9}$", description="家长联系电话"
    )
    parent_name: Optional[str] = Field(None, max_length=50, description="家长姓名")


class StudyPreference(BaseModel):
    """学习偏好"""

    subjects: List[SubjectType] = Field(default_factory=list, description="关注学科")
    difficulty_preference: Optional[int] = Field(
        None, ge=1, le=5, description="难度偏好"
    )
    study_time_preference: Optional[str] = Field(None, description="偏好学习时间段")
    learning_style: Optional[str] = Field(None, description="学习风格")


class LearningGoal(BaseModel):
    """学习目标"""

    goal_type: LearningGoalType
    subject: Optional[SubjectType] = None
    target_score: Optional[int] = Field(None, ge=0, le=100, description="目标分数")
    target_date: Optional[str] = Field(None, description="目标日期")
    description: str = Field(..., max_length=500, description="目标描述")
    priority: int = Field(default=3, ge=1, le=5, description="优先级")


# ========== 用户信息Schema模型 ==========


class UserProfile(UserBase):
    """用户个人资料"""

    study_subjects: Optional[List[SubjectType]] = Field(
        default_factory=list, description="学习学科"
    )
    study_goals: Optional[List[LearningGoal]] = Field(
        default_factory=list, description="学习目标"
    )
    study_preferences: Optional[StudyPreference] = Field(None, description="学习偏好")
    notification_enabled: bool = Field(default=True, description="是否启用通知")


class UserResponse(UserBase):
    """用户信息响应"""

    id: str
    role: UserRole
    is_active: bool
    is_verified: bool
    wechat_openid: Optional[str] = None
    wechat_unionid: Optional[str] = None
    notification_enabled: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """将UUID转换为字符串"""
        if isinstance(v, UUID):
            return str(v)
        return v

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.nickname or self.name

    @property
    def is_student(self) -> bool:
        """是否为学生"""
        return self.role == UserRole.STUDENT


class UserDetailResponse(UserResponse):
    """用户详细信息响应"""

    study_subjects: Optional[List[SubjectType]] = Field(default_factory=list)
    study_goals: Optional[List[LearningGoal]] = Field(default_factory=list)
    study_preferences: Optional[StudyPreference] = None


# ========== 用户管理Schema模型 ==========


class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    school: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[GradeLevel] = None
    class_name: Optional[str] = Field(None, max_length=50)
    institution: Optional[str] = Field(None, max_length=100)
    parent_contact: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    parent_name: Optional[str] = Field(None, max_length=50)
    notification_enabled: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "李四",
                "nickname": "小李",
                "school": "北京中学",
                "grade_level": "junior_2",
                "class_name": "初二(2)班",
                "notification_enabled": True,
            }
        }
    )


class UpdateStudyPreferencesRequest(BaseModel):
    """更新学习偏好请求"""

    subjects: Optional[List[SubjectType]] = Field(None, description="关注学科")
    difficulty_preference: Optional[int] = Field(
        None, ge=1, le=5, description="难度偏好"
    )
    study_time_preference: Optional[str] = Field(None, description="偏好学习时间段")
    learning_style: Optional[str] = Field(None, description="学习风格")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subjects": ["math", "physics", "chemistry"],
                "difficulty_preference": 3,
                "study_time_preference": "evening",
                "learning_style": "visual",
            }
        }
    )


class AddLearningGoalRequest(LearningGoal):
    """添加学习目标请求"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goal_type": "grade_improvement",
                "subject": "math",
                "target_score": 85,
                "target_date": "2024-06-30",
                "description": "数学成绩提升到85分以上",
                "priority": 4,
            }
        }
    )


class UpdateLearningGoalRequest(BaseModel):
    """更新学习目标请求"""

    goal_type: Optional[LearningGoalType] = None
    subject: Optional[SubjectType] = None
    target_score: Optional[int] = Field(None, ge=0, le=100)
    target_date: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_completed: Optional[bool] = None


# ========== 用户活动和统计Schema模型 ==========


class UserActivityResponse(BaseModel):
    """用户活动响应"""

    user_id: str
    total_questions: int = Field(..., description="总提问数")
    total_sessions: int = Field(..., description="总会话数")
    total_homework: int = Field(..., description="总作业数")
    study_streak_days: int = Field(..., description="连续学习天数")
    avg_daily_questions: float = Field(..., description="日均提问数")
    most_active_subject: Optional[str] = Field(None, description="最活跃学科")
    last_activity_at: Optional[datetime] = Field(None, description="最后活动时间")

    model_config = ConfigDict(from_attributes=True)


class UserProgressResponse(BaseModel):
    """用户学习进度响应"""

    user_id: str
    overall_progress: int = Field(..., ge=0, le=100, description="总体进度百分比")
    subject_progress: Dict[str, int] = Field(
        default_factory=dict, description="各学科进度"
    )
    goal_completion_rate: int = Field(..., ge=0, le=100, description="目标完成率")
    knowledge_points_mastered: int = Field(..., description="已掌握知识点数")
    total_knowledge_points: int = Field(..., description="总知识点数")
    strengths: List[str] = Field(default_factory=list, description="优势领域")
    weaknesses: List[str] = Field(default_factory=list, description="薄弱环节")
    recommendations: List[str] = Field(default_factory=list, description="学习建议")

    model_config = ConfigDict(from_attributes=True)


class UserRankingResponse(BaseModel):
    """用户排名响应"""

    user_id: str
    username: str
    avatar_url: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = None
    score: int = Field(..., description="积分")
    rank: int = Field(..., description="排名")
    rank_change: int = Field(default=0, description="排名变化")


class SubjectPerformance(BaseModel):
    """学科表现"""

    subject: SubjectType
    total_questions: int
    correct_rate: float = Field(..., ge=0.0, le=1.0, description="正确率")
    avg_difficulty: float = Field(..., ge=1.0, le=5.0, description="平均难度")
    time_spent: int = Field(..., description="学习时长(分钟)")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    last_study_at: Optional[datetime] = None


class UserPerformanceReport(BaseModel):
    """用户表现报告"""

    user_id: str
    report_period: str = Field(..., description="报告周期")
    overall_score: int = Field(..., ge=0, le=100, description="综合得分")
    subject_performances: List[SubjectPerformance]
    study_consistency: int = Field(..., ge=0, le=100, description="学习一致性")
    improvement_rate: float = Field(..., description="提升率")
    time_efficiency: int = Field(..., ge=0, le=100, description="时间效率")
    goal_achievements: List[str] = Field(default_factory=list, description="目标达成")
    areas_for_improvement: List[str] = Field(
        default_factory=list, description="待改进领域"
    )
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== 用户查询和分页Schema模型 ==========


class UserListQuery(BaseModel):
    """用户列表查询"""

    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    school: Optional[str] = Field(None, max_length=100)
    grade_level: Optional[GradeLevel] = None
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段")
    sort_order: Optional[str] = Field(
        default="desc", pattern="^(asc|desc)$", description="排序方向"
    )


class PaginatedResponse(BaseModel):
    """分页响应基础模型"""

    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class UserListResponse(PaginatedResponse):
    """用户列表响应"""

    items: List[UserResponse] = Field(..., description="用户列表")


class UserStatsResponse(BaseModel):
    """用户统计响应"""

    total_users: int
    active_users: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    verified_users: int
    student_count: int
    teacher_count: int
    parent_count: int
    role_distribution: Dict[str, int] = Field(default_factory=dict)
    grade_distribution: Dict[str, int] = Field(default_factory=dict)
    school_distribution: Dict[str, int] = Field(default_factory=dict)


# ========== 用户关系Schema模型 ==========


class UserRelationship(BaseModel):
    """用户关系"""

    related_user_id: str = Field(..., description="关联用户ID")
    relationship_type: str = Field(
        ..., description="关系类型: parent_child/teacher_student"
    )
    status: str = Field(default="active", description="状态")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRelationshipResponse(BaseModel):
    """用户关系响应"""

    user: UserResponse
    relationships: List[UserRelationship] = Field(
        default_factory=list, description="用户关系列表"
    )


class AddRelationshipRequest(BaseModel):
    """添加关系请求"""

    related_user_phone: str = Field(
        ..., pattern=r"^1[3-9]\d{9}$", description="关联用户手机号"
    )
    relationship_type: str = Field(..., description="关系类型")
    verification_code: Optional[str] = Field(None, description="验证码")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "related_user_phone": "13800138001",
                "relationship_type": "parent_child",
                "verification_code": "123456",
            }
        }
    )
