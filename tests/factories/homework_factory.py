"""
作业相关数据工厂
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from factory.base import Factory
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.faker import Faker

from src.models.homework import (
    DifficultyLevel,
    Homework,
    HomeworkSubmission,
    HomeworkType,
    SubjectType,
    SubmissionStatus,
)


class HomeworkModelFactory(Factory):
    """Homework 模型工厂（使用 factory-boy）"""

    class Meta:
        model = Homework

    id = LazyFunction(lambda: str(uuid.uuid4()))
    title = Sequence(lambda n: f"作业{n}: 测试作业")
    description = Faker("text", locale="zh_CN", max_nb_chars=200)
    subject = SubjectType.MATH.value
    homework_type = HomeworkType.DAILY.value
    difficulty_level = DifficultyLevel.MEDIUM.value

    grade_level = "senior_1"
    chapter = Sequence(lambda n: f"第{n}章")
    knowledge_points = LazyFunction(lambda: ["知识点1", "知识点2"])

    estimated_duration = 60
    deadline = LazyFunction(lambda: datetime.utcnow() + timedelta(days=7))

    creator_id = LazyFunction(lambda: str(uuid.uuid4()))
    creator_name = Faker("name", locale="zh_CN")

    is_active = True
    is_template = False

    total_submissions = 0
    avg_score = None

    created_at = LazyFunction(datetime.utcnow)
    updated_at = LazyFunction(datetime.utcnow)
    deleted_at = None


class HomeworkSubmissionModelFactory(Factory):
    """HomeworkSubmission 模型工厂（使用 factory-boy）"""

    class Meta:
        model = HomeworkSubmission

    id = LazyFunction(lambda: str(uuid.uuid4()))
    homework_id = LazyFunction(lambda: str(uuid.uuid4()))
    student_id = LazyFunction(lambda: str(uuid.uuid4()))
    student_name = Faker("name", locale="zh_CN")

    submission_title = Sequence(lambda n: f"作业提交{n}")
    submission_note = Faker("text", locale="zh_CN", max_nb_chars=100)

    status = SubmissionStatus.UPLOADED.value
    submitted_at = LazyFunction(datetime.utcnow)

    total_score = None
    accuracy_rate = None
    completion_time = None

    ai_review_data = None

    created_at = LazyFunction(datetime.utcnow)
    updated_at = LazyFunction(datetime.utcnow)
    deleted_at = None


class HomeworkFactory:
    """作业数据工厂（传统方法）"""

    @staticmethod
    def create_homework(
        homework_id: Optional[str] = None,
        title: str = "数学练习题",
        subject: str = SubjectType.MATH.value,
        creator_id: Optional[str] = None,
        homework_type: str = HomeworkType.DAILY.value,
        difficulty_level: str = DifficultyLevel.MEDIUM.value,
        **kwargs,
    ) -> Homework:
        """创建测试作业"""
        homework = Homework(
            id=homework_id or str(uuid.uuid4()),
            title=title,
            subject=subject,
            creator_id=creator_id or str(uuid.uuid4()),
            homework_type=homework_type,
            difficulty_level=difficulty_level,
            description=kwargs.get("description", "这是一个测试作业"),
            grade_level=kwargs.get("grade_level", "senior_1"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["description", "grade_level"]
            },
        )
        return homework

    @staticmethod
    def create_math_homework(
        homework_id: Optional[str] = None,
        title: str = "数学作业",
        difficulty_level: str = DifficultyLevel.MEDIUM.value,
        **kwargs,
    ) -> Homework:
        """创建数学作业"""
        return HomeworkFactory.create_homework(
            homework_id=homework_id,
            title=title,
            subject=SubjectType.MATH.value,
            difficulty_level=difficulty_level,
            **kwargs,
        )

    @staticmethod
    def create_english_homework(
        homework_id: Optional[str] = None,
        title: str = "英语作业",
        difficulty_level: str = DifficultyLevel.MEDIUM.value,
        **kwargs,
    ) -> Homework:
        """创建英语作业"""
        return HomeworkFactory.create_homework(
            homework_id=homework_id,
            title=title,
            subject=SubjectType.ENGLISH.value,
            difficulty_level=difficulty_level,
            **kwargs,
        )

    @staticmethod
    def create_batch_homework(
        count: int = 5, subject: str = SubjectType.MATH.value, **kwargs
    ) -> List[Homework]:
        """批量创建作业"""
        return [
            HomeworkFactory.create_homework(
                title=f"{subject}作业{i}",
                subject=subject,
                **kwargs,
            )
            for i in range(count)
        ]


class HomeworkSubmissionFactory:
    """作业提交数据工厂（传统方法）"""

    @staticmethod
    def create_homework_submission(
        submission_id: Optional[str] = None,
        homework_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: str = SubmissionStatus.UPLOADED.value,
        **kwargs,
    ) -> HomeworkSubmission:
        """创建测试作业提交"""
        submission = HomeworkSubmission(
            id=submission_id or str(uuid.uuid4()),
            homework_id=homework_id or str(uuid.uuid4()),
            student_id=student_id or str(uuid.uuid4()),
            student_name=kwargs.get("student_name", "测试学生"),
            status=status,
            submission_title=kwargs.get("submission_title", "测试作业提交"),
            submission_note=kwargs.get("submission_note", "这是作业提交"),
            total_score=kwargs.get("total_score"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "submission_title",
                    "submission_note",
                    "total_score",
                    "student_name",
                ]
            },
        )
        return submission

    @staticmethod
    def create_reviewed_submission(
        submission_id: Optional[str] = None,
        homework_id: Optional[str] = None,
        student_id: Optional[str] = None,
        total_score: float = 85.0,
        **kwargs,
    ) -> HomeworkSubmission:
        """创建已批改的作业提交"""
        return HomeworkSubmissionFactory.create_homework_submission(
            submission_id=submission_id,
            homework_id=homework_id,
            student_id=student_id,
            status=SubmissionStatus.REVIEWED.value,
            total_score=total_score,
            accuracy_rate=kwargs.get("accuracy_rate", 0.85),
            **kwargs,
        )

    @staticmethod
    def create_batch_submissions(
        homework_id: str, student_ids: List[str], **kwargs
    ) -> List[HomeworkSubmission]:
        """为一个作业批量创建提交"""
        return [
            HomeworkSubmissionFactory.create_homework_submission(
                homework_id=homework_id,
                student_id=student_id,
                **kwargs,
            )
            for student_id in student_ids
        ]
