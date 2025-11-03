"""
为现有错题补充知识点关联数据

使用方法:
1. 开发环境: python scripts/backfill_knowledge_points.py
2. 生产环境: ssh 到服务器后运行

功能:
- 扫描所有没有知识点关联的错题
- 调用知识图谱服务分析并关联知识点
- 显示处理进度和结果统计
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 加载环境变量（优先使用 .env.production）
env_file = Path(__file__).parent.parent / ".env.production"
if not env_file.exists():
    env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

from src.models.knowledge_graph import MistakeKnowledgePoint
from src.models.mistake import MistakeRecord
from src.services.bailian_service import BailianService
from src.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

# 从环境变量获取数据库连接
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")
if not DATABASE_URL:
    raise ValueError("未找到数据库配置 SQLALCHEMY_DATABASE_URI")


async def backfill_knowledge_points(limit: int = None, dry_run: bool = False):
    """
    为没有知识点关联的错题补充关联数据

    Args:
        limit: 限制处理的错题数量（None = 处理全部）
        dry_run: 只检查不执行（测试模式）
    """
    # 创建数据库连接
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("🔧 错题知识点关联数据补充工具")
    print("=" * 60)

    async with async_session() as session:
        # 1. 统计总体情况
        total_mistakes = await session.execute(
            select(func.count()).select_from(MistakeRecord)
        )
        total_count = total_mistakes.scalar()

        total_associations = await session.execute(
            select(func.count()).select_from(MistakeKnowledgePoint)
        )
        assoc_count = total_associations.scalar()

        print(f"\n📊 当前状态:")
        print(f"   错题总数: {total_count}")
        print(f"   知识点关联总数: {assoc_count}")

        # 2. 找出没有知识点关联的错题
        stmt = (
            select(MistakeRecord.id, MistakeRecord.subject, MistakeRecord.ocr_text)
            .outerjoin(
                MistakeKnowledgePoint,
                MistakeRecord.id == MistakeKnowledgePoint.mistake_id,
            )
            .where(MistakeKnowledgePoint.id == None)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        mistakes_without_kp = result.all()

        print(f"\n🎯 待处理错题: {len(mistakes_without_kp)}")

        if dry_run:
            print(f"\n⚠️ 测试模式 - 不会执行实际关联")
            if mistakes_without_kp:
                print("\n示例错题:")
                for i, (mid, subject, ocr_text) in enumerate(
                    mistakes_without_kp[:5], 1
                ):
                    preview = (
                        (ocr_text or "")[:50] + "..."
                        if ocr_text and len(ocr_text) > 50
                        else (ocr_text or "无内容")
                    )
                    print(f"  {i}. ID: {mid}, 学科: {subject}")
                    print(f"     内容: {preview}")
            return

        if not mistakes_without_kp:
            print("\n✅ 所有错题都已有知识点关联！")
            return

        # 3. 处理每个错题
        print(f"\n🚀 开始处理...")

        # 初始化服务
        bailian_service = BailianService()

        success_count = 0
        fail_count = 0
        skip_count = 0

        for i, (mistake_id, subject, ocr_text) in enumerate(mistakes_without_kp, 1):
            print(f"\n[{i}/{len(mistakes_without_kp)}] 处理错题 {mistake_id}...")

            # 如果没有题目内容，跳过
            if not ocr_text or ocr_text.strip() == "":
                print(f"  ⏭️  跳过 - 无题目内容")
                skip_count += 1
                continue

            try:
                # 创建新的session用于此次操作
                async with async_session() as op_session:
                    # 查询完整错题信息
                    mistake_stmt = select(MistakeRecord).where(
                        MistakeRecord.id == mistake_id
                    )
                    mistake_result = await op_session.execute(mistake_stmt)
                    mistake = mistake_result.scalar_one_or_none()

                    if not mistake:
                        print(f"  ❌ 错题不存在")
                        fail_count += 1
                        continue

                    # 创建知识图谱服务
                    kg_service = KnowledgeGraphService(op_session, bailian_service)

                    # 分析并关联知识点
                    await kg_service.analyze_and_associate_knowledge_points(
                        mistake_id=UUID(str(mistake.id)),
                        user_id=UUID(str(mistake.user_id)),
                        subject=subject,
                        ocr_text=ocr_text,
                        ai_feedback=None,  # 让AI自动提取
                    )

                    await op_session.commit()
                    print(f"  ✅ 成功关联知识点")
                    success_count += 1

            except Exception as e:
                logger.error(f"处理错题 {mistake_id} 失败: {e}", exc_info=True)
                print(f"  ❌ 失败: {str(e)}")
                fail_count += 1
                continue

        # 4. 显示结果统计
        print("\n" + "=" * 60)
        print("📈 处理结果统计:")
        print(f"   ✅ 成功: {success_count}")
        print(f"   ❌ 失败: {fail_count}")
        print(f"   ⏭️  跳过: {skip_count}")
        print(f"   📝 总计: {len(mistakes_without_kp)}")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="为错题补充知识点关联")
    parser.add_argument("--limit", type=int, help="限制处理数量")
    parser.add_argument("--dry-run", action="store_true", help="测试模式（不执行）")

    args = parser.parse_args()

    asyncio.run(backfill_knowledge_points(limit=args.limit, dry_run=args.dry_run))
