"""
知识图谱定时任务
实现知识图谱快照的定时生成和维护

作者: AI Agent
创建时间: 2025-11-04
版本: v1.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import and_, distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.core.logging import configure_logging, get_logger
from src.models.study import KnowledgeMastery, MistakeRecord
from src.services.knowledge_graph_service import KnowledgeGraphService

# 配置日志
configure_logging()
logger = get_logger(__name__)


async def generate_daily_snapshots() -> dict:
    """
    每日凌晨3点生成知识图谱快照
    
    工作流程:
    1. 查询所有有错题记录的用户
    2. 为每个用户的每个学科生成快照
    3. 记录成功和失败统计
    4. 清理30天前的旧快照
    
    Returns:
        执行统计信息
    """
    logger.info("=" * 60)
    logger.info("🚀 开始执行知识图谱快照定时任务")
    logger.info(f"⏰ 执行时间: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    stats = {
        "total_users": 0,
        "total_snapshots": 0,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "errors": []
    }
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 查询有错题记录的用户和学科
            users_subjects = await _get_users_with_mistakes(db)
            stats["total_users"] = len(set(user_id for user_id, _ in users_subjects))
            stats["total_snapshots"] = len(users_subjects)
            
            logger.info(
                f"📊 找到 {stats['total_users']} 个用户, "
                f"共 {stats['total_snapshots']} 个学科需要生成快照"
            )
            
            if not users_subjects:
                logger.info("✅ 没有需要处理的数据，退出")
                return stats
            
            # 2. 为每个用户的每个学科生成快照
            for user_id, subject in users_subjects:
                try:
                    # 创建新的数据库会话（避免单个失败影响整体）
                    async with AsyncSessionLocal() as snapshot_db:
                        kg_service = KnowledgeGraphService(snapshot_db)
                        
                        # 生成快照
                        snapshot = await kg_service.create_knowledge_graph_snapshot(
                            user_id=UUID(user_id),
                            subject=subject,
                            period_type="daily"
                        )
                        
                        await snapshot_db.commit()
                        
                        stats["success_count"] += 1
                        logger.info(
                            f"✅ 成功生成快照: user={user_id}, subject={subject}, "
                            f"snapshot_id={snapshot.id}"
                        )
                
                except Exception as e:
                    stats["failed_count"] += 1
                    error_msg = f"user={user_id}, subject={subject}, error={str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error(f"❌ 生成快照失败: {error_msg}", exc_info=True)
            
            # 3. 清理30天前的旧快照
            try:
                deleted_count = await _cleanup_old_snapshots(db, days=30)
                logger.info(f"🗑️ 清理了 {deleted_count} 个过期快照(30天前)")
            except Exception as e:
                logger.error(f"清理旧快照失败: {e}", exc_info=True)
            
            # 4. 输出统计信息
            logger.info("=" * 60)
            logger.info("📈 任务执行完成! 统计信息:")
            logger.info(f"  总用户数: {stats['total_users']}")
            logger.info(f"  总快照数: {stats['total_snapshots']}")
            logger.info(f"  成功: {stats['success_count']}")
            logger.info(f"  失败: {stats['failed_count']}")
            logger.info(f"  跳过: {stats['skipped_count']}")
            
            if stats["errors"]:
                logger.warning(f"  错误详情: {stats['errors'][:5]}")  # 只显示前5个
            
            logger.info("=" * 60)
            
            return stats
            
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}", exc_info=True)
            raise


async def _get_users_with_mistakes(db: AsyncSession) -> List[Tuple[str, str]]:
    """
    查询有错题记录的用户和学科组合
    
    Args:
        db: 数据库会话
        
    Returns:
        [(user_id, subject), ...] 列表
    """
    try:
        # 查询所有有错题记录的用户和学科组合
        # 只查询最近7天有活动的
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        stmt = (
            select(MistakeRecord.user_id, MistakeRecord.subject)
            .where(MistakeRecord.created_at >= seven_days_ago)
            .distinct()
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # 转换为 (user_id, subject) 元组列表
        users_subjects = [(str(row[0]), str(row[1])) for row in rows]
        
        logger.debug(f"查询到 {len(users_subjects)} 个用户-学科组合")
        return users_subjects
        
    except Exception as e:
        logger.error(f"查询用户错题记录失败: {e}", exc_info=True)
        return []


async def _cleanup_old_snapshots(db: AsyncSession, days: int = 30) -> int:
    """
    清理过期的快照记录
    
    Args:
        db: 数据库会话
        days: 保留天数（默认30天）
        
    Returns:
        删除的快照数量
    """
    from src.models.knowledge_graph import UserKnowledgeGraphSnapshot
    from src.repositories.base_repository import BaseRepository
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 查询过期快照
        stmt = select(UserKnowledgeGraphSnapshot).where(
            UserKnowledgeGraphSnapshot.created_at < cutoff_date
        )
        result = await db.execute(stmt)
        old_snapshots = result.scalars().all()
        
        # 删除
        snapshot_repo = BaseRepository(UserKnowledgeGraphSnapshot, db)
        deleted_count = 0
        
        for snapshot in old_snapshots:
            snapshot_id = getattr(snapshot, "id", None)
            if snapshot_id:
                await snapshot_repo.delete(str(snapshot_id))
                deleted_count += 1
        
        await db.commit()
        
        return deleted_count
        
    except Exception as e:
        await db.rollback()
        logger.error(f"清理过期快照失败: {e}", exc_info=True)
        return 0


async def generate_snapshot_for_user(
    user_id: str, 
    subject: str
) -> dict:
    """
    为特定用户生成快照（手动触发）
    
    Args:
        user_id: 用户ID
        subject: 学科
        
    Returns:
        执行结果
    """
    logger.info(f"🎯 手动生成快照: user={user_id}, subject={subject}")
    
    result = {
        "success": False,
        "snapshot_id": None,
        "error": None
    }
    
    async with AsyncSessionLocal() as db:
        try:
            kg_service = KnowledgeGraphService(db)
            
            snapshot = await kg_service.create_knowledge_graph_snapshot(
                user_id=UUID(user_id),
                subject=subject,
                period_type="manual"
            )
            
            await db.commit()
            
            result["success"] = True
            result["snapshot_id"] = str(snapshot.id)
            
            logger.info(f"✅ 手动快照生成成功: snapshot_id={snapshot.id}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ 手动快照生成失败: {e}", exc_info=True)
    
    return result


# Celery 任务包装（如果使用 Celery）
try:
    from celery import shared_task
    
    @shared_task(name="knowledge_graph.generate_daily_snapshots")
    def celery_generate_daily_snapshots():
        """Celery 任务包装"""
        return asyncio.run(generate_daily_snapshots())
    
    @shared_task(name="knowledge_graph.generate_snapshot_for_user")
    def celery_generate_snapshot_for_user(user_id: str, subject: str):
        """Celery 任务包装 - 手动触发"""
        return asyncio.run(generate_snapshot_for_user(user_id, subject))
        
except ImportError:
    logger.warning("Celery 未安装，跳过 Celery 任务定义")


# 命令行执行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="知识图谱快照任务")
    parser.add_argument(
        "--user-id",
        type=str,
        help="指定用户ID（手动生成快照）"
    )
    parser.add_argument(
        "--subject",
        type=str,
        help="指定学科（手动生成快照）"
    )
    
    args = parser.parse_args()
    
    if args.user_id and args.subject:
        # 手动生成单个用户快照
        result = asyncio.run(generate_snapshot_for_user(args.user_id, args.subject))
        print(f"执行结果: {result}")
    else:
        # 批量生成快照
        stats = asyncio.run(generate_daily_snapshots())
        print(f"执行统计: {stats}")
