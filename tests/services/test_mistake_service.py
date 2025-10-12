"""
错题服务单元测试
测试 MistakeService 核心功能

作者: AI Agent
创建时间: 2025-10-12
版本: v2.0
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.study import MistakeRecord, MistakeReview
from src.schemas.mistake import CreateMistakeRequest, ReviewCompleteRequest
from src.services.mistake_service import MistakeService


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def mistake_service(db_session):
    """创建错题服务实例"""
    return MistakeService(db_session)


class TestMistakeService:
    """测试错题服务"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, mistake_service):
        """测试服务初始化"""
        assert mistake_service is not None
        assert mistake_service.algorithm is not None
        assert mistake_service.mistake_repo is not None
        assert mistake_service.review_repo is not None

    @pytest.mark.asyncio
    async def test_create_mistake(self, mistake_service):
        """测试创建错题"""
        user_id = uuid4()
        request = CreateMistakeRequest(
            title="测试错题",
            subject="math",
            difficulty_level=3,
            question_content="这是一道测试题",
            knowledge_points=["知识点1", "知识点2"],
        )

        result = await mistake_service.create_mistake(user_id, request)

        assert result.id is not None
        assert result.title == "测试错题"
        assert result.subject == "math"
        assert result.mastery_status == "learning"

    @pytest.mark.asyncio
    async def test_get_mistake_list(self, mistake_service):
        """测试获取错题列表"""
        user_id = uuid4()

        # 创建一些错题
        for i in range(3):
            request = CreateMistakeRequest(
                title=f"错题 {i+1}",
                subject="math",
                question_content=f"题目内容 {i+1}",
            )
            await mistake_service.create_mistake(user_id, request)

        # 查询列表
        result = await mistake_service.get_mistake_list(
            user_id=user_id, page=1, page_size=10
        )

        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_get_statistics(self, mistake_service):
        """测试获取统计"""
        user_id = uuid4()

        # 创建一些错题
        for i in range(5):
            request = CreateMistakeRequest(
                title=f"错题 {i+1}",
                subject="math" if i % 2 == 0 else "english",
                question_content=f"题目内容 {i+1}",
            )
            await mistake_service.create_mistake(user_id, request)

        # 获取统计
        stats = await mistake_service.get_statistics(user_id)

        assert stats.total_mistakes == 5
        assert stats.not_mastered >= 0
        assert "math" in stats.by_subject or "english" in stats.by_subject


if __name__ == "__main__":
    """直接运行测试"""
    pytest.main([__file__, "-v", "-s"])

