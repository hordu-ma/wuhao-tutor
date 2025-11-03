"""align_learning_tracks_with_model

Revision ID: 3b5dff6e22e1
Revises: 9ed9ad5ef837
Create Date: 2025-11-03 15:47:09.013313

重构 knowledge_point_learning_tracks 表以匹配模型定义
从聚合统计表转为详细活动记录表
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3b5dff6e22e1"
down_revision: Union[str, Sequence[str], None] = "9ed9ad5ef837"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """重构表结构为详细活动记录表"""

    # 1. 删除旧的聚合字段
    op.drop_column("knowledge_point_learning_tracks", "learning_events")
    op.drop_column("knowledge_point_learning_tracks", "mastery_curve")
    op.drop_column("knowledge_point_learning_tracks", "first_learned_at")
    op.drop_column("knowledge_point_learning_tracks", "first_mastered_at")
    op.drop_column("knowledge_point_learning_tracks", "last_forgotten_at")
    op.drop_column("knowledge_point_learning_tracks", "total_attempts")
    op.drop_column("knowledge_point_learning_tracks", "total_mistakes")
    op.drop_column("knowledge_point_learning_tracks", "review_efficiency")

    # 2. 删除唯一约束（转为多条记录模式）
    op.drop_constraint(
        "uq_user_knowledge_point", "knowledge_point_learning_tracks", type_="unique"
    )

    # 3. 添加详细活动记录字段
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "activity_type",
            sa.String(20),
            nullable=False,
            server_default="practice",
            comment="活动类型",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "activity_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="活动时间",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "result",
            sa.String(20),
            nullable=False,
            server_default="incorrect",
            comment="结果",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "mastery_before", sa.Numeric(3, 2), nullable=True, comment="活动前掌握度"
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "mastery_after", sa.Numeric(3, 2), nullable=True, comment="活动后掌握度"
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("confidence_level", sa.Integer, nullable=True, comment="信心等级"),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("time_spent", sa.Integer, nullable=True, comment="花费时间(秒)"),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("difficulty_level", sa.Integer, nullable=True, comment="难度等级"),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "error_details",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="错误详情",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "ai_feedback",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="AI反馈",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "improvement_detected",
            sa.Boolean,
            nullable=False,
            server_default="false",
            comment="是否检测到进步",
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("notes", sa.Text, nullable=True, comment="备注"),
    )

    # 4. 创建索引
    op.create_index(
        "idx_kplt_activity_date", "knowledge_point_learning_tracks", ["activity_date"]
    )

    # 5. 移除默认值（仅用于迁移）
    op.alter_column(
        "knowledge_point_learning_tracks", "activity_type", server_default=None
    )
    op.alter_column("knowledge_point_learning_tracks", "result", server_default=None)


def downgrade() -> None:
    """回滚到聚合统计表"""

    # 删除详细记录字段
    op.drop_index(
        "idx_kplt_activity_date", table_name="knowledge_point_learning_tracks"
    )
    op.drop_column("knowledge_point_learning_tracks", "notes")
    op.drop_column("knowledge_point_learning_tracks", "improvement_detected")
    op.drop_column("knowledge_point_learning_tracks", "ai_feedback")
    op.drop_column("knowledge_point_learning_tracks", "error_details")
    op.drop_column("knowledge_point_learning_tracks", "difficulty_level")
    op.drop_column("knowledge_point_learning_tracks", "time_spent")
    op.drop_column("knowledge_point_learning_tracks", "confidence_level")
    op.drop_column("knowledge_point_learning_tracks", "mastery_after")
    op.drop_column("knowledge_point_learning_tracks", "mastery_before")
    op.drop_column("knowledge_point_learning_tracks", "result")
    op.drop_column("knowledge_point_learning_tracks", "activity_date")
    op.drop_column("knowledge_point_learning_tracks", "activity_type")

    # 恢复聚合统计字段
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "learning_events", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "mastery_curve", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("first_learned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("first_mastered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("last_forgotten_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("total_attempts", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column("total_mistakes", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "knowledge_point_learning_tracks",
        sa.Column(
            "review_efficiency", sa.Numeric(3, 2), nullable=False, server_default="0.0"
        ),
    )

    # 恢复唯一约束
    op.create_unique_constraint(
        "uq_user_knowledge_point",
        "knowledge_point_learning_tracks",
        ["user_id", "knowledge_point_id"],
    )
