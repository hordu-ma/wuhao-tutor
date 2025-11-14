#!/usr/bin/env python3
"""检查用户数据 - 错题和知识图谱记录"""

import asyncio
import os
import sys
from uuid import UUID

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select

from src.core.database import AsyncSessionLocal
from src.models.study import KnowledgeMastery, MistakeRecord


async def check_user_data(user_id: UUID):
    """检查用户的数据"""
    async with AsyncSessionLocal() as db:
        # 统计错题
        stmt = select(func.count(MistakeRecord.id)).where(
            MistakeRecord.user_id == user_id
        )
        result = await db.execute(stmt)
        mistake_count = result.scalar_one()

        print(f"\n=== 用户 {user_id} ===")
        print(f"错题总数: {mistake_count}")

        if mistake_count > 0:
            # 按学科统计
            stmt = (
                select(
                    MistakeRecord.subject, func.count(MistakeRecord.id).label("count")
                )
                .where(MistakeRecord.user_id == user_id)
                .group_by(MistakeRecord.subject)
            )
            result = await db.execute(stmt)
            subject_counts = result.all()

            print("\n各学科错题数量:")
            for subject, count in subject_counts:
                print(f"  {subject}: {count}条")

            # 获取一条错题样例
            stmt = (
                select(MistakeRecord).where(MistakeRecord.user_id == user_id).limit(1)
            )
            result = await db.execute(stmt)
            mistake = result.scalar_one_or_none()

            if mistake:
                print(f"\n样例错题:")
                print(f"  ID: {mistake.id}")
                print(f"  学科: {mistake.subject}")
                print(
                    f"  问题: {mistake.question[:80] if mistake.question else 'N/A'}..."
                )
                print(f"  知识点字段类型: {type(mistake.knowledge_points)}")
                print(f"  知识点内容: {mistake.knowledge_points}")

        # 统计知识掌握度
        stmt = select(func.count(KnowledgeMastery.id)).where(
            KnowledgeMastery.user_id == user_id
        )
        result = await db.execute(stmt)
        mastery_count = result.scalar_one()

        print(f"\n知识掌握度记录数: {mastery_count}")

        if mastery_count > 0:
            # 按学科统计
            stmt = (
                select(
                    KnowledgeMastery.subject,
                    func.count(KnowledgeMastery.id).label("count"),
                )
                .where(KnowledgeMastery.user_id == user_id)
                .group_by(KnowledgeMastery.subject)
            )
            result = await db.execute(stmt)
            subject_counts = result.all()

            print("\n各学科知识点数量:")
            for subject, count in subject_counts:
                print(f"  {subject}: {count}个")

        # 诊断
        print("\n=== 诊断结果 ===")
        if mistake_count == 0:
            print("⚠️  用户没有错题记录")
        elif mastery_count == 0:
            print("⚠️  问题确认: 用户有错题但没有知识掌握度记录")
            print("   → 原因: 知识图谱快照未生成")
        else:
            print("✅ 数据正常: 错题和知识掌握度记录都存在")


async def main():
    # 马雅姮的用户ID
    user_id = UUID("e10d8b6b-033a-4198-bb7b-99ff1d4d5ea8")
    await check_user_data(user_id)


if __name__ == "__main__":
    asyncio.run(main())
