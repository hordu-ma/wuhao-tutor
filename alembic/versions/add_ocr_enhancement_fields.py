"""Add OCR enhancement fields to homework_images

Revision ID: add_ocr_enhancement_fields
Revises:
Create Date: 2025-10-04 14:30:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_ocr_enhancement_fields"
down_revision = None  # 请根据实际情况设置上一个迁移的revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加OCR增强字段"""
    # 添加retry_count字段
    op.add_column(
        "homework_images",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="OCR重试次数",
        ),
    )

    # 添加quality_score字段
    op.add_column(
        "homework_images",
        sa.Column(
            "quality_score", sa.Float(), nullable=True, comment="图片质量分数(0-100)"
        ),
    )


def downgrade() -> None:
    """回滚OCR增强字段"""
    op.drop_column("homework_images", "quality_score")
    op.drop_column("homework_images", "retry_count")
