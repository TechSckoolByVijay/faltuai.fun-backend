"""drop_stock_analysis_tables

Revision ID: 7b3e2aa9d5f1
Revises: 9d1c7f8a4b21
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b3e2aa9d5f1'
down_revision: Union[str, None] = '9d1c7f8a4b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS stock_analysis_cache CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS stock_analyses CASCADE"))


def downgrade() -> None:
    pass
