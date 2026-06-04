"""merge_heads

Revision ID: f76d68b0ed98
Revises: a2b3c4d5e6f7, d2f901b9b11d
Create Date: 2026-05-03 07:48:01.132095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f76d68b0ed98'
down_revision: Union[str, None] = ('a2b3c4d5e6f7', 'd2f901b9b11d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass