"""add formula_cache table

Revision ID: 20251104_formula_cache
Revises: 20251104_upd_at
Create Date: 2025-11-04 14:30:00.000000

添加公式缓存表，用于缓存已渲染的 LaTeX 公式
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251104_formula_cache"
down_revision: Union[str, None] = "20251104_upd_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 formula_cache 表"""

    # 创建 formula_cache 表
    op.create_table(
        "formula_cache",
        # 主键 ID（兼容 SQLite 和 PostgreSQL）
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        # LaTeX 内容的 MD5 哈希（用于快速查找）
        sa.Column("latex_hash", sa.String(32), nullable=False, unique=True, index=True),
        # 原始 LaTeX 内容
        sa.Column("latex_content", sa.Text(), nullable=False),
        # 渲染后的图片 URL
        sa.Column("image_url", sa.String(512), nullable=False),
        # 公式类型（inline 或 block）
        sa.Column(
            "formula_type", sa.String(10), nullable=False, server_default="inline"
        ),
        # 命中次数
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        # 最后访问时间
        sa.Column("last_accessed_at", sa.String(), nullable=True),
        # 额外元数据（JSON 格式）
        sa.Column("metadata", sa.Text(), nullable=True),
        # 时间戳字段
        sa.Column(
            "created_at", sa.String(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.String(), nullable=False, server_default=sa.func.now()
        ),
        # 软删除字段
        sa.Column("deleted_at", sa.String(), nullable=True),
    )

    # 创建索引以优化查询性能
    op.create_index("idx_formula_cache_hash", "formula_cache", ["latex_hash"])
    op.create_index("idx_formula_cache_type", "formula_cache", ["formula_type"])
    op.create_index("idx_formula_cache_hit_count", "formula_cache", ["hit_count"])
    op.create_index("idx_formula_cache_created_at", "formula_cache", ["created_at"])


def downgrade() -> None:
    """删除 formula_cache 表"""

    # 删除索引
    op.drop_index("idx_formula_cache_created_at", table_name="formula_cache")
    op.drop_index("idx_formula_cache_hit_count", table_name="formula_cache")
    op.drop_index("idx_formula_cache_type", table_name="formula_cache")
    op.drop_index("idx_formula_cache_hash", table_name="formula_cache")

    # 删除表
    op.drop_table("formula_cache")
