#!/usr/bin/env python3
"""
检查并修复 user_knowledge_graph_snapshots 表结构
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


async def check_and_fix_table():
    """检查并修复表结构"""
    logger.info("🔍 检查 user_knowledge_graph_snapshots 表结构...")

    # 创建数据库连接
    engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI), echo=False, pool_pre_ping=True
    )

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as db:
            # 检查字段是否存在
            check_sql = text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'user_knowledge_graph_snapshots'
                ORDER BY ordinal_position;
            """
            )

            result = await db.execute(check_sql)
            columns = result.fetchall()

            logger.info(f"\n当前表结构 ({len(columns)} 个字段):")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}")

            # 检查是否缺少必要字段
            column_names = [col[0] for col in columns]

            missing_fields = []
            if "period_type" not in column_names:
                missing_fields.append("period_type")
            if "graph_data" not in column_names:
                missing_fields.append("graph_data")

            if missing_fields:
                logger.warning(f"⚠️  缺少字段: {', '.join(missing_fields)}")
                logger.info("📝 添加缺失字段...")

                # 添加缺失字段
                if "period_type" in missing_fields:
                    alter_sql = text(
                        """
                        ALTER TABLE user_knowledge_graph_snapshots
                        ADD COLUMN IF NOT EXISTS period_type VARCHAR(20) DEFAULT 'manual';
                    """
                    )
                    await db.execute(alter_sql)
                    logger.info("  ✓ 添加 period_type 字段")

                if "graph_data" in missing_fields:
                    alter_sql = text(
                        """
                        ALTER TABLE user_knowledge_graph_snapshots
                        ADD COLUMN IF NOT EXISTS graph_data JSONB;
                    """
                    )
                    await db.execute(alter_sql)
                    logger.info("  ✓ 添加 graph_data 字段")

                await db.commit()
                logger.info("✅ 字段添加成功")

                # 再次检查
                result = await db.execute(check_sql)
                columns = result.fetchall()

                logger.info(f"\n修复后表结构 ({len(columns)} 个字段):")
                for col in columns:
                    logger.info(f"  - {col[0]}: {col[1]}")

            else:
                logger.info("✅ 表结构完整，无需修复")

    except Exception as e:
        logger.error(f"❌ 检查失败: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


def main():
    """主函数"""
    try:
        asyncio.run(check_and_fix_table())
        logger.info("\n✅ 表结构检查完成！")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 检查失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
