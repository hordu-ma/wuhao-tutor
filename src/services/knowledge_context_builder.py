"""
KnowledgeContextBuilder 服务 - MCP上下文构建器

负责为AI个性化问答构建用户学情上下文，包括：
- 薄弱知识点分析
- 学习偏好提取
- 上下文摘要生成
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.homework import Homework, HomeworkSubmission
from src.models.learning import Question

logger = get_logger(__name__)


@dataclass
class WeakKnowledgePoint:
    """薄弱知识点数据模型"""

    knowledge_id: str
    knowledge_name: str
    subject: str
    error_rate: float  # 错误率 (0-1)
    error_count: int  # 错误次数
    total_count: int  # 总尝试次数
    last_error_time: datetime
    severity_score: float  # 严重程度评分 (0-1)
    prerequisite_knowledge: List[str]  # 前置知识点


@dataclass
class LearningPreference:
    """学习偏好数据模型"""

    active_subjects: Dict[str, float]  # 活跃学科分布
    difficulty_preference: Dict[str, float]  # 难度偏好
    time_preference: Dict[str, int]  # 时间偏好(小时分布)
    interaction_preference: Dict[str, float]  # 交互偏好
    learning_pace: str  # 学习节奏: slow/medium/fast
    focus_duration: int  # 专注时长(分钟)


@dataclass
class ContextSummary:
    """上下文摘要数据模型"""

    total_questions: int
    total_study_time: int  # 分钟
    recent_activity_days: int
    dominant_subject: str
    current_level: str  # beginner/intermediate/advanced
    learning_streak: int  # 连续学习天数


@dataclass
class LearningContext:
    """完整学习上下文数据模型"""

    user_id: str
    generated_at: datetime
    weak_knowledge_points: List[WeakKnowledgePoint]
    learning_preferences: LearningPreference
    context_summary: ContextSummary
    recent_errors: List[Dict[str, Any]]
    knowledge_mastery: Dict[str, float]  # 知识点掌握度
    study_patterns: Dict[str, Any]  # 学习模式


class KnowledgeContextBuilder:
    """用户学情上下文构建器

    为AI个性化问答提供用户的学习上下文信息
    """

    def __init__(self):
        self.weak_threshold = 0.6  # 薄弱知识点错误率阈值
        self.time_decay_factor = 0.1  # 时间衰减因子
        self.max_context_days = 90  # 最大上下文天数

    async def build_context(
        self,
        user_id: str,
        subject: Optional[str] = None,
        session_type: str = "learning",
    ) -> LearningContext:
        """构建用户学情上下文

        Args:
            user_id: 用户ID
            subject: 学科筛选（可选）
            session_type: 会话类型 learning/homework

        Returns:
            LearningContext: 完整的学习上下文
        """
        from src.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # 并行获取各类上下文数据
            weak_points = await self._analyze_weak_knowledge_points(
                session, user_id, subject
            )
            preferences = await self._extract_learning_preferences(
                session, user_id, subject
            )
            summary = await self._generate_context_summary(session, user_id, subject)
            recent_errors = await self._get_recent_errors(session, user_id, subject)
            mastery = await self._calculate_knowledge_mastery(session, user_id, subject)
            patterns = await self._analyze_study_patterns(session, user_id, subject)

            return LearningContext(
                user_id=user_id,
                generated_at=datetime.utcnow(),
                weak_knowledge_points=weak_points,
                learning_preferences=preferences,
                context_summary=summary,
                recent_errors=recent_errors,
                knowledge_mastery=mastery,
                study_patterns=patterns,
            )

    async def _analyze_weak_knowledge_points(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> List[WeakKnowledgePoint]:
        """分析薄弱知识点

        算法核心：
        1. 查询用户作业提交和问答记录
        2. 统计各知识点错误率，应用时间衰减权重
        3. 筛选错误率>=阈值的知识点并排序
        """
        weak_points = []

        try:
            # 查询作业提交记录
            homework_query = select(HomeworkSubmission).where(
                and_(
                    HomeworkSubmission.student_id == user_id,
                    HomeworkSubmission.status == "reviewed",
                    HomeworkSubmission.weak_knowledge_points.is_not(None),
                )
            )

            if subject:
                homework_query = homework_query.join(Homework).where(
                    Homework.subject == subject
                )

            homework_result = await session.execute(homework_query)
            submissions = homework_result.scalars().all()

            # 统计知识点错误情况
            knowledge_stats = {}

            for submission in submissions:
                submitted_at = submission.submitted_at or submission.created_at
                # 类型转换：确保是 datetime 对象
                if submitted_at is None:
                    submitted_at = datetime.utcnow()
                elif hasattr(submitted_at, "replace") and hasattr(
                    submitted_at, "tzinfo"
                ):
                    # 是 datetime 对象，移除时区信息
                    submitted_at = (
                        submitted_at.replace(tzinfo=None)
                        if submitted_at.tzinfo
                        else submitted_at
                    )
                else:
                    # 其他情况，使用当前时间
                    submitted_at = datetime.utcnow()

                time_weight = self._calculate_time_decay_weight(submitted_at)  # type: ignore

                # 解析薄弱知识点数据
                weak_points_data = submission.weak_knowledge_points or []
                if isinstance(weak_points_data, str):
                    try:
                        weak_points_data = json.loads(weak_points_data)
                    except json.JSONDecodeError:
                        continue

                # 处理知识点统计
                for point_data in weak_points_data:
                    if isinstance(point_data, dict):
                        knowledge_id = point_data.get("knowledge_id") or point_data.get(
                            "name", "unknown"
                        )
                        knowledge_name = point_data.get("name", knowledge_id)
                        error_count = point_data.get("error_count", 1)
                        total_count = point_data.get("total_count", 1)

                        if knowledge_id not in knowledge_stats:
                            knowledge_stats[knowledge_id] = {
                                "name": knowledge_name,
                                "total_errors": 0,
                                "total_attempts": 0,
                                "weighted_errors": 0,
                                "weighted_attempts": 0,
                                "last_error_time": submitted_at,
                                "subject": getattr(submission, "homework", {}).get(
                                    "subject"
                                )
                                or subject
                                or "数学",
                            }

                        stats = knowledge_stats[knowledge_id]
                        stats["total_errors"] += error_count
                        stats["total_attempts"] += total_count
                        stats["weighted_errors"] += error_count * time_weight
                        stats["weighted_attempts"] += total_count * time_weight

                        if submitted_at > stats["last_error_time"]:
                            stats["last_error_time"] = submitted_at

            # 从问答记录补充数据
            question_query = select(Question).where(Question.user_id == user_id)
            if subject:
                question_query = question_query.where(Question.subject == subject)

            question_result = await session.execute(question_query)
            questions = question_result.scalars().all()

            for question in questions:
                question_time = question.created_at
                # 类型转换：确保是 datetime 对象
                if question_time is None:
                    question_time = datetime.utcnow()
                elif hasattr(question_time, "replace") and hasattr(
                    question_time, "tzinfo"
                ):
                    question_time = (
                        question_time.replace(tzinfo=None)
                        if question_time.tzinfo
                        else question_time
                    )
                else:
                    question_time = datetime.utcnow()

                time_weight = self._calculate_time_decay_weight(question_time)  # type: ignore
                content = question.content.lower()

                # 从问题内容推断薄弱知识点
                inferred_points = self._extract_knowledge_from_question(
                    content, subject
                )

                for point_name in inferred_points:
                    knowledge_id = f"inferred_{point_name}"

                    if knowledge_id not in knowledge_stats:
                        knowledge_stats[knowledge_id] = {
                            "name": point_name,
                            "total_errors": 0,
                            "total_attempts": 0,
                            "weighted_errors": 0,
                            "weighted_attempts": 0,
                            "last_error_time": question_time,
                            "subject": getattr(question, "subject", None)
                            or subject
                            or "数学",
                        }

                    stats = knowledge_stats[knowledge_id]
                    stats["total_attempts"] += 1
                    stats["weighted_attempts"] += time_weight

                    if self._is_help_seeking_question(content):
                        stats["total_errors"] += 1
                        stats["weighted_errors"] += time_weight
                        if question_time > stats["last_error_time"]:
                            stats["last_error_time"] = question_time

            # 计算错误率并筛选薄弱知识点
            for knowledge_id, stats in knowledge_stats.items():
                if stats["total_attempts"] == 0:
                    continue

                # 使用加权错误率
                if stats["weighted_attempts"] > 0:
                    error_rate = stats["weighted_errors"] / stats["weighted_attempts"]
                else:
                    error_rate = stats["total_errors"] / stats["total_attempts"]

                # 筛选错误率超过阈值的知识点
                if error_rate >= self.weak_threshold:
                    last_error_time = stats["last_error_time"]
                    time_weight = self._calculate_time_decay_weight(last_error_time)
                    severity_score = self._calculate_severity_score(
                        error_rate, stats["total_errors"], time_weight
                    )

                    weak_point = WeakKnowledgePoint(
                        knowledge_id=knowledge_id,
                        knowledge_name=stats["name"],
                        subject=stats["subject"],
                        error_rate=error_rate,
                        error_count=stats["total_errors"],
                        total_count=stats["total_attempts"],
                        last_error_time=last_error_time,
                        severity_score=severity_score,
                        prerequisite_knowledge=[],
                    )
                    weak_points.append(weak_point)

            # 按严重程度排序，限制返回数量
            weak_points.sort(key=lambda x: x.severity_score, reverse=True)
            return weak_points[:20]

        except Exception as e:
            logger.error(f"分析薄弱知识点失败: {str(e)}")
            return []

    async def _extract_learning_preferences(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> LearningPreference:
        """提取学习偏好

        基于用户历史学习行为分析偏好特征
        """
        try:
            # 1. 分析活跃学科分布
            subject_query = (
                select(
                    func.coalesce(Question.subject, "数学").label("subject"),
                    func.count().label("count"),
                )
                .where(Question.user_id == user_id)
                .group_by(Question.subject)
            )

            subject_result = await session.execute(subject_query)
            subject_rows = subject_result.fetchall()

            total_questions = 0
            count_list = []
            for row in subject_rows:
                count_list.append(getattr(row, "count", 0))
            total_questions = sum(count_list) if count_list else 0

            active_subjects = {}
            if total_questions > 0:
                for row in subject_rows:
                    subject_name = getattr(row, "subject", None) or "数学"
                    count_val = getattr(row, "count", 0)
                    active_subjects[subject_name] = count_val / total_questions
            else:
                active_subjects = {"数学": 1.0}

            # 2. 分析时间偏好（基于提问时间分布）
            time_preference = {}
            for i in range(24):
                time_preference[str(i)] = 0

            questions_query = select(Question.created_at).where(
                Question.user_id == user_id
            )
            questions_result = await session.execute(questions_query)
            question_times = questions_result.scalars().all()

            if question_times:
                for created_at in question_times:
                    if created_at and hasattr(created_at, "hour"):
                        hour = str(created_at.hour)
                        time_preference[hour] = time_preference.get(hour, 0) + 1
            else:
                # 默认活跃时间（学习时间）
                time_preference.update({"9": 2, "14": 3, "19": 5, "20": 4})

            # 3. 分析难度偏好（基于作业难度分布）
            difficulty_query = (
                select(
                    func.coalesce(Homework.difficulty_level, "medium").label(
                        "difficulty"
                    ),
                    func.count().label("count"),
                )
                .select_from(HomeworkSubmission.__table__.join(Homework.__table__))
                .where(HomeworkSubmission.student_id == user_id)
                .group_by(Homework.difficulty_level)
            )

            difficulty_result = await session.execute(difficulty_query)
            difficulty_rows = difficulty_result.fetchall()

            total_homeworks = 0
            homework_count_list = []
            for row in difficulty_rows:
                homework_count_list.append(getattr(row, "count", 0))
            total_homeworks = sum(homework_count_list) if homework_count_list else 0

            difficulty_preference = {}
            if total_homeworks > 0:
                for row in difficulty_rows:
                    difficulty_level = getattr(row, "difficulty", None) or "medium"
                    count_val = getattr(row, "count", 0)
                    difficulty_preference[difficulty_level] = (
                        count_val / total_homeworks
                    )
            else:
                difficulty_preference = {"easy": 0.3, "medium": 0.5, "hard": 0.2}

            # 4. 分析交互偏好（基于问题内容特征）
            interaction_preference = {"text": 0.7, "image": 0.2, "voice": 0.1}

            # 5. 推断学习节奏和专注时长
            learning_pace = "medium"
            focus_duration = 30

            # 基于问题提问频率推断学习节奏
            if total_questions > 50:
                learning_pace = "fast"
                focus_duration = 45
            elif total_questions < 10:
                learning_pace = "slow"
                focus_duration = 20

            return LearningPreference(
                active_subjects=active_subjects,
                difficulty_preference=difficulty_preference,
                time_preference=time_preference,
                interaction_preference=interaction_preference,
                learning_pace=learning_pace,
                focus_duration=focus_duration,
            )

        except Exception as e:
            logger.error(f"提取学习偏好失败: {str(e)}")
            # 返回默认偏好
            return LearningPreference(
                active_subjects={"数学": 1.0},
                difficulty_preference={"easy": 0.3, "medium": 0.5, "hard": 0.2},
                time_preference={"19": 5, "20": 4, "21": 3},
                interaction_preference={"text": 0.7, "image": 0.2, "voice": 0.1},
                learning_pace="medium",
                focus_duration=30,
            )

    async def _generate_context_summary(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> ContextSummary:
        """生成上下文摘要

        统计用户学习概况
        """
        try:
            # 1. 统计总问题数
            questions_query = (
                select(func.count())
                .select_from(Question)
                .where(Question.user_id == user_id)
            )
            if subject:
                questions_query = questions_query.where(Question.subject == subject)

            questions_result = await session.execute(questions_query)
            total_questions = questions_result.scalar() or 0

            # 2. 统计总学习时间（估算）
            # 假设每个问题平均需要5分钟思考和提问
            total_study_time = total_questions * 5

            # 3. 统计最近活跃天数
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_activity_query = select(
                func.count(func.distinct(func.date(Question.created_at)))
            ).where(
                and_(
                    Question.user_id == user_id, Question.created_at >= thirty_days_ago
                )
            )

            if subject:
                recent_activity_query = recent_activity_query.where(
                    Question.subject == subject
                )

            recent_activity_result = await session.execute(recent_activity_query)
            recent_activity_days = recent_activity_result.scalar() or 0

            # 4. 确定主导学科
            dominant_subject_query = (
                select(func.coalesce(Question.subject, "数学").label("subject"))
                .where(Question.user_id == user_id)
                .group_by(Question.subject)
                .order_by(func.count().desc())
                .limit(1)
            )

            dominant_result = await session.execute(dominant_subject_query)
            dominant_subject = dominant_result.scalar() or "数学"

            # 5. 评估当前水平
            current_level = "beginner"
            if total_questions > 20:
                current_level = "intermediate"
            if total_questions > 100:
                current_level = "advanced"

            # 6. 计算学习连续性
            learning_streak = min(recent_activity_days, 30)

            return ContextSummary(
                total_questions=total_questions,
                total_study_time=total_study_time,
                recent_activity_days=recent_activity_days,
                dominant_subject=dominant_subject,
                current_level=current_level,
                learning_streak=learning_streak,
            )

        except Exception as e:
            logger.error(f"生成上下文摘要失败: {str(e)}")
            return ContextSummary(
                total_questions=0,
                total_study_time=0,
                recent_activity_days=0,
                dominant_subject="数学",
                current_level="beginner",
                learning_streak=0,
            )

    def _calculate_time_decay_weight(self, timestamp: datetime) -> float:
        """计算时间衰减权重"""
        current_time = datetime.utcnow()
        time_diff = (current_time - timestamp).total_seconds() / 86400  # 转换为天数

        # 指数衰减: weight = e^(-decay_factor * days)
        weight = math.exp(-self.time_decay_factor * time_diff)
        return max(weight, 0.1)  # 最小权重0.1

    def _calculate_severity_score(
        self, error_rate: float, error_count: int, time_weight: float
    ) -> float:
        """计算薄弱知识点严重程度评分"""
        # 综合考虑错误率、错误次数和时间权重
        base_score = error_rate * 0.6  # 错误率占60%
        frequency_score = min(error_count / 10, 1.0) * 0.3  # 错误频次占30%
        recency_score = time_weight * 0.1  # 时间权重占10%

        return min(base_score + frequency_score + recency_score, 1.0)

    def _extract_knowledge_from_question(
        self, content: str, subject: Optional[str]
    ) -> List[str]:
        """从问题内容提取知识点（简化实现）"""
        knowledge_keywords = {
            "数学": ["函数", "方程", "几何", "代数", "概率", "统计", "微积分"],
            "语文": ["阅读理解", "作文", "古诗词", "文言文", "语法"],
            "英语": ["语法", "词汇", "阅读", "写作", "听力", "口语"],
        }

        current_subject = subject or "数学"
        keywords = knowledge_keywords.get(current_subject, [])

        found_points = []
        for keyword in keywords:
            if keyword in content:
                found_points.append(keyword)

        return found_points

    def _is_help_seeking_question(self, content: str) -> bool:
        """判断是否为求助性质的问题"""
        help_indicators = ["怎么", "如何", "不会", "不懂", "帮助", "解答", "不明白"]
        return any(indicator in content for indicator in help_indicators)

    async def _get_recent_errors(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取最近错题"""
        # TODO: 查询最近的错题记录
        return []

    async def _calculate_knowledge_mastery(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> Dict[str, float]:
        """计算知识点掌握度"""
        # TODO: 分析各知识点的掌握程度
        return {}

    async def _analyze_study_patterns(
        self, session: AsyncSession, user_id: str, subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析学习模式"""
        # TODO: 分析用户学习习惯和模式
        return {}


# 单例实例
knowledge_context_builder = KnowledgeContextBuilder()


async def main():
    """测试函数"""
    # 测试用例
    test_user_id = "test-user-123"

    builder = KnowledgeContextBuilder()
    context = await builder.build_context(test_user_id)

    print(f"用户 {test_user_id} 的学情上下文:")
    print(f"- 薄弱知识点数量: {len(context.weak_knowledge_points)}")
    print(f"- 学习偏好: {context.learning_preferences.learning_pace}")
    print(f"- 生成时间: {context.generated_at}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
