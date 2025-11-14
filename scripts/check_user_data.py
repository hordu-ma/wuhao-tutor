#!/usr/bin/env python3
"""检查用户数据 - 错题、知识点和知识图谱记录"""

import asyncio
import os
import sys
from uuid import UUID

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.study import KnowledgeMastery, MistakeRecord
from src.schemas.mistake import SubjectEnum


async def check_user_mistakes(user_id: UUID):
    """检查用户的错题记录"""
    async with AsyncSessionLocal() as db:
        # 统计各学科错题数量
        stmt = (
            select(MistakeRecord.subject, func.count(MistakeRecord.id).label("count"))
            .where(MistakeRecord.user_id == user_id)
            .group_by(MistakeRecord.subject)
        )
        result = await db.execute(stmt)
        subject_counts = result.all()

        print("\n=== 错题统计 ===")
        if subject_counts:
            for subject, count in subject_counts:
                print(f"  {subject}: {count}条")
        else:
            print("  未找到任何错题记录")

        # 获取前5条错题详情
        stmt = select(MistakeRecord).where(MistakeRecord.user_id == user_id).limit(5)
        result = await db.execute(stmt)
        mistakes = result.scalars().all()

        if mistakes:
            print("\n=== 前5条错题详情 ===")
            for i, mistake in enumerate(mistakes, 1):
                print(f"\n{i}. ID: {mistake.id}")
                print(f"   学科: {mistake.subject}")
                print(f"   问题: {mistake.question[:50]}...")
                print(
                    f"   知识点数量: {len(mistake.knowledge_points) if mistake.knowledge_points else 0}"
                )
                if mistake.knowledge_points:
                    print(f"   知识点: {mistake.knowledge_points[:3]}")

        return bool(mistakes)


async def check_knowledge_mastery(user_id: UUID):
    """检查知识掌握度记录"""
    async with AsyncSessionLocal() as db:
        # 统计各学科知识点数量
        stmt = (
            select(
                KnowledgeMastery.subject, func.count(KnowledgeMastery.id).label("count")
            )
            .where(KnowledgeMastery.user_id == user_id)
            .group_by(KnowledgeMastery.subject)
        )
        result = await db.execute(stmt)
        subject_counts = result.all()

        print("\n=== 知识掌握度记录统计 ===")
        if subject_counts:
            for subject, count in subject_counts:
                print(f"  {subject}: {count}个知识点")
        else:
            print("  未找到任何知识掌握度记录")

        # 获取前5条详情
        stmt = (
            select(KnowledgeMastery).where(KnowledgeMastery.user_id == user_id).limit(5)
        )
        result = await db.execute(stmt)
        masteries = result.scalars().all()

        if masteries:
            print("\n=== 前5条知识掌握度详情 ===")
            for i, mastery in enumerate(masteries, 1):
                print(f"\n{i}. ID: {mastery.id}")
                print(f"   学科: {mastery.subject}")
                print(f"   知识点: {mastery.knowledge_point_name}")
                print(f"   掌握度: {mastery.mastery_level:.2f}")
                print(f"   错误次数: {mastery.mistake_count}")
                print(f"   最后练习: {mastery.last_practiced}")

        return bool(masteries)


async def main():
    # 马雅姮的用户ID
    user_id = UUID("e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8")

    print(f"检查用户 {user_id} 的数据...")

    has_mistakes = await check_user_mistakes(user_id)
    has_mastery = await check_knowledge_mastery(user_id)

    print("\n=== 诊断结果 ===")
    if has_mistakes and not has_mastery:
        print("⚠️  问题确认: 用户有错题记录，但没有知识掌握度记录")
        print("   → 可能原因: 知识图谱快照未生成或数据未同步")
    elif not has_mistakes:
        print("⚠️  用户没有错题记录")
    elif has_mastery:
        print("✅ 数据正常: 用户有错题和知识掌握度记录")
        print("   → 需检查API查询逻辑")
    else:
        print("⚠️  未知情况")


if __name__ == "__main__":
    asyncio.run(main())
