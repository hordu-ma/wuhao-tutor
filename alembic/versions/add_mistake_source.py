"""
为 MistakeRecord 添加来源字段

Revision ID: 20251020_add_mistake_source_fields
Revises: 20251012_add_mistake_reviews
Create Date: 2025-10-20

说明：
- 添加错题来源字段（learning/homework/manual）
- 添加关联的Question ID字段
- 添加学生答案和正确答案字段
- 为来源字段创建索引
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_mistake_source"
down_revision: Union[str, Sequence[str], None] = "20251012_add_mistake_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加错题来源相关字段"""

    # 获取数据库连接
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 获取 mistake_records 表的现有列
    existing_columns = [col["name"] for col in inspector.get_columns("mistake_records")]

    # 添加来源字段（如果不存在）
    if "source" not in existing_columns:
        op.add_column(
            "mistake_records",
            sa.Column(
                "source",
                sa.String(20),
                nullable=True,
                comment="错题来源：learning/homework/manual",
            ),
        )

    # 添加关联的Question ID字段（如果不存在）
    if "source_question_id" not in existing_columns:
        op.add_column(
            "mistake_records",
            sa.Column(
                "source_question_id",
                sa.String(36),
                nullable=True,
                comment="关联的Question ID（从学习问答创建）",
            ),
        )

    # 添加学生答案字段（如果不存在）
    if "student_answer" not in existing_columns:
        op.add_column(
            "mistake_records",
            sa.Column("student_answer", sa.Text, nullable=True, comment="学生答案"),
        )

    # 添加正确答案字段（如果不存在）
    if "correct_answer" not in existing_columns:
        op.add_column(
            "mistake_records",
            sa.Column("correct_answer", sa.Text, nullable=True, comment="正确答案"),
        )

    # 为已存在的记录设置默认值（只有 source 字段存在且需要更新时）
    if "source" in existing_columns:
        op.execute("UPDATE mistake_records SET source = 'manual' WHERE source IS NULL")

        # 设置source字段为非空（有默认值后）
        op.alter_column(
            "mistake_records", "source", nullable=False, server_default="manual"
        )

    # 创建索引（如果不存在）
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("mistake_records")]

    if "idx_mistake_source" not in existing_indexes:
        op.create_index(
            "idx_mistake_source", "mistake_records", ["source", "source_question_id"]
        )

    if "idx_mistake_source_question_id" not in existing_indexes:
        op.create_index(
            "idx_mistake_source_question_id", "mistake_records", ["source_question_id"]
        )


def downgrade() -> None:
    """移除错题来源相关字段"""

    # 删除索引
    op.drop_index("idx_mistake_source_question_id", table_name="mistake_records")
    op.drop_index("idx_mistake_source", table_name="mistake_records")

    # 删除列
    op.drop_column("mistake_records", "correct_answer")
    op.drop_column("mistake_records", "student_answer")
    op.drop_column("mistake_records", "source_question_id")
    op.drop_column("mistake_records", "source")
