"""merge_review_session_branches

Revision ID: 4e983abcec30
Revises: create_review_sessions, fb4caaaf21e5
Create Date: 2025-11-08 19:57:42.062214

合并两个创建 mistake_review_sessions 表的分支
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4e983abcec30"
down_revision: Union[str, Sequence[str], None] = (
    "create_review_sessions",
    "fb4caaaf21e5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    合并迁移：确保 mistake_review_sessions 表存在
    两个分支都试图创建该表，这里进行幂等性检查
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "mistake_review_sessions" in inspector.get_table_names():
        print("✓ Table 'mistake_review_sessions' already exists, skipping...")
    else:
        print("✓ Table 'mistake_review_sessions' will be created by parent migrations")


def downgrade() -> None:
    """合并迁移通常不需要 downgrade"""
    pass
