"""
数学公式缓存模型
用于缓存已渲染的LaTeX公式，提高渲染性能
"""

from datetime import datetime

from sqlalchemy import Column, Index, Integer, String, Text
from sqlalchemy.sql import func

from src.models.base import BaseModel


class FormulaCacheModel(BaseModel):
    """
    公式缓存模型

    存储已渲染的LaTeX公式信息，避免重复渲染
    """

    __tablename__ = "formula_cache"

    # 公式内容的MD5哈希值（用于快速查找）
    latex_hash = Column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="LaTeX内容的MD5哈希",
    )

    # 原始LaTeX内容（用于调试和验证）
    latex_content = Column(Text, nullable=False, comment="原始LaTeX公式内容")

    # 渲染后的图片URL（OSS或CDN地址）
    image_url = Column(String(512), nullable=False, comment="渲染后的图片URL")

    # 公式类型：inline（行内）或 block（块级）
    formula_type = Column(
        String(10), nullable=False, default="inline", comment="公式类型：inline或block"
    )

    # 命中次数（用于统计热门公式）
    hit_count = Column(Integer, nullable=False, default=0, comment="缓存命中次数")

    # 最后访问时间（用于缓存淘汰策略）
    last_accessed_at = Column(
        "last_accessed_at",
        String,  # SQLite兼容性
        nullable=True,
        server_default=func.now(),
        comment="最后访问时间",
    )

    # 额外元数据（JSON格式，存储渲染参数等）
    metadata = Column(Text, nullable=True, comment="额外元数据（JSON格式）")

    # 创建索引以优化查询性能
    __table_args__ = (
        Index("idx_formula_cache_hash", "latex_hash"),
        Index("idx_formula_cache_type", "formula_type"),
        Index("idx_formula_cache_hit_count", "hit_count"),
    )

    def __repr__(self):
        """字符串表示"""
        return f"<FormulaCache(hash={self.latex_hash[:8]}, type={self.formula_type}, hits={self.hit_count})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "latex_hash": self.latex_hash,
            "latex_content": self.latex_content,
            "image_url": self.image_url,
            "formula_type": self.formula_type,
            "hit_count": self.hit_count,
            "last_accessed_at": self.last_accessed_at,
            "created_at": str(self.created_at) if hasattr(self, "created_at") else None,
            "updated_at": str(self.updated_at) if hasattr(self, "updated_at") else None,
        }
