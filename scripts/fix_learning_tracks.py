"""
修复已有错题的学习轨迹记录

为已经创建了知识点关联但缺少学习轨迹的错题补充学习轨迹数据
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

env_file = Path(__file__).parent.parent / ".env.production"
if not env_file.exists():
    env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")


async def fix_learning_tracks():
    """为已有知识点关联但缺少学习轨迹的记录补充数据"""
    from src.services.bailian_service import BailianService
    from src.services.knowledge_graph_service import KnowledgeGraphService

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("🔧 修复学习轨迹记录工具")
    print("=" * 60)

    async with async_session() as session:
        # 查询所有有知识点关联但没有学习轨迹的记录
        query = text(
            """
            SELECT DISTINCT
                mkp.mistake_id,
                mkp.id as association_id,
                m.user_id,
                mkp.knowledge_point_id
            FROM mistake_knowledge_points mkp
            INNER JOIN mistake_records m ON mkp.mistake_id = m.id
            LEFT JOIN knowledge_point_learning_tracks kplt 
                ON kplt.mistake_id = mkp.mistake_id 
                AND kplt.knowledge_point_id = mkp.knowledge_point_id
            WHERE kplt.id IS NULL
        """
        )

        result = await session.execute(query)
        missing_tracks = result.fetchall()

        total = len(missing_tracks)
        print(f"📋 找到 {total} 条需要补充学习轨迹的关联\n")

        if total == 0:
            print("✅ 所有关联都已有学习轨迹记录")
            return

        # 初始化服务
        bailian_service = BailianService()
        kg_service = KnowledgeGraphService(session, bailian_service)

        success_count = 0
        error_count = 0

        for i, (mistake_id, assoc_id, user_id, kp_id) in enumerate(missing_tracks, 1):
            print(f"[{i}/{total}] 处理错题 {mistake_id}")
            print(f"   知识点ID: {kp_id}")

            try:
                # 创建学习轨迹记录
                track_data = {
                    "user_id": UUID(str(user_id)),
                    "knowledge_point_id": UUID(str(kp_id)),
                    "mistake_id": UUID(str(mistake_id)),
                    "activity_type": "mistake_creation",
                    "result": "incorrect",
                }

                await kg_service.track_repo.record_activity(track_data)
                await session.commit()

                print(f"   ✅ 成功")
                success_count += 1

            except Exception as e:
                await session.rollback()
                print(f"   ❌ 失败: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print("📊 处理完成:")
        print(f"   成功: {success_count}")
        print(f"   失败: {error_count}")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_learning_tracks())
