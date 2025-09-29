"""
数据库配置和会话管理模块
使用 SQLAlchemy 2.0+ 异步支持
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# 创建异步引擎
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.DEBUG,  # 在开发模式下打印SQL语句
    pool_pre_ping=True,
    pool_recycle=300,  # 5分钟回收连接
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 防止在异步环境中访问已提交对象时出现问题
)

# 别名，为了兼容性
async_session = AsyncSessionLocal

# 创建声明性基类
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    异步数据库会话依赖注入
    用于FastAPI的依赖注入系统
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库表
    仅用于开发环境，生产环境使用Alembic迁移
    """
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册到Base.metadata
        from src.models import user, study, knowledge, homework, learning  # noqa

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接
    """
    await engine.dispose()


# FastAPI依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入
    用于FastAPI路由的依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
