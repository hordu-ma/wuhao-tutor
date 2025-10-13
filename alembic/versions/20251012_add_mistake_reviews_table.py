"""add mistake reviews table and optimize indexes

Revision ID: 20251012_add_mistake_reviews
Revises: 530d40eea860
Create Date: 2025-10-12 12:38:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from src.core.config import get_settings

# revision identifiers, used by Alembic.
revision: str = "20251012_add_mistake_reviews"
down_revision: Union[str, Sequence[str], None] = "530d40eea860"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 获取配置以确定数据库类型
settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI and "sqlite" in str(
    settings.SQLALCHEMY_DATABASE_URI
)


def upgrade() -> None:
    """Upgrade schema - Create mistake_reviews table and optimize indexes."""

    # 1. 创建 mistake_reviews 表
    if is_sqlite:
        op.create_table(
            "mistake_reviews",
            sa.Column(
                "mistake_id",
                sa.String(length=36),
                sa.ForeignKey("mistake_records.id", ondelete="CASCADE"),
                nullable=False,
                comment="错题记录ID",
            ),
            sa.Column(
                "user_id",
                sa.String(length=36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID（冗余，便于查询）",
            ),
            sa.Column(
                "review_date",
                sa.String(length=50),
                nullable=False,
                comment="复习时间",
            ),
            sa.Column(
                "review_result",
                sa.String(length=20),
                nullable=False,
                comment="复习结果: correct | incorrect | partial",
            ),
            sa.Column("time_spent", sa.Integer(), nullable=True, comment="耗时（秒）"),
            sa.Column(
                "confidence_level",
                sa.Integer(),
                nullable=False,
                server_default="3",
                comment="信心等级 1-5",
            ),
            sa.Column(
                "mastery_level",
                sa.Numeric(precision=3, scale=2),
                nullable=False,
                server_default="0.0",
                comment="掌握度 0.0-1.0",
            ),
            sa.Column(
                "next_review_date",
                sa.String(length=50),
                nullable=True,
                comment="计算的下次复习时间",
            ),
            sa.Column(
                "interval_days", sa.Integer(), nullable=True, comment="复习间隔天数"
            ),
            sa.Column(
                "user_answer", sa.Text(), nullable=True, comment="用户答案（可选）"
            ),
            sa.Column("notes", sa.Text(), nullable=True, comment="复习笔记（可选）"),
            sa.Column(
                "review_method",
                sa.String(length=20),
                nullable=False,
                server_default="manual",
                comment="复习方式: manual | scheduled | random",
            ),
            sa.Column(
                "id",
                sa.String(length=36),
                nullable=False,
                primary_key=True,
                unique=True,
                comment="主键ID",
            ),
            sa.Column(
                "created_at",
                sa.String(length=50),
                nullable=False,
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.String(length=50),
                nullable=False,
                comment="更新时间",
            ),
        )
    else:
        # PostgreSQL版本
        op.create_table(
            "mistake_reviews",
            sa.Column(
                "mistake_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("mistake_records.id", ondelete="CASCADE"),
                nullable=False,
                comment="错题记录ID",
            ),
            sa.Column(
                "user_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                comment="用户ID（冗余，便于查询）",
            ),
            sa.Column(
                "review_date",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                comment="复习时间",
            ),
            sa.Column(
                "review_result",
                sa.String(length=20),
                nullable=False,
                comment="复习结果: correct | incorrect | partial",
            ),
            sa.Column("time_spent", sa.Integer(), nullable=True, comment="耗时（秒）"),
            sa.Column(
                "confidence_level",
                sa.Integer(),
                nullable=False,
                server_default="3",
                comment="信心等级 1-5",
            ),
            sa.Column(
                "mastery_level",
                sa.Numeric(precision=3, scale=2),
                nullable=False,
                server_default="0.0",
                comment="掌握度 0.0-1.0",
            ),
            sa.Column(
                "next_review_date",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="计算的下次复习时间",
            ),
            sa.Column(
                "interval_days", sa.Integer(), nullable=True, comment="复习间隔天数"
            ),
            sa.Column(
                "user_answer", sa.Text(), nullable=True, comment="用户答案（可选）"
            ),
            sa.Column("notes", sa.Text(), nullable=True, comment="复习笔记（可选）"),
            sa.Column(
                "review_method",
                sa.String(length=20),
                nullable=False,
                server_default="manual",
                comment="复习方式: manual | scheduled | random",
            ),
            sa.Column(
                "id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                nullable=False,
                primary_key=True,
                unique=True,
                comment="主键ID",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                comment="创建时间",
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
                comment="更新时间",
            ),
        )

    # 2. 添加检查约束
    op.create_check_constraint(
        "ck_review_result",
        "mistake_reviews",
        "review_result IN ('correct', 'incorrect', 'partial')",
    )

    op.create_check_constraint(
        "ck_confidence_level",
        "mistake_reviews",
        "confidence_level >= 1 AND confidence_level <= 5",
    )

    op.create_check_constraint(
        "ck_mastery_level",
        "mistake_reviews",
        "mastery_level >= 0.0 AND mastery_level <= 1.0",
    )

    # 3. 创建 mistake_reviews 表索引
    op.create_index(
        "idx_mistake_reviews_user_review",
        "mistake_reviews",
        ["user_id", sa.text("review_date DESC")],
    )

    op.create_index(
        "idx_mistake_reviews_mistake",
        "mistake_reviews",
        ["mistake_id", sa.text("review_date DESC")],
    )

    # 部分索引（仅在有下次复习时间时创建索引）
    if is_sqlite:
        # SQLite 支持部分索引
        op.execute(
            "CREATE INDEX idx_mistake_reviews_next_review "
            "ON mistake_reviews(user_id, next_review_date) "
            "WHERE next_review_date IS NOT NULL"
        )
    else:
        # PostgreSQL 支持部分索引
        op.execute(
            "CREATE INDEX idx_mistake_reviews_next_review "
            "ON mistake_reviews(user_id, next_review_date) "
            "WHERE next_review_date IS NOT NULL"
        )

    # 4. 为 mistake_records 表添加新字段
    if is_sqlite:
        op.add_column(
            "mistake_records",
            sa.Column(
                "total_review_count",
                sa.Integer(),
                server_default="0",
                nullable=False,
                comment="总复习次数",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "average_mastery",
                sa.Numeric(precision=3, scale=2),
                server_default="0.0",
                nullable=False,
                comment="平均掌握度",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "last_mastery_update",
                sa.String(length=50),
                nullable=True,
                comment="最后掌握度更新时间",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "is_archived",
                sa.Boolean(),
                server_default="0",
                nullable=False,
                comment="是否归档",
            ),
        )
    else:
        op.add_column(
            "mistake_records",
            sa.Column(
                "total_review_count",
                sa.Integer(),
                server_default="0",
                nullable=False,
                comment="总复习次数",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "average_mastery",
                sa.Numeric(precision=3, scale=2),
                server_default="0.0",
                nullable=False,
                comment="平均掌握度",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "last_mastery_update",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="最后掌握度更新时间",
            ),
        )
        op.add_column(
            "mistake_records",
            sa.Column(
                "is_archived",
                sa.Boolean(),
                server_default="false",
                nullable=False,
                comment="是否归档",
            ),
        )

    # 5. 为 mistake_records 表添加新索引
    # 部分索引：需要复习且未掌握的记录
    if is_sqlite:
        op.execute(
            "CREATE INDEX idx_mistake_records_user_next_review "
            "ON mistake_records(user_id, next_review_at) "
            "WHERE next_review_at IS NOT NULL AND mastery_status != 'mastered'"
        )
    else:
        op.execute(
            "CREATE INDEX idx_mistake_records_user_next_review "
            "ON mistake_records(user_id, next_review_at) "
            "WHERE next_review_at IS NOT NULL AND mastery_status != 'mastered'"
        )

    # 复合索引：用户+学科+掌握状态
    op.create_index(
        "idx_mistake_records_subject_status",
        "mistake_records",
        ["user_id", "subject", "mastery_status"],
    )

    # 6. 为 mistake_records 添加 GIN 索引（仅 PostgreSQL）
    if not is_sqlite:
        op.execute(
            "CREATE INDEX idx_mistake_records_knowledge_points "
            "ON mistake_records USING GIN(knowledge_points)"
        )
        op.execute(
            "CREATE INDEX idx_mistake_records_tags "
            "ON mistake_records USING GIN(tags)"
        )


def downgrade() -> None:
    """Downgrade schema - Remove mistake_reviews table and indexes."""

    # 删除 GIN 索引（仅 PostgreSQL）
    if not is_sqlite:
        op.execute("DROP INDEX IF EXISTS idx_mistake_records_knowledge_points")
        op.execute("DROP INDEX IF EXISTS idx_mistake_records_tags")

    # 删除 mistake_records 表的新索引
    op.drop_index("idx_mistake_records_subject_status", "mistake_records")
    op.execute("DROP INDEX IF EXISTS idx_mistake_records_user_next_review")

    # 删除 mistake_records 表的新字段
    op.drop_column("mistake_records", "is_archived")
    op.drop_column("mistake_records", "last_mastery_update")
    op.drop_column("mistake_records", "average_mastery")
    op.drop_column("mistake_records", "total_review_count")

    # 删除 mistake_reviews 表的索引
    op.execute("DROP INDEX IF EXISTS idx_mistake_reviews_next_review")
    op.drop_index("idx_mistake_reviews_mistake", "mistake_reviews")
    op.drop_index("idx_mistake_reviews_user_review", "mistake_reviews")

    # 删除检查约束
    op.drop_constraint("ck_mastery_level", "mistake_reviews")
    op.drop_constraint("ck_confidence_level", "mistake_reviews")
    op.drop_constraint("ck_review_result", "mistake_reviews")

    # 删除 mistake_reviews 表
    op.drop_table("mistake_reviews")
