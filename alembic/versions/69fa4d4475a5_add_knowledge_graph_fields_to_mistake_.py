"""add_knowledge_graph_fields_to_mistake_knowledge_points

Revision ID: 69fa4d4475a5
Revises: 20251103_kg_tables
Create Date: 2025-11-03 14:35:52.794035

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "69fa4d4475a5"
down_revision: Union[str, Sequence[str], None] = "20251103_kg_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 AI 分析结果字段
    op.add_column(
        "mistake_knowledge_points",
        sa.Column(
            "ai_diagnosis",
            sa.JSON(),
            nullable=True,
            comment="AI诊断结果（包含薄弱点、改进建议等）",
        ),
    )

    op.add_column(
        "mistake_knowledge_points",
        sa.Column(
            "improvement_suggestions", sa.JSON(), nullable=True, comment="改进建议列表"
        ),
    )

    # 添加学习状态字段
    op.add_column(
        "mistake_knowledge_points",
        sa.Column(
            "mastered_after_review",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="复习后是否已掌握",
        ),
    )

    op.add_column(
        "mistake_knowledge_points",
        sa.Column(
            "review_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="针对此知识点的复习次数",
        ),
    )

    op.add_column(
        "mistake_knowledge_points",
        sa.Column(
            "last_review_result",
            sa.String(20),
            nullable=True,
            comment="最后一次复习结果（correct/incorrect/partial）",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 删除添加的字段
    op.drop_column("mistake_knowledge_points", "last_review_result")
    op.drop_column("mistake_knowledge_points", "review_count")
    op.drop_column("mistake_knowledge_points", "mastered_after_review")
    op.drop_column("mistake_knowledge_points", "improvement_suggestions")
    op.drop_column("mistake_knowledge_points", "ai_diagnosis")
