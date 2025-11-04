#!/usr/bin/env python3
"""
修复知识点科目数据脚本（简化版）

问题：历史数据中部分知识点的科目字段为"其他"，导致按科目筛选失败
解决：直接将科目="其他"的记录批量更新为"数学"（K12最常见科目）

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
from src.models.study import KnowledgeMastery


async def fix_knowledge_point_subjects():
    """
    修复知识点科目数据（简化版）

    直接将所有科目为"其他"的记录更新为"数学"
    """
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("📚 修复知识点科目数据")
        print("=" * 60)

        # 1. 查询科目为"其他"的记录数
        count_stmt = select(KnowledgeMastery).where(KnowledgeMastery.subject == "其他")
        result = await session.execute(count_stmt)
        wrong_subject_records = result.scalars().all()

        count = len(wrong_subject_records)
        print(f"\n发现 {count} 条科目为'其他'的记录")

        if count == 0:
            print("✅ 无需修复！")
            return

        # 2. 批量更新为"数学"
        print(f"\n开始批量更新...")

        for record in wrong_subject_records:
            record.subject = "数学"
            print(f"  • {record.knowledge_point} -> 数学")

        # 提交事务
        await session.commit()

        print(f"\n✅ 成功更新 {count} 条记录")
        print("\n" + "=" * 60)
        print("修复完成!")
        print("=" * 60)


async def verify_fixes():
    """验证修复结果"""
    async with AsyncSessionLocal() as session:
        print("\n" + "=" * 60)
        print("📊 验证修复结果")
        print("=" * 60)

        # 统计各科目的知识点数量
        stmt = select(
            KnowledgeMastery.subject, func.count(KnowledgeMastery.id).label("count")
        ).group_by(KnowledgeMastery.subject)

        result = await session.execute(stmt)
        rows = result.all()

        print("\n科目分布:")
        for subject, count in rows:
            print(f"  {subject}: {count} 个知识点")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n⚙️  开始修复知识点科目数据...\n")

    # 运行修复
    asyncio.run(fix_knowledge_point_subjects())

    # 验证结果
    asyncio.run(verify_fixes())

    print("\n✨ 全部完成！\n")
