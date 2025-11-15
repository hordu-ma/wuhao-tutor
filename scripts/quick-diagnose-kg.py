#!/usr/bin/env python3
"""
快速诊断知识图谱数据问题的脚本
检查：1. MistakeRecord 数据 2. KnowledgeMastery 数据 3. 关联关系
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.models.knowledge_graph import MistakeKnowledgePoint
from src.models.study import KnowledgeMastery, MistakeRecord


async def main():
    """主诊断流程"""
    settings = get_settings()

    # 创建异步引擎
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True,
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            print("=" * 80)
            print("知识图谱快速诊断工具")
            print("=" * 80)

            # 1. 检查 MistakeRecord 数据
            print("\n📋 【步骤1】检查 MistakeRecord 表数据")
            print("-" * 80)
            await diagnose_mistake_records(session)

            # 2. 检查 KnowledgeMastery 数据
            print("\n📊 【步骤2】检查 KnowledgeMastery 表数据")
            print("-" * 80)
            await diagnose_knowledge_mastery(session)

            # 3. 检查关联关系
            print("\n🔗 【步骤3】检查 MistakeKnowledgePoint 关联关系")
            print("-" * 80)
            await diagnose_associations(session)

            # 4. 检查学科标准化
            print("\n🌍 【步骤4】检查学科名称标准化")
            print("-" * 80)
            await diagnose_subject_normalization(session)

            # 5. 生成诊断摘要
            print("\n" + "=" * 80)
            print("📈 诊断摘要")
            print("=" * 80)
            await generate_summary(session)

    finally:
        await engine.dispose()


async def diagnose_mistake_records(session: AsyncSession):
    """诊断 MistakeRecord 表"""
    try:
        # 1. 获取总记录数
        total_stmt = select(func.count(MistakeRecord.id))
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar() or 0
        print(f"✅ MistakeRecord 总数: {total_count}")

        if total_count == 0:
            print("⚠️  警告：MistakeRecord 表为空，无错题数据！")
            return

        # 2. 按学科统计
        subject_stmt = select(
            MistakeRecord.subject, func.count(MistakeRecord.id).label("count")
        ).group_by(MistakeRecord.subject)
        subject_result = await session.execute(subject_stmt)
        subjects = subject_result.all()

        print(f"\n📚 按学科分布:")
        for subject, count in subjects:
            print(f"   - {subject}: {count} 条")

        # 3. 检查 knowledge_points 字段
        has_kp_stmt = select(func.count(MistakeRecord.id)).where(
            MistakeRecord.knowledge_points != None
        )
        has_kp_result = await session.execute(has_kp_stmt)
        has_kp_count = has_kp_result.scalar() or 0

        print(f"\n✅ 有 knowledge_points 字段的记录: {has_kp_count}/{total_count}")

        # 4. 采样检查 knowledge_points 内容
        sample_stmt = select(MistakeRecord).limit(3)
        sample_result = await session.execute(sample_stmt)
        samples = sample_result.scalars().all()

        print(f"\n🔍 采样检查（前3条）:")
        for i, record in enumerate(samples, 1):
            print(f"\n   记录 {i}:")
            print(f"   - ID: {record.id}")
            print(f"   - 学科: {record.subject}")
            print(f"   - 标题: {record.title[:50]}...")
            print(f"   - knowledge_points: {record.knowledge_points}")

    except Exception as e:
        print(f"❌ 诊断 MistakeRecord 失败: {e}")
        import traceback

        traceback.print_exc()


async def diagnose_knowledge_mastery(session: AsyncSession):
    """诊断 KnowledgeMastery 表"""
    try:
        # 1. 获取总记录数
        total_stmt = select(func.count(KnowledgeMastery.id))
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar() or 0
        print(f"✅ KnowledgeMastery 总数: {total_count}")

        if total_count == 0:
            print("⚠️  警告：KnowledgeMastery 表为空！")
            print("   这是知识图谱不显示的主要原因。")
            print("   需要检查 analyze_and_associate_knowledge_points() 是否正确执行。")
            return

        # 2. 按学科统计
        subject_stmt = select(
            KnowledgeMastery.subject, func.count(KnowledgeMastery.id).label("count")
        ).group_by(KnowledgeMastery.subject)
        subject_result = await session.execute(subject_stmt)
        subjects = subject_result.all()

        print(f"\n📚 按学科分布:")
        for subject, count in subjects:
            print(f"   - {subject}: {count} 条")

        # 3. 按用户统计
        user_stmt = select(
            KnowledgeMastery.user_id, func.count(KnowledgeMastery.id).label("count")
        ).group_by(KnowledgeMastery.user_id)
        user_result = await session.execute(user_stmt)
        users = user_result.all()

        print(f"\n👥 按用户分布 (前5个用户):")
        for user_id, count in list(users)[:5]:
            print(f"   - {user_id}: {count} 条")

        # 4. 采样检查
        sample_stmt = select(KnowledgeMastery).limit(3)
        sample_result = await session.execute(sample_stmt)
        samples = sample_result.scalars().all()

        print(f"\n🔍 采样检查（前3条）:")
        for i, record in enumerate(samples, 1):
            print(f"\n   记录 {i}:")
            print(f"   - ID: {record.id}")
            print(f"   - 用户: {record.user_id}")
            print(f"   - 学科: {record.subject}")
            print(f"   - 知识点: {record.knowledge_point}")
            print(f"   - 掌握度: {record.mastery_level}")

    except Exception as e:
        print(f"❌ 诊断 KnowledgeMastery 失败: {e}")
        import traceback

        traceback.print_exc()


async def diagnose_associations(session: AsyncSession):
    """诊断关联关系"""
    try:
        # 1. 获取总关联数
        total_stmt = select(func.count(MistakeKnowledgePoint.id))
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar() or 0
        print(f"✅ MistakeKnowledgePoint 总数: {total_count}")

        if total_count == 0:
            print("⚠️  警告：MistakeKnowledgePoint 表为空！")
            print("   说明错题与知识点的关联未被创建。")
            return

        # 2. 采样检查
        sample_stmt = select(MistakeKnowledgePoint).limit(5)
        sample_result = await session.execute(sample_stmt)
        samples = sample_result.scalars().all()

        print(f"\n🔍 采样检查（前5条）:")
        for i, record in enumerate(samples, 1):
            print(f"\n   关联 {i}:")
            print(f"   - ID: {record.id}")
            print(f"   - 错题ID: {record.mistake_id}")
            print(f"   - 知识点ID: {record.knowledge_point_id}")

    except Exception as e:
        print(f"❌ 诊断关联关系失败: {e}")
        import traceback

        traceback.print_exc()


async def diagnose_subject_normalization(session: AsyncSession):
    """检查学科名称标准化问题"""
    try:
        print("检查学科名称是否统一...")

        # 获取 MistakeRecord 中的所有学科
        mr_subjects_stmt = select(MistakeRecord.subject).distinct()
        mr_result = await session.execute(mr_subjects_stmt)
        mr_subjects = set(row[0] for row in mr_result if row[0])

        print(f"✅ MistakeRecord 中的学科: {mr_subjects}")

        # 获取 KnowledgeMastery 中的所有学科
        km_subjects_stmt = select(KnowledgeMastery.subject).distinct()
        km_result = await session.execute(km_subjects_stmt)
        km_subjects = set(row[0] for row in km_result if row[0])

        print(f"✅ KnowledgeMastery 中的学科: {km_subjects}")

        # 检查是否存在不匹配
        only_in_mr = mr_subjects - km_subjects
        only_in_km = km_subjects - mr_subjects

        if only_in_mr:
            print(f"\n⚠️  仅在 MistakeRecord 中存在的学科: {only_in_mr}")

        if only_in_km:
            print(f"\n⚠️  仅在 KnowledgeMastery 中存在的学科: {only_in_km}")

        if not only_in_mr and not only_in_km:
            print("\n✅ 学科名称统一，无不匹配问题")

    except Exception as e:
        print(f"❌ 诊断学科标准化失败: {e}")
        import traceback

        traceback.print_exc()


async def generate_summary(session: AsyncSession):
    """生成诊断摘要"""
    try:
        # 统计各表数据
        mr_count_stmt = select(func.count(MistakeRecord.id))
        mr_count = (await session.execute(mr_count_stmt)).scalar() or 0

        km_count_stmt = select(func.count(KnowledgeMastery.id))
        km_count = (await session.execute(km_count_stmt)).scalar() or 0

        mkp_count_stmt = select(func.count(MistakeKnowledgePoint.id))
        mkp_count = (await session.execute(mkp_count_stmt)).scalar() or 0

        print(f"\n📊 数据统计:")
        print(f"   - MistakeRecord: {mr_count}")
        print(f"   - KnowledgeMastery: {km_count}")
        print(f"   - MistakeKnowledgePoint: {mkp_count}")

        # 诊断问题
        print(f"\n🔍 问题诊断:")

        issues = []

        if mr_count == 0:
            issues.append("❌ MistakeRecord 为空 → 无错题数据")

        if km_count == 0:
            issues.append("❌ KnowledgeMastery 为空 → 知识点关联未创建")
        elif km_count < mr_count / 2:
            issues.append(
                f"⚠️  KnowledgeMastery ({km_count}) 远少于 MistakeRecord ({mr_count}) → 可能有错题未关联知识点"
            )

        if mkp_count == 0 and mr_count > 0:
            issues.append("❌ MistakeKnowledgePoint 为空 → 错题知识点关联未创建")

        if not issues:
            print("✅ 数据一致，知识图谱应能正常显示")
        else:
            for issue in issues:
                print(f"   {issue}")

        print(f"\n💡 建议:")
        print(f"   1. 查看后端日志，搜索关键词：")
        print(f"      - '✅ 已为错题' → 确认知识点是否关联成功")
        print(f"      - '❌ 知识点自动关联失败' → 查看具体错误")
        print(f"      - '⚠️ 知识点列表为空' → 确认AI是否提取知识点")
        print(f"\n   2. 查看前端网络请求：")
        print(f"      - GET /knowledge-graph/graphs/math (或其他学科)")
        print(f"      - 检查响应中是否有 'nodes' 字段")
        print(f"\n   3. 执行以下命令查看实时日志：")
        print(
            f"      journalctl -u wuhao-tutor.service -f | grep -E '知识图谱|关联知识点'"
        )

    except Exception as e:
        print(f"❌ 生成摘要失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
