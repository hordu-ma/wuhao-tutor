"""
公式缓存仓储
负责公式缓存的数据访问操作
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.formula_cache import FormulaCacheModel
from src.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


class FormulaCacheRepository(BaseRepository[FormulaCacheModel]):
    """公式缓存仓储类"""

    def __init__(self, db: AsyncSession):
        """初始化仓储"""
        super().__init__(FormulaCacheModel, db)

    async def get_by_hash(self, latex_hash: str) -> Optional[FormulaCacheModel]:
        """
        根据哈希值获取缓存

        Args:
            latex_hash: LaTeX内容的MD5哈希

        Returns:
            缓存记录或None
        """
        try:
            stmt = select(FormulaCacheModel).where(
                FormulaCacheModel.latex_hash == latex_hash
            )
            result = await self.db.execute(stmt)
            cache = result.scalar_one_or_none()

            if cache:
                logger.debug(f"Cache hit for hash: {latex_hash[:8]}...")
                # 更新访问时间和命中次数
                await self.increment_hit_count(latex_hash)
            else:
                logger.debug(f"Cache miss for hash: {latex_hash[:8]}...")

            return cache

        except Exception as e:
            logger.error(f"Error getting cache by hash {latex_hash}: {e}")
            return None

    async def increment_hit_count(self, latex_hash: str) -> None:
        """
        增加缓存命中次数

        Args:
            latex_hash: LaTeX内容的MD5哈希
        """
        try:
            stmt = (
                update(FormulaCacheModel)
                .where(FormulaCacheModel.latex_hash == latex_hash)
                .values(
                    hit_count=FormulaCacheModel.hit_count + 1,
                    last_accessed_at=func.now(),
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to increment hit count for {latex_hash}: {e}")
            # 不影响主流程，静默失败
            pass

    async def create_cache(
        self,
        latex_hash: str,
        latex_content: str,
        image_url: str,
        formula_type: str = "inline",
        metadata: Optional[str] = None,
    ) -> Optional[FormulaCacheModel]:
        """
        创建新的缓存记录

        Args:
            latex_hash: LaTeX内容的MD5哈希
            latex_content: 原始LaTeX内容
            image_url: 渲染后的图片URL
            formula_type: 公式类型（inline或block）
            metadata: 额外元数据（JSON字符串）

        Returns:
            创建的缓存记录或None（如果失败）
        """
        try:
            # 检查是否已存在
            existing = await self.get_by_hash(latex_hash)
            if existing:
                logger.debug(f"Cache already exists for hash: {latex_hash[:8]}...")
                return existing

            # 创建新记录
            cache_data = {
                "latex_hash": latex_hash,
                "latex_content": latex_content,
                "image_url": image_url,
                "formula_type": formula_type,
                "hit_count": 0,
                "last_accessed_at": datetime.now().isoformat(),
                "metadata": metadata,
            }

            cache = await self.create(cache_data)
            logger.info(f"Created cache for formula: {latex_hash[:8]}...")

            return cache

        except Exception as e:
            logger.error(f"Error creating cache for {latex_hash}: {e}")
            return None

    async def get_hot_formulas(self, limit: int = 100) -> List[FormulaCacheModel]:
        """
        获取热门公式（按命中次数排序）

        Args:
            limit: 返回数量限制

        Returns:
            热门公式列表
        """
        try:
            stmt = (
                select(FormulaCacheModel)
                .order_by(desc(FormulaCacheModel.hit_count))
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting hot formulas: {e}")
            return []

    async def cleanup_old_cache(self, days: int = 90) -> int:
        """
        清理旧缓存（用于定期维护）

        Args:
            days: 保留最近N天的缓存

        Returns:
            删除的记录数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = (
                select(func.count())
                .select_from(FormulaCacheModel)
                .where(
                    FormulaCacheModel.last_accessed_at < cutoff_date.isoformat(),
                    FormulaCacheModel.hit_count < 5,  # 只删除低频访问的
                )
            )
            result = await self.db.execute(stmt)
            count = result.scalar()

            if count and count > 0:
                logger.info(f"Would delete {count} old cache records (dry run)")
                # 实际删除逻辑可以在需要时启用
                # delete_stmt = delete(FormulaCacheModel).where(...)
                # await self.db.execute(delete_stmt)
                # await self.db.commit()

            return count or 0

        except Exception as e:
            logger.error(f"Error cleaning up old cache: {e}")
            return 0

    async def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            # 总记录数
            total_stmt = select(func.count()).select_from(FormulaCacheModel)
            total_result = await self.db.execute(total_stmt)
            total_count = total_result.scalar() or 0

            # 总命中次数
            hits_stmt = select(func.sum(FormulaCacheModel.hit_count))
            hits_result = await self.db.execute(hits_stmt)
            total_hits = hits_result.scalar() or 0

            # 按类型分组
            type_stmt = select(
                FormulaCacheModel.formula_type, func.count().label("count")
            ).group_by(FormulaCacheModel.formula_type)
            type_result = await self.db.execute(type_stmt)
            type_counts = {row[0]: row[1] for row in type_result.all()}

            return {
                "total_cached": total_count,
                "total_hits": total_hits,
                "avg_hits_per_formula": (
                    round(total_hits / total_count, 2) if total_count > 0 else 0
                ),
                "by_type": type_counts,
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "total_cached": 0,
                "total_hits": 0,
                "avg_hits_per_formula": 0,
                "by_type": {},
            }
