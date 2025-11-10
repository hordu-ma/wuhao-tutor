"""add_mistake_fields_for_homework_correction

Revision ID: d733cab41568
Revises: 4e983abcec30
Create Date: 2025-11-10 17:52:19.336771

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d733cab41568"
down_revision: Union[str, Sequence[str], None] = "4e983abcec30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add homework correction fields to mistake_records."""
    # Add the 4 new columns for homework correction
    op.add_column(
        "mistake_records",
        sa.Column(
            "question_number",
            sa.Integer(),
            nullable=True,
            comment="题号(从1开始，用于区分同一作业中的不同题目)",
        ),
    )
    op.add_column(
        "mistake_records",
        sa.Column(
            "is_unanswered",
            sa.Boolean(),
            nullable=False,
            server_default="0",
            comment="是否未作答",
        ),
    )
    op.add_column(
        "mistake_records",
        sa.Column(
            "question_type",
            sa.String(length=50),
            nullable=True,
            comment="题目类型: 选择题/填空题/解答题/判断题/多选题/短答题等",
        ),
    )
    op.add_column(
        "mistake_records",
        sa.Column(
            "error_type",
            sa.String(length=100),
            nullable=True,
            comment="错误类型: 未作答/计算错误/概念错误/理解错误/单位错误/逻辑错误等",
        ),
    )

    # Create composite index for fast lookup by user and question number
    op.create_index(
        "ix_mistake_records_user_question",
        "mistake_records",
        ["user_id", "question_number"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - Remove homework correction fields."""
    # Drop the index first
    op.drop_index("ix_mistake_records_user_question", table_name="mistake_records")

    # Drop the columns in reverse order
    op.drop_column("mistake_records", "error_type")
    op.drop_column("mistake_records", "question_type")
    op.drop_column("mistake_records", "is_unanswered")
    op.drop_column("mistake_records", "question_number")
