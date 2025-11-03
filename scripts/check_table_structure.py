"""检查数据库表结构"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

env_file = Path(__file__).parent.parent / ".env.production"
if not env_file.exists():
    env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")


async def check_table():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='knowledge_point_learning_tracks' 
            ORDER BY ordinal_position
        """
            )
        )

        print("knowledge_point_learning_tracks 表结构：")
        print("-" * 60)
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"  {row[0]:<30} {row[1]:<20} {nullable}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_table())
