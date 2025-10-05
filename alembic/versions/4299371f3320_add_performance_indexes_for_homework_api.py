"""add_performance_indexes_for_homework_api

Revision ID: 4299371f3320
Revises: 5b2fedd12211
Create Date: 2025-10-05 21:53:19.400909

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4299371f3320"
down_revision: Union[str, Sequence[str], None] = "5b2fedd12211"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by adding performance indexes."""

    # HomeworkSubmission表的复合索引
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_submissions_student_created 
        ON homework_submissions(student_id, created_at DESC);
    """
        )
    )

    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_submissions_status_created 
        ON homework_submissions(status, created_at DESC);
    """
        )
    )

    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_submissions_student_status 
        ON homework_submissions(student_id, status);
    """
        )
    )

    # HomeworkReview表的索引
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_reviews_submission_status 
        ON homework_reviews(submission_id, status);
    """
        )
    )

    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_reviews_completed_at 
        ON homework_reviews(completed_at DESC) 
        WHERE completed_at IS NOT NULL;
    """
        )
    )

    # Homework表的复合索引
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_homework_subject_grade 
        ON homework(subject, grade_level);
    """
        )
    )

    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_homework_active_created 
        ON homework(is_active, created_at DESC) 
        WHERE deleted_at IS NULL;
    """
        )
    )

    # HomeworkImage表的索引
    op.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_images_submission_order 
        ON homework_images(submission_id, image_order);
    """
        )
    )

    # 更新表统计信息
    op.execute(text("ANALYZE homework;"))
    op.execute(text("ANALYZE homework_submissions;"))
    op.execute(text("ANALYZE homework_reviews;"))
    op.execute(text("ANALYZE homework_images;"))


def downgrade() -> None:
    """Downgrade schema by removing performance indexes."""

    # 删除创建的索引
    op.execute(text("DROP INDEX IF EXISTS idx_submissions_student_created;"))
    op.execute(text("DROP INDEX IF EXISTS idx_submissions_status_created;"))
    op.execute(text("DROP INDEX IF EXISTS idx_submissions_student_status;"))
    op.execute(text("DROP INDEX IF EXISTS idx_reviews_submission_status;"))
    op.execute(text("DROP INDEX IF EXISTS idx_reviews_completed_at;"))
    op.execute(text("DROP INDEX IF EXISTS idx_homework_subject_grade;"))
    op.execute(text("DROP INDEX IF EXISTS idx_homework_active_created;"))
    op.execute(text("DROP INDEX IF EXISTS idx_images_submission_order;"))
