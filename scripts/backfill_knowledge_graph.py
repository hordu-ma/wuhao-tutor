#!/usr/bin/env python3
"""
历史错题知识图谱数据批量补全脚本

功能:
1. 扫描缺失知识点关联的历史错题
2. 批量调用 AI 分析并创建知识点关联
3. 批量生成知识图谱快照

使用方法:
    # DRY-RUN 模式（不实际执行，仅预览）
    python scripts/backfill_knowledge_graph.py --dry-run
    
    # 正式执行（小批量测试）
    python scripts/backfill_knowledge_graph.py --batch-size 10
    
    # 全量执行
    python scripts/backfill_knowledge_graph.py --batch-size 100

作者: 五好伴学开发团队
日期: 2025-11-15
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# noqa: E402 - 模块导入必须在 sys.path 修改之后
from sqlalchemy import and_, func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from src.core.database import AsyncSessionLocal  # noqa: E402
from src.models.knowledge_graph import MistakeKnowledgePoint  # noqa: E402
from src.models.study import MistakeRecord  # noqa: E402
from src.services.bailian_service import BailianService  # noqa: E402
from src.services.knowledge_graph_service import KnowledgeGraphService  # noqa: E402


class KnowledgeGraphBackfiller:
    """知识图谱历史数据补全工具"""

    def __init__(self, dry_run: bool = False, batch_size: int = 50):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            "total_mistakes": 0,
            "need_backfill": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

    async def get_mistakes_without_kg(
        self, db: AsyncSession
    ) -> List[MistakeRecord]:
        """获取没有知识点关联的历史错题"""
        
        # 查询没有知识点关联的错题
        subquery = (
            select(MistakeKnowledgePoint.mistake_id)
            .distinct()
        )
        
        query = (
            select(MistakeRecord)
            .where(
                and_(
                    MistakeRecord.id.notin_(subquery),
                    MistakeRecord.subject.isnot(None),  # 必须有学科
                )
            )
            .options(selectinload(MistakeRecord.user))
            .order_by(MistakeRecord.created_at.desc())
            .limit(self.batch_size)
        )

        result = await db.execute(query)
        mistakes = result.scalars().all()
        
        return list(mistakes)

    async def backfill_mistake(
        self,
        db: AsyncSession,
        kg_service: KnowledgeGraphService,
        mistake: MistakeRecord,
    ) -> bool:
        """为单个错题补全知识点关联"""
        
        try:
            # 构建 AI 反馈数据
            ai_feedback: Optional[Dict[str, Any]] = None
            
            if mistake.ai_analysis:
                ai_feedback = {
                    "knowledge_points": mistake.ai_analysis.get("knowledge_points", []),
                    "question": mistake.question_content or "",
                    "explanation": mistake.ai_analysis.get("explanation", ""),
                }
            
            # 调用知识图谱服务分析并关联
            print(f"  📊 分析错题: {mistake.id} (用户: {mistake.user_id}, 学科: {mistake.subject})")
            
            if not self.dry_run:
                associations = await kg_service.analyze_and_associate_knowledge_points(
                    mistake_id=UUID(str(mistake.id)),
                    user_id=UUID(str(mistake.user_id)),
                    subject=str(mistake.subject),
                    ocr_text=str(mistake.question_content or mistake.ocr_text or ""),
                    ai_feedback=ai_feedback,
                )
                
                print(f"  ✅ 成功关联 {len(associations)} 个知识点")
            else:
                print("  🔍 [DRY-RUN] 将关联知识点")
            
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            self.stats["failed"] += 1
            return False

    async def regenerate_snapshots(
        self,
        db: AsyncSession,
        kg_service: KnowledgeGraphService,
    ) -> None:
        """为所有有错题的用户重新生成知识图谱快照"""
        
        print("\n📸 开始重新生成知识图谱快照...")
        
        # 获取所有有错题的用户ID
        query = select(MistakeRecord.user_id).distinct()
        result = await db.execute(query)
        user_ids = result.scalars().all()
        
        print(f"📊 找到 {len(user_ids)} 个用户需要生成快照")
        
        success_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                print(f"  📸 生成用户 {user_id} 的快照...")
                
                if not self.dry_run:
                    # 获取用户的学科列表（从该用户的错题中）
                    subject_query = (
                        select(MistakeRecord.subject)
                        .where(MistakeRecord.user_id == user_id)
                        .distinct()
                    )
                    subject_result = await db.execute(subject_query)
                    subjects = subject_result.scalars().all()
                    
                    # 为每个学科生成快照
                    for subject in subjects:
                        await kg_service.create_knowledge_graph_snapshot(
                            user_id=UUID(str(user_id)),
                            subject=str(subject),
                            period_type="backfill",
                            auto_commit=True,
                        )
                    print("  ✅ 完成")
                else:
                    print("  🔍 [DRY-RUN] 将生成快照")
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                failed_count += 1
        
        print(f"\n📊 快照生成完成: 成功 {success_count}, 失败 {failed_count}")

    async def run(self) -> None:
        """执行批量补全任务"""
        
        print("=" * 80)
        print("🚀 知识图谱历史数据批量补全")
        print("=" * 80)
        
        if self.dry_run:
            print("⚠️  DRY-RUN 模式：仅预览，不实际执行")
        else:
            print("✅ 正式执行模式")
        
        print(f"📦 批次大小: {self.batch_size}")
        print("=" * 80)
        
        async with AsyncSessionLocal() as db:
            # 初始化服务
            bailian_service = BailianService()
            kg_service = KnowledgeGraphService(db, bailian_service)
            
            # 1. 统计总数
            print("\n📊 统计数据...")
            
            total_query = select(func.count(MistakeRecord.id))
            result = await db.execute(total_query)
            self.stats["total_mistakes"] = result.scalar() or 0
            
            # 获取需要补全的错题
            mistakes_to_backfill = await self.get_mistakes_without_kg(db)
            self.stats["need_backfill"] = len(mistakes_to_backfill)
            
            print(f"✅ 错题总数: {self.stats['total_mistakes']}")
            print(f"⚠️  需要补全: {self.stats['need_backfill']} (本批次)")
            
            if self.stats["need_backfill"] == 0:
                print("\n🎉 没有需要补全的错题！")
                return
            
            # 2. 批量补全知识点
            print("\n🔄 开始补全知识点...")
            
            for i, mistake in enumerate(mistakes_to_backfill, 1):
                print(f"\n[{i}/{len(mistakes_to_backfill)}]", end=" ")
                
                await self.backfill_mistake(db, kg_service, mistake)
                
                # 每处理10条提交一次
                if not self.dry_run and i % 10 == 0:
                    await db.commit()
                    print(f"  💾 已提交事务 (已处理 {i} 条)")
            
            # 最终提交
            if not self.dry_run:
                await db.commit()
                print("\n💾 最终提交完成")
            
            # 3. 重新生成快照
            if not self.dry_run:
                await self.regenerate_snapshots(db, kg_service)
            else:
                print("\n📸 [DRY-RUN] 跳过快照生成")
        
        # 4. 打印统计报告
        self._print_report()

    def _print_report(self) -> None:
        """打印执行报告"""
        
        print("\n" + "=" * 80)
        print("📊 执行报告")
        print("=" * 80)
        print(f"错题总数:       {self.stats['total_mistakes']}")
        print(f"需要补全:       {self.stats['need_backfill']}")
        print(f"成功:           {self.stats['success']}")
        print(f"失败:           {self.stats['failed']}")
        print(f"跳过:           {self.stats['skipped']}")
        print("=" * 80)
        
        if self.dry_run:
            print("\n⚠️  这是 DRY-RUN 模式的预览结果")
            print("✅ 确认无误后，请去掉 --dry-run 参数正式执行")
        else:
            print("\n✅ 批量补全完成！")
            
            if self.stats["failed"] > 0:
                print(f"⚠️  {self.stats['failed']} 条记录处理失败，请检查日志")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="历史错题知识图谱数据批量补全")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="DRY-RUN 模式（仅预览，不实际执行）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="批次大小（默认: 50）",
    )
    
    args = parser.parse_args()
    
    backfiller = KnowledgeGraphBackfiller(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
    
    await backfiller.run()


if __name__ == "__main__":
    asyncio.run(main())
