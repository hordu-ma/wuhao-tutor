import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 加载环境配置（优先使用 ENVIRONMENT 指定的环境）
from dotenv import load_dotenv

environment = os.getenv("ENVIRONMENT", "development").lower()
if environment == "production":
    load_dotenv(".env.production", override=True)
elif environment == "testing":
    load_dotenv(".env.testing", override=True)
else:
    load_dotenv(".env", override=False)

# 导入数据库配置和模型
from src.core.config import get_settings
from src.core.database import Base
from src.models import *  # 导入所有模型以确保它们被注册到 Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        # 从配置文件获取数据库URL
        settings = get_settings()
        url = (
            str(settings.SQLALCHEMY_DATABASE_URI)
            .replace("+asyncpg", "")
            .replace("+aiosqlite", "")
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section, {})
    if "sqlalchemy.url" not in configuration:
        # 从配置文件获取数据库URL
        settings = get_settings()
        configuration["sqlalchemy.url"] = (
            str(settings.SQLALCHEMY_DATABASE_URI)
            .replace("+asyncpg", "")
            .replace("+aiosqlite", "")
        )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
