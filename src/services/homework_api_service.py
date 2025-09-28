"""
作业服务API适配器
为API层提供简化的作业服务接口，处理数据库会话管理
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.homework_service import HomeworkService
from src.schemas.homework import (
    HomeworkCreate, HomeworkUpdate, HomeworkResponse,
    HomeworkSubmissionCreate, HomeworkSubmissionResponse,
    HomeworkSubmissionDetail, HomeworkReviewResponse,
    HomeworkQuery, SubmissionQuery,
    HomeworkStatistics, HomeworkImageResponse
)
from src.schemas.common import PaginatedResponse

logger = logging.getLogger("homework_api_service")


class HomeworkAPIService:
    """
    作业服务API适配器
    简化API调用，自动处理数据库会话
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.homework_service = HomeworkService()

    # ========== 作业模板管理 ==========

    async def create_homework(
        self,
        homework_data: Dict[str, Any],
        creator_id: str,
        creator_name: str
    ) -> HomeworkResponse:
        """创建作业模板"""
        from src.schemas.homework import HomeworkCreate

        homework_create = HomeworkCreate(**homework_data)
        homework = await self.homework_service.create_homework(
            session=self.db,
            homework_data=homework_create,
            creator_id=UUID(creator_id),
            creator_name=creator_name
        )
        return HomeworkResponse.from_orm(homework)

    async def get_homework(self, homework_id: str) -> Optional[HomeworkResponse]:
        """获取作业模板"""
        homework = await self.homework_service.get_homework(
            session=self.db,
            homework_id=UUID(homework_id)
        )
        return HomeworkResponse.from_orm(homework) if homework else None

    async def update_homework(
        self,
        homework_id: str,
        update_data: Dict[str, Any]
    ) -> HomeworkResponse:
        """更新作业模板"""
        homework = await self.homework_service.update_homework(
            session=self.db,
            homework_id=homework_id,
            update_data=update_data
        )
        return HomeworkResponse.from_orm(homework)

    async def list_homeworks(
        self,
        filters: Dict[str, Any],
        creator_id: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取作业模板列表"""
        result = await self.homework_service.list_homeworks(
            session=self.db,
            filters=filters,
            creator_id=UUID(creator_id) if creator_id else None,
            page=page,
            size=size
        )
        return result

    # ========== 作业提交管理 ==========

    async def create_submission(
        self,
        homework_id: str,
        student_id: str,
        student_name: str,
        submission_data: Dict[str, Any]
    ) -> HomeworkSubmissionResponse:
        """创建作业提交"""
        from src.schemas.homework import HomeworkSubmissionCreate
        # 添加homework_id到submission_data中
        submission_data_with_id = {**submission_data, "homework_id": homework_id}
        submission_create = HomeworkSubmissionCreate(**submission_data_with_id)
        submission = await self.homework_service.create_submission(
            session=self.db,
            submission_data=submission_create,
            student_id=UUID(student_id),
            student_name=student_name
        )
        return HomeworkSubmissionResponse.from_orm(submission)

    async def get_submission(
        self,
        submission_id: str,
        student_id: str
    ) -> Optional[HomeworkSubmissionResponse]:
        """获取作业提交"""
        submission = await self.homework_service.get_submission(
            session=self.db,
            submission_id=UUID(submission_id)
        )
        # 验证提交属于当前学生
        if submission and str(submission.student_id) != student_id:
            return None
        return HomeworkSubmissionResponse.from_orm(submission) if submission else None

    async def get_submission_with_details(
        self,
        submission_id: str,
        student_id: str
    ) -> Optional[HomeworkSubmissionDetail]:
        """获取作业提交详情"""
        details = await self.homework_service.get_submission_with_details(
            session=self.db,
            submission_id=UUID(submission_id)
        )
        # 验证提交属于当前学生
        if details and str(details.student_id) != student_id:
            return None
        return details

    async def upload_homework_images(
        self,
        submission_id: str,
        files: List[Any]
    ) -> List[HomeworkImageResponse]:
        """上传作业图片"""
        images = await self.homework_service.upload_homework_images(
            session=self.db,
            submission_id=UUID(submission_id),
            image_files=files
        )
        return [HomeworkImageResponse.from_orm(img) for img in images]

    async def start_ai_review(
        self,
        submission_id: str
    ) -> HomeworkReviewResponse:
        """启动AI批改"""
        review = await self.homework_service.start_ai_review(
            session=self.db,
            submission_id=UUID(submission_id)
        )
        return HomeworkReviewResponse.from_orm(review)

    async def list_submissions(
        self,
        student_id: str,
        filters: Dict[str, Any],
        page: int = 1,
        size: int = 20
    ) -> PaginatedResponse:
        """获取作业提交列表"""
        return await self.homework_service.list_submissions(
            session=self.db,
            student_id=student_id,
            filters=filters,
            page=page,
            size=size
        )

    async def get_homework_statistics(
        self,
        student_id: str,
        subject: Optional[str] = None,
        days: int = 30
    ) -> HomeworkStatistics:
        """获取作业统计信息"""
        stats = await self.homework_service.get_homework_statistics(
            session=self.db,
            student_id=student_id,
            subject=subject,
            days=days
        )
        return HomeworkStatistics(**stats)

    # ========== 健康检查 ==========

    async def health_check(self) -> bool:
        """健康检查"""
        return await self.homework_service.health_check(self.db)

    async def check_ai_service_status(self) -> bool:
        """检查AI服务状态"""
        return await self.homework_service.check_ai_service_status()


def get_homework_api_service(
    db: AsyncSession = Depends(get_db)
) -> HomeworkAPIService:
    """
    获取作业API服务实例

    Args:
        db: 数据库会话

    Returns:
        作业API服务实例
    """
    return HomeworkAPIService(db)
