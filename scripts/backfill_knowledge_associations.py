#!/usr/bin/env python3
"""
历史错题知识点关联批量补全脚本

功能:
1. 扫描所有缺少知识点关联的历史错题
2. 从 knowledge_points JSON 字段提取知识点
3. 批量创建 KnowledgeMastery 和 MistakeKnowledgePoint 关联
4. 为所有用户重新生成知识图谱快照

使用方法:
    python scripts/backfill_knowledge_associations.py [--dry-run] [--batch-size=100]

作者: AI Agent
创建时间: 2025-11-15
版本: v1.0
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# noqa: E402 - 模块导入必须在 sys.path 修改之后
from src.core.database import AsyncSessionLocal  # noqa: E402
from src.core.logging import configure_logging, get_logger  # noqa: E402
from src.models.study import KnowledgeMastery, MistakeRecord  # noqa: E402
from src.services.knowledge_graph_service import KnowledgeGraphService  # noqa: E402

# 配置日志
configure_logging()
logger = get_logger(__name__)


class KnowledgeAssociationBackfiller:
    """知识点关联批量补全器"""

    def __init__(self, db: AsyncSession, dry_run: bool = False, batch_size: int = 100):
        self.db = db
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            "total_mistakes": 0,
            "mistakes_without_assoc": 0,
            "mistakes_processed": 0,
            "associations_created": 0,
            "snapshots_generated": 0,
            "errors": 0,
            "skipped": 0,
        }

    async def run(self) -> Dict:
        """执行批量补全"""
        logger.info("=" * 80)
        logger.info("🚀 开始历史错题知识点关联批量补全")
        logger.info(f"⏰ 执行时间: {datetime.now().isoformat()}")
        logger.info(f"📊 模式: {'DRY-RUN (仅检查)' if self.dry_run else '正式执行'}")
        logger.info(f"📦 批次大小: {self.batch_size}")
        logger.info("=" * 80)

        try:
            # Step 1: 扫描缺失关联的错题
            mistakes_without_assoc = await self._find_mistakes_without_associations()
            self.stats["mistakes_without_assoc"] = len(mistakes_without_assoc)

            if not mistakes_without_assoc:
                logger.info("✅ 所有历史错题都已有知识点关联,无需补全")
                return self.stats

            logger.info(
                f"\n📋 发现 {len(mistakes_without_assoc)} 个错题缺少知识点关联"
            )

            if self.dry_run:
                logger.info("\n🔍 DRY-RUN 模式,仅显示待处理数据:")
                await self._preview_mistakes(mistakes_without_assoc[:10])
                logger.info(
                    f"\n💡 实际执行时将处理 {len(mistakes_without_assoc)} 个错题"
                )
                return self.stats

            # Step 2: 批量补全关联
            await self._backfill_associations(mistakes_without_assoc)

            # Step 3: 重新生成所有快照
            await self._regenerate_all_snapshots()

            logger.info("\n" + "=" * 80)
            logger.info("✅ 批量补全任务完成")
            self._print_stats()
            logger.info("=" * 80)

            return self.stats

        except Exception as e:
            logger.error(f"❌ 批量补全任务失败: {e}", exc_info=True)
            self.stats["errors"] += 1
            raise

    async def _find_mistakes_without_associations(self) -> List[MistakeRecord]:
        """查找缺少知识点关联的错题"""
        logger.info("\n🔍 Step 1: 扫描缺少知识点关联的错题...")

        # 查询所有错题总数
        result = await self.db.execute(text("SELECT COUNT(*) FROM mistake_records"))
        self.stats["total_mistakes"] = int(result.scalar() or 0)

        # 查询缺失关联的错题 (有 knowledge_points 但无关联记录)
        stmt = text("""
            SELECT m.*
            FROM mistake_records m
            LEFT JOIN mistake_knowledge_points mkp ON m.id = mkp.mistake_id
            WHERE mkp.id IS NULL
              AND m.knowledge_points IS NOT NULL
              AND m.knowledge_points != '[]'
              AND m.knowledge_points != 'null'
            ORDER BY m.created_at DESC
        """)

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        # 转换为 MistakeRecord 对象
        mistakes = []
        for row in rows:
            mistake = await self.db.get(MistakeRecord, row.id)
            if mistake:
                mistakes.append(mistake)

        total = self.stats['total_mistakes']
        coverage_pct = (len(mistakes) / total * 100) if total > 0 else 0
        logger.info(
            f"   总错题数: {total}, "
            f"缺少关联: {len(mistakes)} ({coverage_pct:.1f}%)"
        )

        return mistakes

    async def _preview_mistakes(self, mistakes: List[MistakeRecord]) -> None:
        """预览待处理错题 (DRY-RUN 模式)"""
        logger.info(f"\n📝 前 {len(mistakes)} 个待处理错题:")

        for i, mistake in enumerate(mistakes, 1):
            kp_list = mistake.knowledge_points or []
            # 确保 kp_list 是列表类型
            if not isinstance(kp_list, list):
                kp_list = []
            
            logger.info(
                f"   {i}. ID={str(mistake.id)[:8]}... | "
                f"Subject={str(mistake.subject)} | "
                f"KPs={len(kp_list)} | "
                f"Created={mistake.created_at.strftime('%Y-%m-%d')}"
            )
            if kp_list and len(kp_list) > 0:
                logger.info(f"      知识点: {', '.join(str(kp) for kp in kp_list[:3])}")

    async def _backfill_associations(self, mistakes: List[MistakeRecord]) -> None:
        """批量补全知识点关联"""
        logger.info(f"\n🔗 Step 2: 批量补全知识点关联 (批次大小: {self.batch_size})...")

        kg_service = KnowledgeGraphService(self.db)

        # 分批处理
        total = len(mistakes)
        for i in range(0, total, self.batch_size):
            batch = mistakes[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size

            logger.info(
                f"\n📦 处理批次 {batch_num}/{total_batches} "
                f"({len(batch)} 个错题)..."
            )

            for j, mistake in enumerate(batch, 1):
                try:
                    # 跳过没有知识点的错题
                    kp_list = mistake.knowledge_points or []
                    # 确保 kp_list 是列表类型
                    if not isinstance(kp_list, list):
                        kp_list = []
                    
                    if not kp_list or len(kp_list) == 0:
                        logger.debug(
                            f"   [{j}/{len(batch)}] 跳过 {mistake.id[:8]}... (无知识点)"
                        )
                        self.stats["skipped"] += 1
                        continue

                    # 构造 ai_feedback
                    ai_feedback = {
                        "knowledge_points": [
                            {"name": kp, "relevance": 0.8} for kp in kp_list
                        ]
                    }

                    # 创建关联
                    ocr_text_value = str(mistake.ocr_text) if hasattr(mistake.ocr_text, '__str__') else None
                    associations = await kg_service.analyze_and_associate_knowledge_points(
                        mistake_id=UUID(str(mistake.id)),
                        user_id=UUID(str(mistake.user_id)),
                        subject=str(mistake.subject),
                        ocr_text=ocr_text_value,
                        ai_feedback=ai_feedback,
                    )

                    if associations:
                        self.stats["mistakes_processed"] += 1
                        self.stats["associations_created"] += len(associations)
                        logger.info(
                            f"   ✅ [{j}/{len(batch)}] {mistake.id[:8]}... | "
                            f"创建 {len(associations)} 个关联 | "
                            f"Subject={mistake.subject}"
                        )
                    else:
                        logger.warning(
                            f"   ⚠️  [{j}/{len(batch)}] {mistake.id[:8]}... | "
                            f"未创建关联"
                        )
                        self.stats["skipped"] += 1

                except Exception as e:
                    logger.error(
                        f"   ❌ [{j}/{len(batch)}] {mistake.id[:8]}... | "
                        f"处理失败: {e}"
                    )
                    self.stats["errors"] += 1

            # 每批提交一次
            try:
                await self.db.commit()
                logger.info(
                    f"   💾 批次 {batch_num} 提交成功 "
                    f"(已处理: {self.stats['mistakes_processed']}/{total})"
                )
            except Exception as e:
                logger.error(f"   ❌ 批次 {batch_num} 提交失败: {e}")
                await self.db.rollback()
                self.stats["errors"] += 1

        logger.info(
            f"\n✅ 关联补全完成: "
            f"成功 {self.stats['mistakes_processed']}/{total}, "
            f"跳过 {self.stats['skipped']}, "
            f"失败 {self.stats['errors']}"
        )

    async def _regenerate_all_snapshots(self) -> None:
        """为所有用户重新生成知识图谱快照"""
        logger.info("\n📸 Step 3: 重新生成所有用户知识图谱快照...")

        # 查询所有用户-学科组合
        stmt = select(KnowledgeMastery.user_id, KnowledgeMastery.subject).distinct()
        result = await self.db.execute(stmt)
        combinations = result.all()

        if not combinations:
            logger.warning("   ⚠️  未发现知识掌握度记录,跳过快照生成")
            return

        logger.info(f"   发现 {len(combinations)} 个用户-学科组合")

        kg_service = KnowledgeGraphService(self.db)
        success_count = 0

        for i, (user_id, subject) in enumerate(combinations, 1):
            try:
                await kg_service.create_knowledge_graph_snapshot(
                    user_id=UUID(str(user_id)),
                    subject=subject,
                    period_type="backfill",
                    auto_commit=False,
                )
                success_count += 1
                logger.info(
                    f"   ✅ [{i}/{len(combinations)}] "
                    f"User={str(user_id)[:8]}... | Subject={subject}"
                )
            except Exception as e:
                logger.error(
                    f"   ❌ [{i}/{len(combinations)}] "
                    f"User={str(user_id)[:8]}... | Subject={subject} | "
                    f"Error={e}"
                )
                self.stats["errors"] += 1

        # 统一提交
        try:
            await self.db.commit()
            self.stats["snapshots_generated"] = success_count
            logger.info(f"\n   💾 快照批量提交成功: {success_count}/{len(combinations)}")
        except Exception as e:
            logger.error(f"   ❌ 快照批量提交失败: {e}")
            await self.db.rollback()

    def _print_stats(self) -> None:
        """打印统计信息"""
        logger.info("\n📊 执行统计:")
        logger.info(f"   总错题数: {self.stats['total_mistakes']}")
        logger.info(f"   缺少关联: {self.stats['mistakes_without_assoc']}")
        logger.info(f"   成功处理: {self.stats['mistakes_processed']}")
        logger.info(f"   创建关联: {self.stats['associations_created']}")
        logger.info(f"   生成快照: {self.stats['snapshots_generated']}")
        logger.info(f"   跳过: {self.stats['skipped']}")
        logger.info(f"   错误: {self.stats['errors']}")

        if self.stats["mistakes_processed"] > 0:
            coverage = (
                self.stats["mistakes_processed"]
                / self.stats["mistakes_without_assoc"]
                * 100
            )
            logger.info(f"   补全覆盖率: {coverage:.1f}%")


async def main(dry_run: bool = False, batch_size: int = 100):
    """主函数"""
    async with AsyncSessionLocal() as db:
        backfiller = KnowledgeAssociationBackfiller(db, dry_run, batch_size)
        stats = await backfiller.run()

        # 返回退出码
        if stats["errors"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="历史错题知识点关联批量补全")
    parser.add_argument(
        "--dry-run", action="store_true", help="DRY-RUN 模式,仅检查不执行"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="批次大小 (默认: 100)"
    )

    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run, batch_size=args.batch_size))
