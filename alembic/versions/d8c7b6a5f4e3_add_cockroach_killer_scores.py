"""add cockroach killer score table

Revision ID: d8c7b6a5f4e3
Revises: f76d68b0ed98
Create Date: 2026-06-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'd8c7b6a5f4e3'
down_revision = 'f76d68b0ed98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cockroach_killer_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(length=255), nullable=False),
        sa.Column('theme', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('cockroach_killer_records')
