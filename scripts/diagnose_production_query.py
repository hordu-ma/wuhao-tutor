#!/usr/bin/env python
"""
生产环境Repository查询诊断脚本
"""
import asyncio
import os
import sys
from uuid import UUID

# 添加项目路径
sys.path.insert(0, "/opt/wuhao-tutor")

# 强制使用生产环境配置
os.environ["ENVIRONMENT"] = "production"

from src.core.database import AsyncSessionLocal
from src.models.study import MistakeRecord
from src.repositories.mistake_repository import MistakeRepository


async def diagnose():
    async with AsyncSessionLocal() as db:
        repo = MistakeRepository(MistakeRecord, db)
        user_id = UUID("e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8")

        print("=" * 60)
        print("生产环境Repository查询诊断")
        print("=" * 60)

        # 测试1: 无筛选
        items1, total1 = await repo.find_by_user(user_id=user_id, page=1, page_size=50)
        print(f"\n测试1: 无筛选")
        print(f"  总数(count): {total1}")
        print(f"  返回记录: {len(items1)}")

        # 测试2: 筛选数学
        items2, total2 = await repo.find_by_user(
            user_id=user_id, subject="数学", page=1, page_size=50
        )
        print(f"\n测试2: 筛选数学")
        print(f"  总数(count): {total2}")
        print(f"  返回记录: {len(items2)}")

        # 统计source分布
        print(f"\n返回记录的source分布:")
        sources = {}
        for item in items2:
            sources[item.source] = sources.get(item.source, 0) + 1
        for source, count in sorted(sources.items()):
            print(f"  {source}: {count}条")

        # 打印前5条
        print(f"\n前5条记录:")
        for i, item in enumerate(items2[:5], 1):
            print(
                f"{i}. {item.title[:50]} | source={item.source} | subject={item.subject}"
            )

        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(diagnose())
