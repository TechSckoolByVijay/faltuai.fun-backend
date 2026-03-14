"""add_is_super_user_to_users

Revision ID: f2a1c9b6d012
Revises: a7ff7ed5c8c4
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a1c9b6d012'
down_revision: Union[str, None] = 'd8f9e5c2a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_super_user', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
    op.alter_column('users', 'is_super_user', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'is_super_user')
