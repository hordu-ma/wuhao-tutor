#!/usr/bin/env python3
"""
修复错题记录科目数据脚本

问题：MistakeRecord 表中的 subject 字段大部分为"其他"，导致按科目筛选时返回空结果
解决：根据 OCR 文本智能推断科目并批量更新

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
from src.models.study import MistakeRecord


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
            "9999",
            "简便方法",
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


async def fix_mistake_subjects():
    """
    修复错题记录科目数据
    """
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("📚 修复错题记录科目数据")
        print("=" * 60)

        # 1. 查询科目为"其他"的记录
        stmt = select(MistakeRecord).where(MistakeRecord.subject == "其他")
        result = await session.execute(stmt)
        wrong_subject_records = result.scalars().all()

        count = len(wrong_subject_records)
        print(f"\n发现 {count} 条科目为'其他'的错题记录")

        if count == 0:
            print("✅ 无需修复！")
            return

        # 2. 批量更新
        print(f"\n开始智能推断科目...\n")

        updated_count = 0

        for record in wrong_subject_records:
            # 从 OCR 文本推断科目
            content = record.ocr_text or record.title or ""
            inferred_subject = infer_subject_from_content(content)

            record.subject = inferred_subject
            updated_count += 1

            title_preview = (record.title[:20] if record.title else "无标题") + "..."
            print(f"  ✅ {title_preview} -> {inferred_subject}")

        # 提交事务
        await session.commit()

        print(f"\n✅ 成功更新 {updated_count} 条记录")
        print("\n" + "=" * 60)
        print("修复完成!")
        print("=" * 60)


async def verify_fixes():
    """验证修复结果"""
    async with AsyncSessionLocal() as session:
        print("\n" + "=" * 60)
        print("📊 验证修复结果")
        print("=" * 60)

        # 统计各科目的错题数量
        stmt = select(
            MistakeRecord.subject, func.count(MistakeRecord.id).label("count")
        ).group_by(MistakeRecord.subject)

        result = await session.execute(stmt)
        rows = result.all()

        print("\n错题科目分布:")
        for subject, count in rows:
            print(f"  {subject}: {count} 个错题")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n⚙️  开始修复错题记录科目数据...\n")

    # 运行修复
    asyncio.run(fix_mistake_subjects())

    # 验证结果
    asyncio.run(verify_fixes())

    print("\n✨ 全部完成！\n")
