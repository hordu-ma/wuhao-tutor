"""add updated_at to snapshots

Revision ID: 20251104_upd_at
Revises: 3b5dff6e22e1
Create Date: 2025-11-04 12:15:00.000000

修复 user_knowledge_graph_snapshots 表缺少 updated_at 字段的问题
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251104_upd_at"
down_revision: Union[str, None] = "3b5dff6e22e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 updated_at 字段到 user_knowledge_graph_snapshots 表"""

    # 添加 updated_at 列
    op.add_column(
        "user_knowledge_graph_snapshots",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
    )

    print("✅ 已添加 updated_at 字段到 user_knowledge_graph_snapshots 表")


def downgrade() -> None:
    """回滚：删除 updated_at 字段"""

    op.drop_column("user_knowledge_graph_snapshots", "updated_at")

    print("⬅️ 已删除 updated_at 字段")
