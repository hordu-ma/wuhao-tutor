#!/usr/bin/env python3
"""
修复知识点错题计数脚本

问题：KnowledgeMastery.mistake_count 字段未正确统计，导致筛选时返回空结果
解决：根据 MistakeKnowledgePoint 关联表重新计算每个知识点的错题数量

作者：五好伴学开发团队
日期：2025-11-04
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from src.core.database import AsyncSessionLocal
from src.models.knowledge_graph import MistakeKnowledgePoint
from src.models.study import KnowledgeMastery


async def fix_mistake_count():
    """
    重新计算并更新每个知识点的错题数量
    """
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("📊 修复知识点错题计数")
        print("=" * 60)

        # 1. 查询所有 KnowledgeMastery 记录
        stmt = select(KnowledgeMastery)
        result = await session.execute(stmt)
        all_km = result.scalars().all()

        print(f"\n找到 {len(all_km)} 条知识点掌握度记录")
        print("\n开始重新计算错题数量...\n")

        updated_count = 0

        for km in all_km:
            # 2. 统计该知识点的关联错题数
            count_stmt = select(func.count(MistakeKnowledgePoint.id)).where(
                MistakeKnowledgePoint.knowledge_point_id == str(km.id)
            )
            count_result = await session.execute(count_stmt)
            actual_count = count_result.scalar() or 0

            # 3. 如果计数不一致，更新记录
            if km.mistake_count != actual_count:
                old_count = km.mistake_count
                km.mistake_count = actual_count
                updated_count += 1

                print(f"  ✅ {km.knowledge_point}: {old_count} -> {actual_count}")
            else:
                print(f"  ⏭️  {km.knowledge_point}: {actual_count} (无需更新)")

        # 4. 提交事务
        if updated_count > 0:
            await session.commit()
            print(f"\n✅ 成功更新 {updated_count} 条记录")
        else:
            print(f"\n✅ 所有记录的错题计数已正确，无需更新")

        print("\n" + "=" * 60)
        print("修复完成!")
        print("=" * 60)


async def verify_fixes():
    """验证修复结果"""
    async with AsyncSessionLocal() as session:
        print("\n" + "=" * 60)
        print("📊 验证修复结果")
        print("=" * 60)

        # 按科目统计
        stmt = select(
            KnowledgeMastery.subject,
            func.count(KnowledgeMastery.id).label("total"),
            func.sum(KnowledgeMastery.mistake_count).label("total_mistakes"),
        ).group_by(KnowledgeMastery.subject)

        result = await session.execute(stmt)
        rows = result.all()

        print("\n科目统计:")
        for subject, total, total_mistakes in rows:
            print(f"  {subject}: {total} 个知识点, 共 {total_mistakes or 0} 个错题关联")

        # 显示有错题的知识点
        print("\n有错题的知识点 (mistake_count > 0):")
        stmt2 = (
            select(
                KnowledgeMastery.subject,
                KnowledgeMastery.knowledge_point,
                KnowledgeMastery.mistake_count,
            )
            .where(KnowledgeMastery.mistake_count > 0)
            .order_by(KnowledgeMastery.mistake_count.desc())
        )

        result2 = await session.execute(stmt2)
        rows2 = result2.all()

        if rows2:
            for subject, kp, count in rows2:
                print(f"  {subject} - {kp}: {count} 个错题")
        else:
            print("  (无)")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n⚙️  开始修复知识点错题计数...\n")

    # 运行修复
    asyncio.run(fix_mistake_count())

    # 验证结果
    asyncio.run(verify_fixes())

    print("\n✨ 全部完成！\n")
