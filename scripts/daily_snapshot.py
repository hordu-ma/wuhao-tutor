#!/usr/bin/env python3
"""
每日知识图谱快照任务
每天凌晨3点执行，为所有用户生成知识图谱快照

作者: AI Agent
创建时间: 2025-11-03
版本: v1.0
"""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.logging import get_logger
from src.models.study import KnowledgeMastery
from src.services.bailian_service import BailianService
from src.services.knowledge_graph_service import KnowledgeGraphService

logger = get_logger(__name__)


async def create_daily_snapshots():
    """为所有用户创建每日知识图谱快照"""
    logger.info("🚀 开始执行每日知识图谱快照任务...")

    # 创建数据库连接
    engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        echo=False,
        pool_pre_ping=True,
    )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session() as db:
            # 初始化服务
            bailian_service = BailianService()
            kg_service = KnowledgeGraphService(db, bailian_service)

            # 获取所有需要生成快照的用户
            stmt = select(KnowledgeMastery.user_id).distinct()
            result = await db.execute(stmt)
            user_ids = result.scalars().all()

            logger.info(f"📊 发现 {len(user_ids)} 个用户需要生成快照")

            # 为每个用户生成快照
            success_count = 0
            failed_count = 0

            for user_id in user_ids:
                # 获取该用户的所有学科
                subject_stmt = (
                    select(KnowledgeMastery.subject)
                    .where(KnowledgeMastery.user_id == str(user_id))
                    .distinct()
                )
                subject_result = await db.execute(subject_stmt)
                subjects = subject_result.scalars().all()

                logger.info(f"👤 用户 {user_id} 有 {len(subjects)} 个学科: {subjects}")

                # 为每个学科创建快照
                for subject in subjects:
                    try:
                        snapshot = await kg_service.create_knowledge_graph_snapshot(
                            user_id=UUID(str(user_id)),
                            subject=subject,
                            period_type="daily",
                        )
                        logger.info(
                            f"✅ 成功为用户 {user_id} 创建 {subject} 学科快照: {snapshot.id}"
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(
                            f"❌ 为用户 {user_id} 创建 {subject} 学科快照失败: {e}",
                            exc_info=True,
                        )
                        failed_count += 1

            logger.info(f"📈 快照任务完成！成功: {success_count}, 失败: {failed_count}")

    except Exception as e:
        logger.error(f"❌ 每日快照任务执行失败: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


def main():
    """主函数"""
    # 使用模块级 logger

    try:
        asyncio.run(create_daily_snapshots())
        logger.info("✨ 每日快照任务执行成功！")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 每日快照任务执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
