"""add knowledge graph tables

Revision ID: 20251103_kg_tables
Revises: add_ocr_enhancement_fields
Create Date: 2025-11-03 10:00:00.000000

添加知识图谱相关表:
- mistake_knowledge_points: 错题-知识点关联表
- user_knowledge_graph_snapshots: 用户知识图谱快照表
- knowledge_point_learning_tracks: 知识点学习轨迹表

扩展现有表:
- mistake_records: 添加 knowledge_graph_snapshot 字段
- knowledge_mastery: 添加 related_mistakes 字段
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251103_kg_tables'
down_revision: Union[str, None] = 'add_mistake_source'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库结构"""
    
    # 1. 创建 mistake_knowledge_points 表 (错题-知识点关联)
    op.create_table(
        'mistake_knowledge_points',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('mistake_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_point_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # 关联强度
        sa.Column('relevance_score', sa.Numeric(3, 2), nullable=False, server_default='0.5'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        
        # 错误分析
        sa.Column('error_type', sa.String(50), nullable=False),
        sa.Column('error_reason', sa.Text(), nullable=True),
        
        # 掌握度追踪
        sa.Column('mastery_before', sa.Numeric(3, 2), nullable=True),
        sa.Column('mastery_after', sa.Numeric(3, 2), nullable=True),
        
        # 改进建议
        sa.Column('improvement_notes', sa.Text(), nullable=True),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['mistake_id'], ['mistake_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_nodes.id'], ondelete='CASCADE'),
        
        # 唯一约束
        sa.UniqueConstraint('mistake_id', 'knowledge_point_id', name='uq_mistake_knowledge')
    )
    
    # 创建索引
    op.create_index('idx_mkp_mistake', 'mistake_knowledge_points', ['mistake_id'])
    op.create_index('idx_mkp_knowledge_point', 'mistake_knowledge_points', ['knowledge_point_id'])
    op.create_index('idx_mkp_primary', 'mistake_knowledge_points', ['is_primary'], 
                    postgresql_where=sa.text('is_primary = true'))
    
    # 2. 创建 user_knowledge_graph_snapshots 表 (知识图谱快照)
    op.create_table(
        'user_knowledge_graph_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject', sa.String(20), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        
        # 图谱数据 (JSON)
        sa.Column('knowledge_points', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('weak_chains', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('strong_areas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # 学情摘要
        sa.Column('learning_profile', sa.Text(), nullable=True),
        sa.Column('ai_recommendations', sa.Text(), nullable=True),
        
        # 统计指标
        sa.Column('total_mistakes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_mastery', sa.Numeric(3, 2), nullable=False, server_default='0.0'),
        sa.Column('improvement_trend', sa.String(20), nullable=True),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        
        # 唯一约束: 每个用户每个学科每天只有一个快照
        sa.UniqueConstraint('user_id', 'subject', 'snapshot_date', name='uq_user_subject_date')
    )
    
    # 创建索引
    op.create_index('idx_ukgs_user_subject', 'user_knowledge_graph_snapshots', ['user_id', 'subject'])
    op.create_index('idx_ukgs_date', 'user_knowledge_graph_snapshots', ['snapshot_date'], 
                    postgresql_ops={'snapshot_date': 'DESC'})
    
    # 3. 创建 knowledge_point_learning_tracks 表 (学习轨迹)
    op.create_table(
        'knowledge_point_learning_tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_point_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # 轨迹数据 (JSON)
        sa.Column('learning_events', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mastery_curve', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # 关键节点
        sa.Column('first_learned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_mastered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_forgotten_at', sa.DateTime(timezone=True), nullable=True),
        
        # 统计
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_mistakes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('review_efficiency', sa.Numeric(3, 2), nullable=False, server_default='0.0'),
        
        # 元数据
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_nodes.id'], ondelete='CASCADE'),
        
        # 唯一约束
        sa.UniqueConstraint('user_id', 'knowledge_point_id', name='uq_user_knowledge_point')
    )
    
    # 创建索引
    op.create_index('idx_kplt_user', 'knowledge_point_learning_tracks', ['user_id'])
    op.create_index('idx_kplt_kp', 'knowledge_point_learning_tracks', ['knowledge_point_id'])
    
    # 4. 扩展现有表 - mistake_records
    op.add_column('mistake_records', 
                  sa.Column('knowledge_graph_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # 5. 扩展现有表 - knowledge_mastery (如果存在的话)
    # 先检查表是否存在,如果存在再添加字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'knowledge_mastery' in inspector.get_table_names():
        op.add_column('knowledge_mastery', 
                      sa.Column('related_mistakes', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    print("✅ 知识图谱表结构创建成功!")


def downgrade() -> None:
    """回滚数据库结构"""
    
    # 删除扩展字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'knowledge_mastery' in inspector.get_table_names():
        op.drop_column('knowledge_mastery', 'related_mistakes')
    
    op.drop_column('mistake_records', 'knowledge_graph_snapshot')
    
    # 删除索引
    op.drop_index('idx_kplt_kp', table_name='knowledge_point_learning_tracks')
    op.drop_index('idx_kplt_user', table_name='knowledge_point_learning_tracks')
    
    op.drop_index('idx_ukgs_date', table_name='user_knowledge_graph_snapshots')
    op.drop_index('idx_ukgs_user_subject', table_name='user_knowledge_graph_snapshots')
    
    op.drop_index('idx_mkp_primary', table_name='mistake_knowledge_points')
    op.drop_index('idx_mkp_knowledge_point', table_name='mistake_knowledge_points')
    op.drop_index('idx_mkp_mistake', table_name='mistake_knowledge_points')
    
    # 删除表
    op.drop_table('knowledge_point_learning_tracks')
    op.drop_table('user_knowledge_graph_snapshots')
    op.drop_table('mistake_knowledge_points')
    
    print("✅ 知识图谱表结构回滚成功!")
