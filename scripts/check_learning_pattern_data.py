#!/usr/bin/env python
"""检查学习模式相关数据的完整性"""

import asyncio

from sqlalchemy import func, select, text

from src.core.database import AsyncSessionLocal
from src.models.learning import Question


async def check_data():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("学习模式数据诊断报告")
        print("=" * 60)

        # 1. 检查基本统计
        stmt = select(
            func.count(Question.id).label("total"),
            func.count(Question.difficulty_level).label("with_difficulty"),
            func.count(Question.session_id).label("with_session"),
        )
        result = await db.execute(stmt)
        stats = result.one()

        print(f"\n【基本统计】")
        print(f"  总问题数: {stats.total}")
        print(f"  有难度级别的: {stats.with_difficulty}")
        print(f"  有会话ID的: {stats.with_session}")
        if stats.total > 0:
            print(f"  难度级别填充率: {stats.with_difficulty/stats.total*100:.1f}%")

        # 2. 难度级别分布
        if stats.with_difficulty > 0:
            stmt2 = (
                select(Question.difficulty_level, func.count(Question.id))
                .where(Question.difficulty_level.isnot(None))
                .group_by(Question.difficulty_level)
            )
            result2 = await db.execute(stmt2)
            print("\n【难度级别分布】")
            difficulty_map = {1: "简单", 2: "较简单", 3: "中等", 4: "较难", 5: "困难"}
            for row in result2.all():
                print(
                    f'  难度 {row[0]} ({difficulty_map.get(row[0], "未知")}): {row[1]} 个问题'
                )
        else:
            print("\n【难度级别分布】")
            print("  ⚠️  没有问题包含难度级别数据")

        # 3. 检查时间分布(小时)
        stmt3 = text(
            """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM questions
        WHERE created_at IS NOT NULL
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 10
        """
        )
        result3 = await db.execute(stmt3)
        rows = result3.all()
        if rows:
            print("\n【最活跃时段】(前10)")
            for row in rows:
                print(f"  {row.hour:02d}:00 - {row.count} 个问题")
        else:
            print("\n【最活跃时段】")
            print("  ⚠️  没有时间数据")

        # 4. 检查星期分布
        stmt4 = text(
            """
        SELECT 
            CAST(strftime('%w', created_at) AS INTEGER) as weekday,
            COUNT(*) as count
        FROM questions
        WHERE created_at IS NOT NULL
        GROUP BY weekday
        ORDER BY count DESC
        """
        )
        result4 = await db.execute(stmt4)
        rows4 = result4.all()
        if rows4:
            print("\n【最活跃日期】")
            weekday_map = {
                0: "周日",
                1: "周一",
                2: "周二",
                3: "周三",
                4: "周四",
                5: "周五",
                6: "周六",
            }
            for row in rows4:
                print(f'  {weekday_map.get(row.weekday, "未知")} - {row.count} 个问题')
        else:
            print("\n【最活跃日期】")
            print("  ⚠️  没有日期数据")

        # 5. 检查会话时长(每个会话的问题数)
        stmt5 = text(
            """
        SELECT 
            session_id,
            COUNT(*) as question_count
        FROM questions
        WHERE session_id IS NOT NULL
        GROUP BY session_id
        """
        )
        result5 = await db.execute(stmt5)
        session_counts = [row.question_count for row in result5.all()]

        if session_counts:
            avg_questions = sum(session_counts) / len(session_counts)
            avg_minutes = int(avg_questions * 5)  # 每个问题5分钟
            print("\n【平均会话时长】")
            print(f"  总会话数: {len(session_counts)}")
            print(f"  平均每会话问题数: {avg_questions:.1f}")
            print(f"  估算平均时长: {avg_minutes} 分钟")
        else:
            print("\n【平均会话时长】")
            print("  ⚠️  没有会话数据")

        # 6. 综合结论
        print("\n" + "=" * 60)
        print("【诊断结论】")
        print("=" * 60)

        issues = []
        if stats.with_difficulty == 0:
            issues.append("❌ difficulty_level 字段完全为空 - 偏好难度功能不可用")
        elif stats.with_difficulty < stats.total * 0.5:
            issues.append(
                f"⚠️  difficulty_level 字段填充率仅 {stats.with_difficulty/stats.total*100:.1f}% - 偏好难度可能不准确"
            )
        else:
            print("✅ difficulty_level 字段数据充足 - 偏好难度功能正常")

        if stats.total > 0 and rows:
            print("✅ created_at 字段有数据 - 最活跃时段/日期功能正常")
        else:
            issues.append("❌ created_at 字段为空 - 最活跃时段/日期功能不可用")

        if session_counts:
            print("✅ session_id 字段有数据 - 平均会话时长功能正常")
        else:
            issues.append("❌ session_id 字段为空 - 平均会话时长功能不可用")

        if issues:
            print("\n存在以下问题:")
            for issue in issues:
                print(f"  {issue}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_data())
