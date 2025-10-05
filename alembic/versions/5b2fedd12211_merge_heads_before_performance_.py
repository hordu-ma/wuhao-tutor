"""merge_heads_before_performance_optimization

Revision ID: 5b2fedd12211
Revises: 8656ac8e3fe6, add_ocr_enhancement_fields
Create Date: 2025-10-05 21:53:12.698359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b2fedd12211'
down_revision: Union[str, Sequence[str], None] = ('8656ac8e3fe6', 'add_ocr_enhancement_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
