#!/usr/bin/env python3
"""
错题知识点关联数据回填脚本

功能：
1. 读取所有有 ai_feedback 但无知识点关联的错题
2. 从 ai_feedback 中提取知识点
3. 创建知识点关联记录
4. 更新知识点掌握度

使用方法：
    python scripts/backfill_knowledge_associations.py [--dry-run] [--limit=100]

参数：
    --dry-run: 只显示将要处理的数据，不实际写入数据库
    --limit: 限制处理的错题数量（用于测试）
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import AsyncSessionLocal
from src.core.logging import configure_logging, get_logger
from src.models.study import MistakeRecord
from src.services.knowledge_graph_service import KnowledgeGraphService

# 配置日志
configure_logging()
logger = get_logger(__name__)
settings = get_settings()


async def extract_knowledge_points_from_feedback(
    ai_feedback: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    从 AI feedback 中提取知识点
    
    Args:
        ai_feedback: AI 反馈数据
        
    Returns:
        知识点列表
    """
    knowledge_points = []
    
    # 尝试从 knowledge_points 字段获取
    if "knowledge_points" in ai_feedback and ai_feedback["knowledge_points"]:
        kps = ai_feedback["knowledge_points"]
        
        # 处理不同格式
        if isinstance(kps, list):
            for kp in kps:
                if isinstance(kp, dict):
                    knowledge_points.append(kp)
                elif isinstance(kp, str):
                    knowledge_points.append({"name": kp, "relevance": 0.7})
        elif isinstance(kps, str):
            # 单个知识点字符串
            knowledge_points.append({"name": kps, "relevance": 0.7})
    
    # 从其他可能的字段提取
    for field in ["涉及知识点", "知识点", "related_knowledge"]:
        if field in ai_feedback and ai_feedback[field]:
            items = ai_feedback[field]
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        knowledge_points.append({"name": item, "relevance": 0.6})
    
    return knowledge_points


async def backfill_single_mistake(
    session: AsyncSession,
    mistake: MistakeRecord,
    kg_service: KnowledgeGraphService,
    dry_run: bool = False,
) -> bool:
    """
    为单个错题回填知识点关联
    
    Args:
        session: 数据库会话
        mistake: 错题记录
        kg_service: 知识图谱服务
        dry_run: 是否为干运行（不实际写入）
        
    Returns:
        是否成功处理
    """
    try:
        mistake_id = mistake.id
        user_id = mistake.user_id
        subject = mistake.subject
        
        # 解析 ai_feedback
        ai_feedback = {}
        if mistake.ai_feedback:
            try:
                if isinstance(mistake.ai_feedback, str):
                    ai_feedback = json.loads(mistake.ai_feedback)
                elif isinstance(mistake.ai_feedback, dict):
                    ai_feedback = mistake.ai_feedback
            except json.JSONDecodeError:
                logger.warning(f"错题 {mistake_id} 的 ai_feedback 无法解析")
                return False
        
        # 提取知识点
        knowledge_points = await extract_knowledge_points_from_feedback(ai_feedback)
        
        if not knowledge_points:
            logger.info(f"错题 {mistake_id} 没有提取到知识点")
            return False
        
        logger.info(
            f"错题 {mistake_id} 提取到 {len(knowledge_points)} 个知识点: "
            f"{[kp.get('name') for kp in knowledge_points]}"
        )
        
        if dry_run:
            logger.info(f"[DRY-RUN] 将为错题 {mistake_id} 创建 {len(knowledge_points)} 个关联")
            return True
        
        # 调用知识图谱服务创建关联
        associations = await kg_service.analyze_and_associate_knowledge_points(
            mistake_id=UUID(str(mistake_id)),
            user_id=UUID(str(user_id)),
            subject=subject or "数学",
            ocr_text=mistake.ocr_text,
            ai_feedback=ai_feedback,
        )
        
        if associations:
            logger.info(
                f"✅ 成功为错题 {mistake_id} 创建 {len(associations)} 个知识点关联"
            )
            return True
        else:
            logger.warning(f"⚠️ 错题 {mistake_id} 知识点关联创建失败")
            return False
            
    except Exception as e:
        logger.error(f"处理错题 {mistake_id} 失败: {e}", exc_info=True)
        return False


async def main(dry_run: bool = False, limit: Optional[int] = None):
    """
    主函数
    
    Args:
        dry_run: 是否为干运行
        limit: 限制处理的错题数量
    """
    logger.info("=" * 60)
    logger.info("错题知识点关联数据回填脚本")
    logger.info(f"模式: {'干运行（不写入数据库）' if dry_run else '正式运行'}")
    logger.info(f"限制: {limit if limit else '无限制'}")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # 查询所有有 ai_feedback 但无知识点关联的错题
            from src.models.knowledge_graph import MistakeKnowledgePoint
            
            # 子查询：已有关联的错题ID
            subquery = select(MistakeKnowledgePoint.mistake_id).distinct()
            
            # 主查询：未关联的错题
            stmt = (
                select(MistakeRecord)
                .where(
                    and_(
                        MistakeRecord.ai_feedback.is_not(None),
                        MistakeRecord.id.notin_(subquery),
                    )
                )
                .order_by(MistakeRecord.created_at.desc())
            )
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            mistakes = result.scalars().all()
            
            total_count = len(mistakes)
            logger.info(f"找到 {total_count} 条需要处理的错题记录")
            
            if total_count == 0:
                logger.info("✅ 没有需要处理的数据，退出")
                return
            
            # 初始化知识图谱服务
            kg_service = KnowledgeGraphService(session)
            
            # 统计
            success_count = 0
            failed_count = 0
            skipped_count = 0
            
            # 逐条处理
            for index, mistake in enumerate(mistakes, 1):
                logger.info(f"[{index}/{total_count}] 处理错题 {mistake.id}")
                
                success = await backfill_single_mistake(
                    session, mistake, kg_service, dry_run
                )
                
                if success:
                    success_count += 1
                else:
                    skipped_count += 1
                
                # 每处理10条提交一次（非干运行模式）
                if not dry_run and index % 10 == 0:
                    await session.commit()
                    logger.info(f"已提交前 {index} 条数据")
            
            # 最后提交剩余数据
            if not dry_run:
                await session.commit()
                logger.info("✅ 所有数据已提交")
            
            # 打印统计信息
            logger.info("=" * 60)
            logger.info("处理完成！统计信息：")
            logger.info(f"  总计: {total_count}")
            logger.info(f"  成功: {success_count}")
            logger.info(f"  跳过: {skipped_count}")
            logger.info(f"  失败: {failed_count}")
            logger.info("=" * 60)
            
            if dry_run:
                logger.info("💡 这是干运行模式，数据未实际写入数据库")
                logger.info("💡 如需正式运行，请去掉 --dry-run 参数")
            
        except Exception as e:
            logger.error(f"脚本执行失败: {e}", exc_info=True)
            if not dry_run:
                await session.rollback()
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="错题知识点关联数据回填脚本")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式，不实际写入数据库",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的错题数量（用于测试）",
    )
    
    args = parser.parse_args()
    
    # 运行脚本
    asyncio.run(main(dry_run=args.dry_run, limit=args.limit))
