"""
测试错题仓储层
测试 MistakeRepository 的数据访问方法

作者: AI Agent
创建时间: 2025-10-12
版本: v1.0
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.study import MistakeRecord
from src.repositories.mistake_repository import MistakeRepository


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    # 使用内存SQLite数据库
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # 清理
    await engine.dispose()


@pytest.fixture
async def mistake_repo(db_session):
    """创建错题仓储实例"""
    return MistakeRepository(MistakeRecord, db_session)


@pytest.fixture
async def sample_mistakes(mistake_repo):
    """创建示例错题数据"""
    user_id = str(uuid4())
    mistakes = []

    # 创建不同状态的错题
    for i in range(5):
        data = {
            "user_id": user_id,
            "subject": "math" if i % 2 == 0 else "english",
            "title": f"错题 {i + 1}",
            "ocr_text": f"题目内容 {i + 1}",
            "difficulty_level": (i % 3) + 1,
            "mastery_status": ["learning", "reviewing", "mastered"][i % 3],
            "review_count": i,
            "correct_count": i // 2,
            "next_review_at": datetime.now() + timedelta(days=i),
            "knowledge_points": [f"知识点{i}", f"知识点{i + 1}"],
        }
        mistake = await mistake_repo.create(data)
        mistakes.append(mistake)

    return user_id, mistakes


class TestMistakeRepository:
    """测试错题仓储"""

    @pytest.mark.asyncio
    async def test_find_by_user_basic(self, mistake_repo, sample_mistakes):
        """测试基本用户查询"""
        user_id, _ = sample_mistakes

        items, total = await mistake_repo.find_by_user(
            user_id=user_id, page=1, page_size=10
        )

        assert total == 5
        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_find_by_user_with_subject_filter(
        self, mistake_repo, sample_mistakes
    ):
        """测试学科筛选"""
        user_id, _ = sample_mistakes

        items, total = await mistake_repo.find_by_user(
            user_id=user_id, subject="math", page=1, page_size=10
        )

        assert total == 3  # math: 0, 2, 4
        assert all(item.subject == "math" for item in items)

    @pytest.mark.asyncio
    async def test_find_due_for_review(self, mistake_repo, sample_mistakes):
        """测试查询待复习错题"""
        user_id, mistakes = sample_mistakes

        # 更新一些错题为今天需要复习
        for i in [0, 1, 2]:
            await mistake_repo.update(
                str(mistakes[i].id),
                {
                    "next_review_at": datetime.now() - timedelta(hours=1),
                    "mastery_status": "reviewing",
                },
            )

        due_mistakes = await mistake_repo.find_due_for_review(user_id=user_id, limit=10)

        assert len(due_mistakes) == 3

    @pytest.mark.asyncio
    async def test_get_statistics(self, mistake_repo, sample_mistakes):
        """测试统计数据"""
        user_id, _ = sample_mistakes

        stats = await mistake_repo.get_statistics(user_id=user_id)

        assert stats["total"] == 5
        assert stats["learning"] >= 0
        assert stats["reviewing"] >= 0
        assert stats["mastered"] >= 0
        assert "math" in stats["by_subject"]
        assert "english" in stats["by_subject"]
