"""add_knowledge_mastery_index_for_subject_query

Revision ID: 4b0c11bd46a4
Revises: d733cab41568
Create Date: 2025-11-12 18:36:08.385422

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b0c11bd46a4"
down_revision: Union[str, Sequence[str], None] = "d733cab41568"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - 添加联合索引优化按学科查询知识图谱的性能."""
    # 创建联合索引: (user_id, subject, mastery_level)
    # 用于优化 get_subject_knowledge_graph 查询
    op.create_index(
        "idx_knowledge_mastery_user_subject_mastery",
        "knowledge_mastery",
        ["user_id", "subject", "mastery_level"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - 移除联合索引."""
    op.drop_index(
        "idx_knowledge_mastery_user_subject_mastery", table_name="knowledge_mastery"
    )
