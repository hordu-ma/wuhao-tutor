#!/usr/bin/env python3
"""
PostgreSQL数据库初始化和连接测试脚本
用于生产环境数据库的初始化和验证
"""

import asyncio
import sys
import os
from typing import Optional
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from alembic import command
from alembic.config import Config

from src.core.config import get_settings
from src.core.database import Base
from src.models import *  # 导入所有模型

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""

    def __init__(self, environment: str = "production"):
        """
        初始化数据库连接器

        Args:
            environment: 环境名称 (development, testing, production)
        """
        # 设置环境变量
        os.environ["ENVIRONMENT"] = environment
        self.settings = get_settings()
        self.environment = environment

        logger.info(f"初始化数据库环境: {environment}")
        logger.info(f"数据库配置: {self.settings.POSTGRES_SERVER}:{self.settings.POSTGRES_PORT}/{self.settings.POSTGRES_DB}")

    async def check_postgresql_connection(self) -> bool:
        """检查PostgreSQL服务器连接"""
        try:
            # 连接到默认的postgres数据库
            conn = await asyncpg.connect(
                user=self.settings.POSTGRES_USER,
                password=self.settings.POSTGRES_PASSWORD,
                database="postgres",
                host=self.settings.POSTGRES_SERVER,
                port=int(self.settings.POSTGRES_PORT)
            )
            await conn.close()
            logger.info("✅ PostgreSQL服务器连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL服务器连接失败: {e}")
            return False

    async def create_database_if_not_exists(self) -> bool:
        """创建数据库（如果不存在）"""
        try:
            # 连接到默认的postgres数据库
            conn = await asyncpg.connect(
                user=self.settings.POSTGRES_USER,
                password=self.settings.POSTGRES_PASSWORD,
                database="postgres",
                host=self.settings.POSTGRES_SERVER,
                port=int(self.settings.POSTGRES_PORT)
            )

            # 检查数据库是否存在
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.settings.POSTGRES_DB
            )

            if not db_exists:
                # 创建数据库
                await conn.execute(f'CREATE DATABASE "{self.settings.POSTGRES_DB}"')
                logger.info(f"✅ 数据库 '{self.settings.POSTGRES_DB}' 创建成功")
            else:
                logger.info(f"ℹ️  数据库 '{self.settings.POSTGRES_DB}' 已存在")

            await conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False

    async def test_database_connection(self) -> bool:
        """测试应用数据库连接"""
        try:
            engine = create_async_engine(
                str(self.settings.SQLALCHEMY_DATABASE_URI),
                echo=False
            )

            async with engine.begin() as conn:
                result = await conn.execute(sa.text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ 应用数据库连接成功")
                logger.info(f"PostgreSQL版本: {version}")

            await engine.dispose()
            return True

        except Exception as e:
            logger.error(f"❌ 应用数据库连接失败: {e}")
            return False

    def run_alembic_migrations(self) -> bool:
        """运行Alembic数据库迁移"""
        try:
            # 配置Alembic
            alembic_cfg = Config(str(project_root / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

            # 设置数据库URL（移除异步驱动前缀）
            db_url = str(self.settings.SQLALCHEMY_DATABASE_URI).replace("+asyncpg", "")
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)

            # 运行迁移
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Alembic数据库迁移完成")
            return True

        except Exception as e:
            logger.error(f"❌ Alembic迁移失败: {e}")
            return False

    async def verify_tables_created(self) -> bool:
        """验证数据库表是否正确创建"""
        try:
            engine = create_async_engine(
                str(self.settings.SQLALCHEMY_DATABASE_URI),
                echo=False
            )

            async with engine.begin() as conn:
                # 检查主要表是否存在
                expected_tables = [
                    'users', 'user_sessions', 'homework',
                    'homework_submissions', 'homework_images', 'homework_reviews'
                ]

                for table_name in expected_tables:
                    result = await conn.execute(
                        sa.text(
                            "SELECT EXISTS (SELECT FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_name = :table_name)"
                        ),
                        {"table_name": table_name}
                    )
                    exists = result.scalar()
                    if exists:
                        logger.info(f"✅ 表 '{table_name}' 存在")
                    else:
                        logger.error(f"❌ 表 '{table_name}' 不存在")
                        await engine.dispose()
                        return False

            await engine.dispose()
            logger.info("✅ 所有数据库表验证通过")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库表验证失败: {e}")
            return False

    async def create_initial_data(self) -> bool:
        """创建初始数据（如果需要）"""
        try:
            engine = create_async_engine(
                str(self.settings.SQLALCHEMY_DATABASE_URI),
                echo=False
            )

            AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
                class_=AsyncSession,
            )

            async with AsyncSessionLocal() as session:
                # 检查是否已有用户数据
                result = await session.execute(sa.text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()

                if user_count == 0:
                    logger.info("🔄 创建初始测试数据...")
                    # 这里可以添加初始数据创建逻辑
                    # 目前保持空白，后续可以根据需要添加
                else:
                    logger.info(f"ℹ️  数据库中已有 {user_count} 个用户")

                await session.commit()

            await engine.dispose()
            logger.info("✅ 初始数据检查完成")
            return True

        except Exception as e:
            logger.error(f"❌ 创建初始数据失败: {e}")
            return False

    async def run_full_initialization(self) -> bool:
        """运行完整的数据库初始化流程"""
        logger.info("🚀 开始数据库初始化流程...")

        steps = [
            ("检查PostgreSQL连接", self.check_postgresql_connection()),
            ("创建数据库", self.create_database_if_not_exists()),
            ("测试应用数据库连接", self.test_database_connection()),
            ("运行Alembic迁移", self.run_alembic_migrations),
            ("验证表结构", self.verify_tables_created()),
            ("创建初始数据", self.create_initial_data()),
        ]

        for step_name, step_func in steps:
            logger.info(f"🔄 执行步骤: {step_name}")

            if asyncio.iscoroutinefunction(step_func):
                success = await step_func
            else:
                success = step_func()

            if not success:
                logger.error(f"💥 步骤失败: {step_name}")
                return False

        logger.info("🎉 数据库初始化完成!")
        return True


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL数据库初始化脚本")
    parser.add_argument(
        "--env",
        choices=["development", "testing", "production"],
        default="production",
        help="环境名称 (默认: production)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查连接，不执行初始化"
    )

    args = parser.parse_args()

    # 创建初始化器
    initializer = DatabaseInitializer(args.env)

    if args.check_only:
        # 仅检查连接
        logger.info("🔍 仅执行连接检查...")
        pg_ok = await initializer.check_postgresql_connection()
        db_ok = await initializer.test_database_connection()

        if pg_ok and db_ok:
            logger.info("✅ 数据库连接检查通过")
            sys.exit(0)
        else:
            logger.error("❌ 数据库连接检查失败")
            sys.exit(1)
    else:
        # 完整初始化
        success = await initializer.run_full_initialization()

        if success:
            logger.info("🎉 数据库初始化成功!")
            sys.exit(0)
        else:
            logger.error("💥 数据库初始化失败!")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
