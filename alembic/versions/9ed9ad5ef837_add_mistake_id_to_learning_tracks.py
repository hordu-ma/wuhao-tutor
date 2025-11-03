"""add_mistake_id_to_learning_tracks

Revision ID: 9ed9ad5ef837
Revises: 69fa4d4475a5
Create Date: 2025-11-03 15:44:28.879065

添加 mistake_id 字段到 knowledge_point_learning_tracks 表
用于记录学习轨迹关联的错题
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ed9ad5ef837"
down_revision: Union[str, Sequence[str], None] = "69fa4d4475a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 mistake_id 字段"""
    # 添加 mistake_id 列
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "mistake_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="关联的错题ID（如有）",
        ),
    )

    # 添加外键约束
    op.create_foreign_key(
        "fk_kplt_mistake",
        "knowledge_point_learning_tracks",
        "mistake_records",
        ["mistake_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 添加索引以提升查询性能
    op.create_index(
        "idx_kplt_mistake", "knowledge_point_learning_tracks", ["mistake_id"]
    )


def downgrade() -> None:
    """移除 mistake_id 字段"""
    op.drop_index("idx_kplt_mistake", table_name="knowledge_point_learning_tracks")
    op.drop_constraint(
        "fk_kplt_mistake", "knowledge_point_learning_tracks", type_="foreignkey"
    )
    op.drop_column("knowledge_point_learning_tracks", "mistake_id")
