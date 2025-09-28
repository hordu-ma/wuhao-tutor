"""初始化数据库表结构

Revision ID: 514d24f19ff7
Revises:
Create Date: 2025-09-28 12:04:03.718301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '514d24f19ff7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone', sa.String(11), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('wechat_openid', sa.String(128), nullable=True, unique=True, index=True),
        sa.Column('wechat_unionid', sa.String(128), nullable=True, unique=True, index=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('nickname', sa.String(50), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('school', sa.String(100), nullable=True),
        sa.Column('grade_level', sa.String(20), nullable=True),
        sa.Column('class_name', sa.String(50), nullable=True),
        sa.Column('institution', sa.String(100), nullable=True),
        sa.Column('parent_contact', sa.String(11), nullable=True),
        sa.Column('parent_name', sa.String(50), nullable=True),
        sa.Column('role', sa.String(20), default='student', nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('study_subjects', sa.Text, nullable=True),
        sa.Column('study_goals', sa.Text, nullable=True),
        sa.Column('notification_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('last_login_at', sa.String(50), nullable=True),
        sa.Column('login_count', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('device_id', sa.String(128), nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('access_token_jti', sa.String(36), nullable=False, unique=True),
        sa.Column('refresh_token_jti', sa.String(36), nullable=False, unique=True),
        sa.Column('expires_at', sa.String(50), nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create homework table
    op.create_table(
        'homework',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('subject', sa.String(20), nullable=False, index=True),
        sa.Column('homework_type', sa.String(20), default='daily', nullable=False),
        sa.Column('difficulty_level', sa.String(10), default='medium', nullable=False),
        sa.Column('grade_level', sa.String(20), nullable=False, index=True),
        sa.Column('chapter', sa.String(100), nullable=True),
        sa.Column('knowledge_points', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('estimated_duration', sa.Integer, nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('creator_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('creator_name', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_template', sa.Boolean, default=False, nullable=False),
        sa.Column('total_submissions', sa.Integer, default=0, nullable=False),
        sa.Column('avg_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id']),
    )

    # Create homework_submissions table
    op.create_table(
        'homework_submissions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('homework_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('student_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('student_name', sa.String(50), nullable=False),
        sa.Column('submission_title', sa.String(200), nullable=True),
        sa.Column('submission_note', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='uploaded', nullable=False, index=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Float, nullable=True),
        sa.Column('accuracy_rate', sa.Float, nullable=True),
        sa.Column('completion_time', sa.Integer, nullable=True),
        sa.Column('ai_review_data', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('weak_knowledge_points', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('improvement_suggestions', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('device_info', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['homework_id'], ['homework.id']),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
        sa.UniqueConstraint('homework_id', 'student_id', name='uq_homework_student'),
    )

    # Create homework_images table
    op.create_table(
        'homework_images',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('image_width', sa.Integer, nullable=True),
        sa.Column('image_height', sa.Integer, nullable=True),
        sa.Column('display_order', sa.Integer, default=0, nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False, nullable=False),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('ocr_confidence', sa.Float, nullable=True),
        sa.Column('ocr_data', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('ocr_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_processed', sa.Boolean, default=False, nullable=False),
        sa.Column('processing_error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['homework_submissions.id']),
    )

    # Create homework_reviews table
    op.create_table(
        'homework_reviews',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('review_type', sa.String(20), default='ai_auto', nullable=False),
        sa.Column('reviewer_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewer_name', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration', sa.Integer, nullable=True),
        sa.Column('total_score', sa.Float, nullable=True),
        sa.Column('max_score', sa.Float, default=100.0, nullable=False),
        sa.Column('accuracy_rate', sa.Float, nullable=True),
        sa.Column('overall_comment', sa.Text, nullable=True),
        sa.Column('strengths', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('weaknesses', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('suggestions', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('knowledge_point_analysis', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('difficulty_analysis', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('question_reviews', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('ai_model_version', sa.String(50), nullable=True),
        sa.Column('ai_confidence_score', sa.Float, nullable=True),
        sa.Column('ai_processing_tokens', sa.Integer, nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('needs_manual_review', sa.Boolean, default=False, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['homework_submissions.id']),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id']),
    )

    # Create indexes for performance
    op.create_index('idx_homework_subject_grade', 'homework', ['subject', 'grade_level'])
    op.create_index('idx_homework_creator_active', 'homework', ['creator_id', 'is_active'])
    op.create_index('idx_submission_student_status', 'homework_submissions', ['student_id', 'status'])
    op.create_index('idx_submission_homework_submitted', 'homework_submissions', ['homework_id', 'submitted_at'])
    op.create_index('idx_image_submission_order', 'homework_images', ['submission_id', 'display_order'])
    op.create_index('idx_review_submission_status', 'homework_reviews', ['submission_id', 'status'])
    op.create_index('idx_review_completed', 'homework_reviews', ['completed_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_review_completed')
    op.drop_index('idx_review_submission_status')
    op.drop_index('idx_image_submission_order')
    op.drop_index('idx_submission_homework_submitted')
    op.drop_index('idx_submission_student_status')
    op.drop_index('idx_homework_creator_active')
    op.drop_index('idx_homework_subject_grade')

    # Drop tables in reverse order to respect foreign keys
    op.drop_table('homework_reviews')
    op.drop_table('homework_images')
    op.drop_table('homework_submissions')
    op.drop_table('homework')
    op.drop_table('user_sessions')
    op.drop_table('users')
