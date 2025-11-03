"""
快速诊断知识点数据 - 使用FastAPI运行时环境
直接通过API调用诊断生产数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 强制加载生产环境配置
import os

from dotenv import load_dotenv

# 加载.env.production文件
env_path = Path(__file__).parent.parent / ".env.production"
print(f"📁 加载配置文件: {env_path}")
load_dotenv(env_path, override=True)

from sqlalchemy import text

from src.core.database import get_db


async def quick_diagnose():
    """快速诊断"""
    print("=" * 70)
    print("🔍 知识点关联数据快速诊断")
    print("=" * 70)

    async for db in get_db():
        try:
            # 1. 基础统计
            print("\n📊 数据统计:")

            # 错题总数
            result = await db.execute(text("SELECT COUNT(*) FROM mistakes"))
            mistake_count = result.scalar()
            print(f"   错题总数: {mistake_count}")

            # 知识点关联数
            result = await db.execute(
                text("SELECT COUNT(*) FROM mistake_knowledge_points")
            )
            mkp_count = result.scalar()
            print(f"   知识点关联数: {mkp_count}")

            # 知识点掌握度记录数
            result = await db.execute(text("SELECT COUNT(*) FROM knowledge_mastery"))
            km_count = result.scalar()
            print(f"   知识点掌握度记录数: {km_count}")

            # 2. 关联覆盖率
            print("\n📈 关联覆盖率:")

            result = await db.execute(
                text(
                    """
                SELECT 
                    COUNT(DISTINCT m.id) as total,
                    COUNT(DISTINCT CASE WHEN mkp.id IS NOT NULL THEN m.id END) as with_kp
                FROM mistakes m
                LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
            """
                )
            )
            row = result.fetchone()
            total, with_kp = row[0], row[1]
            coverage = (with_kp / total * 100) if total > 0 else 0
            print(f"   有关联的错题: {with_kp}/{total} ({coverage:.1f}%)")
            print(f"   无关联的错题: {total - with_kp}")

            # 3. 按学科统计
            print("\n📚 按学科统计:")
            result = await db.execute(
                text(
                    """
                SELECT 
                    m.subject,
                    COUNT(DISTINCT m.id) as total_mistakes,
                    COUNT(DISTINCT CASE WHEN mkp.id IS NOT NULL THEN m.id END) as with_kp
                FROM mistakes m
                LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
                GROUP BY m.subject
                ORDER BY total_mistakes DESC
            """
                )
            )
            rows = result.fetchall()
            for subject, total, with_kp in rows:
                coverage = (with_kp / total * 100) if total > 0 else 0
                print(f"   {subject}: {with_kp}/{total} ({coverage:.1f}%)")

            # 4. 示例：没有知识点关联的错题
            if total - with_kp > 0:
                print(f"\n❌ 没有知识点关联的错题示例 (前5个):")
                result = await db.execute(
                    text(
                        """
                    SELECT 
                        m.id, 
                        m.subject, 
                        m.title,
                        LEFT(m.ocr_text, 50) as content_preview
                    FROM mistakes m
                    LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
                    WHERE mkp.id IS NULL
                    ORDER BY m.created_at DESC
                    LIMIT 5
                """
                    )
                )
                rows = result.fetchall()
                for i, (mid, subject, title, preview) in enumerate(rows, 1):
                    print(f"   {i}. ID: {mid}")
                    print(f"      学科: {subject}, 标题: {title or '无标题'}")
                    print(f"      内容: {preview or '无内容'}...")

            print("\n" + "=" * 70)

        finally:
            await db.close()
            break  # 只取第一个session


if __name__ == "__main__":
    asyncio.run(quick_diagnose())
