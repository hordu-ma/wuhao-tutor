"""
简化版知识点补充脚本 - 直接调用生产API

使用方法:
  python scripts/simple_backfill.py --dry-run  # 测试模式
  python scripts/simple_backfill.py            # 执行补充
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
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
if not DATABASE_URL:
    raise ValueError("未找到数据库配置")


async def call_kg_api(mistake_id: str, api_url: str = "http://127.0.0.1:8000"):
    """
    调用知识图谱API为错题添加知识点

    Args:
        mistake_id: 错题ID
        api_url: API基础URL
    """
    url = f"{api_url}/api/v1/knowledge-graph/analyze-mistake/{mistake_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"      ❌ API调用失败: {e}")
            return None


async def backfill(dry_run: bool = False, limit: int = None):
    """补充知识点关联数据"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("🔧 错题知识点补充工具（API调用版）")
    print("=" * 60)
    print(f"   模式: {'🧪 测试模式 (不执行)' if dry_run else '✅ 执行模式'}")
    print(f"   限制: {limit if limit else '全部'}")
    print()

    async with async_session() as session:
        # 查询没有知识点关联的错题
        query = text(
            """
            SELECT m.id, m.subject, m.title, m.ocr_text, m.created_at
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
            for i, (mid, subject, title, ocr_text, created_at) in enumerate(
                mistakes, 1
            ):
                preview = (ocr_text or "")[:50]
                print(f"{i}. ID: {mid}")
                print(f"   学科: {subject}")
                print(f"   标题: {title or '无标题'}")
                print(f"   内容: {preview}...")
                print(f"   创建时间: {created_at}")
                print()
            return

        # 执行补充
        success_count = 0
        error_count = 0

        for i, (mid, subject, title, ocr_text, created_at) in enumerate(mistakes, 1):
            print(f"[{i}/{total}] 处理错题: {title or '无标题'} (ID: {mid})")

            result = await call_kg_api(str(mid))
            if result:
                print(f"      ✅ 成功")
                success_count += 1
            else:
                print(f"      ❌ 失败")
                error_count += 1

            # 避免频繁调用
            await asyncio.sleep(0.5)

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
