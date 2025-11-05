"""修复数据库中的中文年级数据"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["ENVIRONMENT"] = "production"

from dotenv import load_dotenv

# 加载生产环境配置
env_path = Path(__file__).parent.parent / ".env.production"
load_dotenv(env_path)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.models.user import User

# 中文到英文的映射
GRADE_MAPPING = {
    "一年级": "primary_1",
    "二年级": "primary_2",
    "三年级": "primary_3",
    "四年级": "primary_4",
    "五年级": "primary_5",
    "六年级": "primary_6",
    "七年级": "junior_1",
    "八年级": "junior_2",
    "九年级": "junior_3",
    "高一": "senior_1",
    "高二": "senior_2",
    "高三": "senior_3",
}


async def fix_grades():
    settings = get_settings()
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 查找所有使用中文年级的用户
        result = await session.execute(
            select(User).where(User.grade_level.in_(list(GRADE_MAPPING.keys())))
        )
        users = result.scalars().all()

        if not users:
            print("✅ 没有需要修复的年级数据")
            return

        print(f"📋 找到 {len(users)} 个需要修复的用户:")
        fixed_count = 0

        for user in users:
            old_grade = user.grade_level
            new_grade = GRADE_MAPPING.get(old_grade)

            if new_grade:
                user.grade_level = new_grade
                print(f"  - {user.name} ({user.phone}): {old_grade} → {new_grade}")
                fixed_count += 1

        await session.commit()
        print(f"\n✅ 成功修复 {fixed_count} 个用户的年级数据")


if __name__ == "__main__":
    asyncio.run(fix_grades())
