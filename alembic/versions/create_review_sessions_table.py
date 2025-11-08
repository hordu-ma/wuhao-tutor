"""create review sessions table

Revision ID: create_review_sessions
Revises: fb4caaaf21e5
Create Date: 2025-11-08 18:35:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "create_review_sessions"
down_revision: Union[str, Sequence[str], None] = "20251104_formula_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """只创建 mistake_review_sessions 表，不修改任何现有表"""
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "mistake_review_sessions" in inspector.get_table_names():
        print("Table mistake_review_sessions already exists, skipping...")
        return

    op.create_table(
        "mistake_review_sessions",
        sa.Column("mistake_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("current_stage", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("id", UUID(as_uuid=True), nullable=False, comment="主键ID"),
        sa.Column(
            "created_at", sa.String(length=50), nullable=False, comment="创建时间"
        ),
        sa.Column(
            "updated_at", sa.String(length=50), nullable=False, comment="更新时间"
        ),
        sa.ForeignKeyConstraint(
            ["mistake_id"],
            ["mistake_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_mistake_review_sessions_status"),
        "mistake_review_sessions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """删除 mistake_review_sessions 表"""
    op.drop_index(
        op.f("ix_mistake_review_sessions_status"), table_name="mistake_review_sessions"
    )
    op.drop_table("mistake_review_sessions")
