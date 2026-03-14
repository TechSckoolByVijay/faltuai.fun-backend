"""add_esm_email_smoothener_sessions_table

Revision ID: 9d1c7f8a4b21
Revises: f2a1c9b6d012
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d1c7f8a4b21'
down_revision: Union[str, None] = 'f2a1c9b6d012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'esm_email_smoothener_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_esm_email_smoothener_sessions_id'), 'esm_email_smoothener_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_esm_email_smoothener_sessions_user_id'), 'esm_email_smoothener_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_esm_email_smoothener_sessions_user_id'), table_name='esm_email_smoothener_sessions')
    op.drop_index(op.f('ix_esm_email_smoothener_sessions_id'), table_name='esm_email_smoothener_sessions')
    op.drop_table('esm_email_smoothener_sessions')
