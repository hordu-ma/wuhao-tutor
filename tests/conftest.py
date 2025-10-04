"""
测试配置文件
提供测试数据库、会话和通用测试工具
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境
os.environ["ENVIRONMENT"] = "testing"

from src.api.dependencies.auth import get_current_user, get_current_user_id
from src.core.config import get_settings
from src.core.database import Base, get_db
from src.main import app
from src.models.user import User

settings = get_settings()

# 创建测试数据库引擎
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:", echo=False, future=True
)

# 创建测试会话工厂
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """测试数据库会话依赖重写"""
    async with TestingSessionLocal() as session:
        yield session


# Mock认证函数
def mock_get_current_user() -> User:
    """测试Mock当前用户"""
    mock_user = User(
        id="test_user_123",
        username="testuser",
        real_name="测试用户",
        phone="13800138000",
        email="test@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return mock_user


def mock_get_current_user_id() -> str:
    """测试Mock当前用户ID"""
    return "test_user_123"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_setup():
    """设置测试数据库"""
    # 先删除所有表，再重新创建
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 清理
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def test_client(test_db_setup) -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def test_homework_data():
    """测试作业数据"""
    return {
        "title": "数学练习题",
        "subject": "数学",
        "grade": "高一",
        "description": "这是一个测试作业",
        "template_id": 1,
    }
