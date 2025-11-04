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

from sqlalchemy import select, update

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
        from sqlalchemy import func

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

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, select, update

from src.core.database import AsyncSessionLocal
from src.models.study import KnowledgeMastery, MistakeRecord


def infer_subject_from_content(content: str) -> str:
    """
    从内容智能推断科目（与 learning_service.py 保持一致）
    """
    if not content:
        return "数学"

    content_lower = content.lower()

    # 科目关键词库
    subject_keywords = {
        "数学": [
            "方程",
            "函数",
            "几何",
            "三角",
            "代数",
            "微积分",
            "导数",
            "积分",
            "圆",
            "直线",
            "抛物线",
            "椭圆",
            "双曲线",
            "正弦",
            "余弦",
            "正切",
            "sin",
            "cos",
            "tan",
            "x",
            "y",
            "z",
            "f(x)",
            "π",
            "∫",
            "∑",
            "求解",
            "计算",
            "证明",
            "面积",
            "体积",
            "长度",
            "球",
            "圆柱",
            "棱锥",
            "立方体",
        ],
        "物理": [
            "力",
            "速度",
            "加速度",
            "质量",
            "能量",
            "功",
            "功率",
            "牛顿",
            "焦耳",
            "瓦特",
            "欧姆",
            "伏特",
            "安培",
            "电路",
            "磁场",
            "电场",
            "电流",
            "电压",
            "电阻",
            "光",
            "波",
            "声",
            "热",
            "温度",
            "压强",
            "F=",
            "W=",
            "P=",
            "E=",
            "v=",
            "a=",
        ],
        "化学": [
            "化学式",
            "化学反应",
            "分子",
            "原子",
            "离子",
            "元素",
            "氧化",
            "还原",
            "酸",
            "碱",
            "盐",
            "pH",
            "H₂O",
            "CO₂",
            "O₂",
            "H₂",
            "Na",
            "Cl",
            "摩尔",
            "溶液",
            "浓度",
            "质量分数",
            "反应方程式",
            "化合物",
            "单质",
        ],
        "英语": [
            "grammar",
            "vocabulary",
            "tense",
            "sentence",
            "translate",
            "reading",
            "writing",
            "speaking",
            "verb",
            "noun",
            "adjective",
            "adverb",
            "past",
            "present",
            "future",
            "passive",
            "what",
            "where",
            "when",
            "who",
            "how",
            "why",
        ],
        "语文": [
            "作文",
            "阅读理解",
            "古诗",
            "文言文",
            "现代文",
            "作者",
            "主题",
            "手法",
            "修辞",
            "比喻",
            "拟人",
            "段落",
            "中心思想",
            "写作",
            "文章",
            "朗诵",
            "背诵",
            "默写",
            "古文",
            "诗词",
        ],
        "生物": [
            "细胞",
            "基因",
            "遗传",
            "染色体",
            "DNA",
            "RNA",
            "光合作用",
            "呼吸作用",
            "新陈代谢",
            "生态",
            "环境",
            "物种",
            "进化",
            "器官",
            "组织",
            "系统",
            "血液",
            "神经",
        ],
    }

    # 统计每个科目的关键词匹配数
    scores = {}
    for subject, keywords in subject_keywords.items():
        count = sum(1 for kw in keywords if kw in content_lower)
        if count > 0:
            scores[subject] = count

    # 返回匹配最多的科目，如果没有匹配则默认数学
    if scores:
        return max(scores, key=scores.get)

    return "数学"


async def fix_knowledge_point_subjects():
    """
    修复知识点科目数据

    步骤:
    1. 查询所有科目为"其他"的 KnowledgeMastery 记录
    2. 通过关联的错题获取OCR内容
    3. 智能推断正确科目
    4. 批量更新
    """
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("📚 修复知识点科目数据")
        print("=" * 60)

        # 1. 查询科目为"其他"的记录
        stmt = select(KnowledgeMastery).where(KnowledgeMastery.subject == "其他")
        result = await session.execute(stmt)
        wrong_subject_records = result.scalars().all()

        print(f"\n发现 {len(wrong_subject_records)} 条科目为'其他'的记录")

        if not wrong_subject_records:
            print("✅ 无需修复！")
            return

        # 2. 批量处理
        updated_count = 0
        skipped_count = 0

        for km in wrong_subject_records:
            try:
                # 尝试从用户的错题中获取内容
                # 通过 user_id + knowledge_point 查找相关错题
                from src.models.knowledge_graph import MistakeKnowledgePoint

                # 查找关联的错题
                assoc_stmt = (
                    select(MistakeKnowledgePoint)
                    .where(MistakeKnowledgePoint.knowledge_point_id == str(km.id))
                    .limit(1)
                )
                assoc_result = await session.execute(assoc_stmt)
                assoc = assoc_result.scalar_one_or_none()

                if not assoc:
                    print(f"⚠️  跳过: {km.knowledge_point} (无关联错题)")
                    skipped_count += 1
                    continue

                # 获取错题内容
                mistake_stmt = select(Mistake).where(Mistake.id == assoc.mistake_id)
                mistake_result = await session.execute(mistake_stmt)
                mistake = mistake_result.scalar_one_or_none()

                if not mistake or not mistake.ocr_text:
                    print(f"⚠️  跳过: {km.knowledge_point} (无OCR内容)")
                    skipped_count += 1
                    continue

                # 推断科目
                inferred_subject = infer_subject_from_content(mistake.ocr_text)

                # 更新记录
                km.subject = inferred_subject
                updated_count += 1

                print(f"✅ 更新: {km.knowledge_point} -> {inferred_subject}")

            except Exception as e:
                print(f"❌ 处理失败: {km.knowledge_point}, 错误: {e}")
                skipped_count += 1

        # 提交事务
        if updated_count > 0:
            await session.commit()
            print(f"\n✅ 成功更新 {updated_count} 条记录")

        if skipped_count > 0:
            print(f"⚠️  跳过 {skipped_count} 条记录")

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
        from sqlalchemy import func

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
