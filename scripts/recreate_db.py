#!/usr/bin/env python3
"""
重新创建数据库表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import Base, engine

# 导入所有模型以注册到Base.metadata - 使用通配符导入确保所有模型都被注册
from src.models import *  # noqa: F403, F401


async def main():
    """重新创建所有表"""
    print("🗑️  删除所有旧表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("✨ 创建新表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功！")


if __name__ == "__main__":
    asyncio.run(main())
