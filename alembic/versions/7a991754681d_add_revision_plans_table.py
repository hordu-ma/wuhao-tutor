"""add_revision_plans_table

Revision ID: 7a991754681d
Revises: 4b0c11bd46a4
Create Date: 2025-11-21 20:09:42.835297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a991754681d'
down_revision: Union[str, Sequence[str], None] = '4b0c11bd46a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('revision_plans',
        sa.Column('id', sa.UUID(), nullable=False, comment='主键ID'),
        sa.Column('user_id', sa.UUID(), nullable=False, comment='用户ID'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='计划标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='简短描述'),
        sa.Column('cycle_type', sa.String(length=20), nullable=False, comment='周期类型: 7days|14days|30days'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='状态: draft|published|completed|expired'),
        sa.Column('mistake_count', sa.Integer(), nullable=True, comment='包含的错题数'),
        sa.Column('knowledge_points', sa.JSON(), nullable=True, comment='涉及的知识点列表'),
        sa.Column('date_range', sa.JSON(), nullable=True, comment='日期范围'),
        sa.Column('plan_content', sa.JSON(), nullable=True, comment='结构化的复习计划数据'),
        sa.Column('pdf_url', sa.String(length=500), nullable=True, comment='PDF下载链接(OSS)'),
        sa.Column('pdf_size', sa.Integer(), nullable=True, comment='文件大小(字节)'),
        sa.Column('markdown_url', sa.String(length=500), nullable=True, comment='Markdown源文件链接'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('expired_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('download_count', sa.Integer(), nullable=True, comment='下载次数'),
        sa.Column('view_count', sa.Integer(), nullable=True, comment='浏览次数'),
        sa.Column('is_shared', sa.Boolean(), nullable=True, comment='是否分享过'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revision_plans_created_at'), 'revision_plans', ['created_at'], unique=False)
    op.create_index(op.f('ix_revision_plans_expired_at'), 'revision_plans', ['expired_at'], unique=False)
    op.create_index(op.f('ix_revision_plans_user_id'), 'revision_plans', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_revision_plans_user_id'), table_name='revision_plans')
    op.drop_index(op.f('ix_revision_plans_expired_at'), table_name='revision_plans')
    op.drop_index(op.f('ix_revision_plans_created_at'), table_name='revision_plans')
    op.drop_table('revision_plans')
