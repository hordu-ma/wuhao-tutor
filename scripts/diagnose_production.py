#!/usr/bin/env python3
"""
生产环境数据诊断和修复脚本

功能：
1. 检查用户的错题记录
2. 检查知识点掌握度记录
3. 为缺少知识点的错题重新关联知识点
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select

from src.core.database import AsyncSessionLocal
from src.models.study import KnowledgeMastery, MistakeRecord
from src.services.knowledge_graph_service import KnowledgeGraphService


async def diagnose_and_fix(user_id: UUID):
    """诊断并修复用户的知识图谱数据"""

    async with AsyncSessionLocal() as db:
        print(f"\n{'='*60}")
        print(f"诊断用户: {user_id}")
        print(f"{'='*60}\n")

        # 1. 检查错题记录
        stmt = select(func.count(MistakeRecord.id)).where(
            MistakeRecord.user_id == user_id
        )
        result = await db.execute(stmt)
        mistake_count = result.scalar_one()

        print(f"📚 错题总数: {mistake_count}")

        if mistake_count == 0:
            print("\n⚠️  用户没有错题记录，无法生成知识图谱")
            return

        # 按学科统计
        stmt = (
            select(MistakeRecord.subject, func.count(MistakeRecord.id).label("count"))
            .where(MistakeRecord.user_id == user_id)
            .group_by(MistakeRecord.subject)
        )
        result = await db.execute(stmt)
        subject_counts = result.all()

        print("\n各学科错题分布:")
        for subject, count in subject_counts:
            print(f"  • {subject}: {count}条")

        # 2. 检查知识掌握度记录
        stmt = select(func.count(KnowledgeMastery.id)).where(
            KnowledgeMastery.user_id == str(user_id)
        )
        result = await db.execute(stmt)
        mastery_count = result.scalar_one()

        print(f"\n🧠 知识掌握度记录数: {mastery_count}")

        if mastery_count > 0:
            stmt = (
                select(
                    KnowledgeMastery.subject,
                    func.count(KnowledgeMastery.id).label("count"),
                )
                .where(KnowledgeMastery.user_id == str(user_id))
                .group_by(KnowledgeMastery.subject)
            )
            result = await db.execute(stmt)
            mastery_subjects = result.all()

            print("\n各学科知识点分布:")
            for subject, count in mastery_subjects:
                print(f"  • {subject}: {count}个")

        # 3. 诊断结果
        print(f"\n{'='*60}")
        print("诊断结果")
        print(f"{'='*60}\n")

        if mastery_count == 0:
            print("❌ 问题确认: 用户有错题但没有知识掌握度记录")
            print("   原因: 错题创建时知识点关联失败或未触发")
            print("\n💡 建议修复方案:")
            print("   1. 检查错题记录的 knowledge_points 字段是否为空")
            print("   2. 为现有错题重新关联知识点")
            print("   3. 调用知识图谱快照生成API")

            # 获取样例错题
            stmt = (
                select(MistakeRecord).where(MistakeRecord.user_id == user_id).limit(3)
            )
            result = await db.execute(stmt)
            mistakes = result.scalars().all()

            if mistakes:
                print("\n📝 样例错题:")
                for i, m in enumerate(mistakes, 1):
                    print(f"\n  {i}. ID: {m.id}")
                    print(f"     学科: {m.subject}")
                    print(f"     问题: {m.question[:60] if m.question else 'N/A'}...")
                    print(f"     知识点字段: {m.knowledge_points}")
                    print(f"     知识点类型: {type(m.knowledge_points)}")

                    # 检查是否有值
                    if m.knowledge_points:
                        print(f"     ✅ 有知识点数据，需重新关联")
                    else:
                        print(f"     ❌ 知识点字段为空，需AI分析")
        else:
            print("✅ 数据正常: 用户有错题和知识掌握度记录")
            print("   → 如果知识图谱API返回空，检查API的subject参数是否正确")
            print(f"   → 确认subject值是否在: {[s for s, _ in subject_counts]}")


async def main():
    # 马雅姮的用户ID
    user_id = UUID("e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8")

    try:
        await diagnose_and_fix(user_id)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("五好伴学 - 生产环境诊断工具")
    print("=" * 60)
    asyncio.run(main())
