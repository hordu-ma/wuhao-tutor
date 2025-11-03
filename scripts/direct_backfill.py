"""
直接版知识点补充脚本 - 使用 Service 层

使用方法:
  python scripts/direct_backfill.py --dry-run  # 测试模式
  python scripts/direct_backfill.py            # 执行补充
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 加载环境变量
env_file = Path(__file__).parent.parent / ".env.production"
if not env_file.exists():
    env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY")
BAILIAN_APPLICATION_ID = os.getenv("BAILIAN_APPLICATION_ID")

if not all([DATABASE_URL, BAILIAN_API_KEY, BAILIAN_APPLICATION_ID]):
    raise ValueError("缺少必要的环境变量配置")


async def backfill(dry_run: bool = False, limit: int = None):
    """补充知识点关联数据"""
    # 必须在这里导入，因为需要先加载环境变量
    from src.services.bailian_service import BailianService
    from src.services.knowledge_graph_service import KnowledgeGraphService

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("🔧 错题知识点补充工具（Service层版）")
    print("=" * 60)
    print(f"   模式: {'🧪 测试模式 (不执行)' if dry_run else '✅ 执行模式'}")
    print(f"   限制: {limit if limit else '全部'}")
    print()

    async with async_session() as session:
        # 查询没有知识点关联的错题
        query = text(
            """
            SELECT m.id, m.user_id, m.subject, m.title, m.ocr_text, m.created_at
            FROM mistake_records m
            LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
            WHERE mkp.id IS NULL
            ORDER BY m.created_at DESC
        """
        )

        if limit:
            query = text(str(query) + f" LIMIT {limit}")

        result = await session.execute(query)
        mistakes = result.fetchall()

        total = len(mistakes)
        print(f"📋 找到 {total} 条需要补充知识点的错题\n")

        if dry_run:
            print("🧪 测试模式：以下错题将被处理:\n")
            for i, (mid, user_id, subject, title, ocr_text, created_at) in enumerate(
                mistakes, 1
            ):
                preview = (ocr_text or "")[:50]
                print(f"{i}. ID: {mid}")
                print(f"   用户: {user_id}")
                print(f"   学科: {subject}")
                print(f"   标题: {title or '无标题'}")
                print(f"   内容: {preview}...")
                print(f"   创建时间: {created_at}")
                print()
            return

        # 执行补充
        success_count = 0
        error_count = 0

        # 初始化服务
        bailian_service = BailianService()
        kg_service = KnowledgeGraphService(session, bailian_service)

        for i, (mid, user_id, subject, title, ocr_text, created_at) in enumerate(
            mistakes, 1
        ):
            print(f"[{i}/{total}] 处理错题: {title or '无标题'}")
            print(f"   ID: {mid}")
            print(f"   学科: {subject}")

            try:
                # 调用知识图谱服务分析并关联知识点
                await kg_service.analyze_and_associate_knowledge_points(
                    mistake_id=UUID(str(mid)),
                    user_id=UUID(str(user_id)),
                    subject=subject,
                    ocr_text=ocr_text or "",
                    ai_feedback=None,  # 没有AI反馈，让服务自己分析
                )

                await session.commit()
                print(f"   ✅ 成功")
                success_count += 1

            except Exception as e:
                await session.rollback()
                print(f"   ❌ 失败: {e}")
                error_count += 1

            # 避免频繁调用AI
            await asyncio.sleep(1.0)

        print("\n" + "=" * 60)
        print("📊 处理完成:")
        print(f"   成功: {success_count}")
        print(f"   失败: {error_count}")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="补充错题知识点关联")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不执行")
    parser.add_argument("--limit", type=int, help="限制处理数量")

    args = parser.parse_args()
    asyncio.run(backfill(dry_run=args.dry_run, limit=args.limit))
