"""add_analytics_performance_indexes

Revision ID: 530d40eea860
Revises: 4299371f3320
Create Date: 2025-10-05 22:43:37.450127

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "530d40eea860"
down_revision: Union[str, Sequence[str], None] = "4299371f3320"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add analytics performance indexes."""

    # 作业提交表索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_homework_submission_student_created "
        "ON homework_submissions(student_id, created_at DESC)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_homework_submission_score "
        "ON homework_submissions(total_score) "
        "WHERE total_score IS NOT NULL"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_homework_submission_status_created "
        "ON homework_submissions(status, created_at DESC)"
    )

    # 作业表索引（包含学科）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_homework_subject_created "
        "ON homework(subject, created_at DESC)"
    )

    # 问题表索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_question_user_created "
        "ON questions(user_id, created_at DESC)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_question_subject_created "
        "ON questions(subject, created_at DESC) "
        "WHERE subject IS NOT NULL"
    )

    # 答案表索引
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_answer_question_created "
        "ON answers(question_id, created_at DESC)"
    )

    # 复合索引优化学情分析查询
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_homework_submission_analytics "
        "ON homework_submissions(student_id, created_at, total_score, status) "
        "WHERE status != 'deleted'"
    )


def downgrade() -> None:
    """Downgrade schema - Remove analytics performance indexes."""

    # 删除创建的索引
    op.execute("DROP INDEX IF EXISTS idx_homework_submission_student_created")
    op.execute("DROP INDEX IF EXISTS idx_homework_submission_score")
    op.execute("DROP INDEX IF EXISTS idx_homework_submission_status_created")
    op.execute("DROP INDEX IF EXISTS idx_homework_subject_created")
    op.execute("DROP INDEX IF EXISTS idx_question_user_created")
    op.execute("DROP INDEX IF EXISTS idx_question_subject_created")
    op.execute("DROP INDEX IF EXISTS idx_answer_question_created")
    op.execute("DROP INDEX IF EXISTS idx_homework_submission_analytics")
