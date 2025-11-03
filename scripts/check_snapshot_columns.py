#!/usr/bin/env python3
"""检查user_knowledge_graph_snapshots表结构"""

import asyncio

import asyncpg


async def main():
    conn = await asyncpg.connect(
        "postgresql://wuhaoadmin:Wuhao2024Secure!@localhost/wuhao_tutor"
    )
    try:
        result = await conn.fetch(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_knowledge_graph_snapshots'
            ORDER BY ordinal_position
            """
        )
        print("\n当前表结构:")
        for row in result:
            print(f"  {row['column_name']}: {row['data_type']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
