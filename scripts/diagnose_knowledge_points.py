"""
诊断知识点关联数据情况

直接连接生产数据库，检查：
1. 错题总数
2. 知识点关联数
3. 知识点掌握度记录数
4. 示例数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 生产数据库连接
DATABASE_URL = "postgresql+asyncpg://postgres:lkj1006@pgm-bp1ce0sp88j6ha90.pg.rds.aliyuncs.com:5432/wuhao_tutor"


async def diagnose():
    """诊断知识点数据情况"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 70)
    print("🔍 知识点关联数据诊断报告")
    print("=" * 70)

    async with async_session() as session:
        # 1. 基础统计
        print("\n📊 数据统计:")

        # 错题总数
        result = await session.execute(text("SELECT COUNT(*) FROM mistakes"))
        mistake_count = result.scalar()
        print(f"   错题总数: {mistake_count}")

        # 知识点关联数
        result = await session.execute(
            text("SELECT COUNT(*) FROM mistake_knowledge_points")
        )
        mkp_count = result.scalar()
        print(f"   知识点关联数: {mkp_count}")

        # 知识点掌握度记录数
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_mastery"))
        km_count = result.scalar()
        print(f"   知识点掌握度记录数: {km_count}")

        # 2. 关联覆盖率
        print("\n📈 关联覆盖率:")

        result = await session.execute(
            text(
                """
            SELECT 
                COUNT(DISTINCT m.id) as total,
                COUNT(DISTINCT mkp.mistake_id) as with_kp
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

        # 3. 示例：有知识点关联的错题
        if mkp_count > 0:
            print("\n✅ 有知识点关联的错题示例 (前3个):")
            result = await session.execute(
                text(
                    """
                SELECT 
                    m.id, 
                    m.subject, 
                    m.title,
                    COUNT(mkp.id) as kp_count
                FROM mistakes m
                INNER JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
                GROUP BY m.id, m.subject, m.title
                ORDER BY m.created_at DESC
                LIMIT 3
            """
                )
            )
            rows = result.fetchall()
            for i, (mid, subject, title, kp_count) in enumerate(rows, 1):
                print(f"   {i}. ID: {mid}")
                print(f"      学科: {subject}, 标题: {title or '无标题'}")
                print(f"      关联知识点数: {kp_count}")

                # 查询具体关联的知识点
                kp_result = await session.execute(
                    text(
                        """
                    SELECT 
                        km.knowledge_point,
                        mkp.is_primary,
                        mkp.relevance_score,
                        km.mastery_level
                    FROM mistake_knowledge_points mkp
                    INNER JOIN knowledge_mastery km ON mkp.knowledge_point_id = km.id
                    WHERE mkp.mistake_id = :mistake_id
                    ORDER BY mkp.is_primary DESC, mkp.relevance_score DESC
                """
                    ),
                    {"mistake_id": mid},
                )
                kp_rows = kp_result.fetchall()
                for kp_name, is_primary, score, mastery in kp_rows:
                    primary_mark = "⭐" if is_primary else "  "
                    mastery_color = (
                        "🟢" if mastery >= 0.7 else "🟡" if mastery >= 0.4 else "🔴"
                    )
                    print(
                        f"         {primary_mark} {mastery_color} {kp_name} (关联度: {score:.2f}, 掌握度: {mastery:.2f})"
                    )

        # 4. 示例：没有知识点关联的错题
        if total - with_kp > 0:
            print(f"\n❌ 没有知识点关联的错题示例 (前5个):")
            result = await session.execute(
                text(
                    """
                SELECT 
                    m.id, 
                    m.subject, 
                    m.title,
                    SUBSTRING(m.ocr_text, 1, 50) as content_preview,
                    m.created_at
                FROM mistakes m
                LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
                WHERE mkp.id IS NULL
                ORDER BY m.created_at DESC
                LIMIT 5
            """
                )
            )
            rows = result.fetchall()
            for i, (mid, subject, title, preview, created_at) in enumerate(rows, 1):
                print(f"   {i}. ID: {mid}")
                print(f"      学科: {subject}, 标题: {title or '无标题'}")
                print(f"      内容预览: {preview or '无内容'}...")
                print(f"      创建时间: {created_at}")

        # 5. 按学科统计
        print("\n📚 按学科统计:")
        result = await session.execute(
            text(
                """
            SELECT 
                m.subject,
                COUNT(DISTINCT m.id) as total_mistakes,
                COUNT(DISTINCT mkp.mistake_id) as with_kp
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

    print("\n" + "=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(diagnose())
