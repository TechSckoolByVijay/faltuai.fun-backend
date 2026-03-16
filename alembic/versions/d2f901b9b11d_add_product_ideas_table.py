"""add product ideas table

Revision ID: d2f901b9b11d
Revises: 7b3e2aa9d5f1
Create Date: 2026-03-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f901b9b11d'
down_revision: Union[str, None] = '7b3e2aa9d5f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'faltu_product_ideas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('idea_title', sa.String(length=220), nullable=False),
        sa.Column('idea_description', sa.Text(), nullable=False),
        sa.Column('target_users', sa.String(length=220), nullable=True),
        sa.Column('feature_categories', sa.JSON(), nullable=True),
        sa.Column('usage_frequency', sa.String(length=80), nullable=True),
        sa.Column('example_references', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=80), nullable=False),
        sa.Column('is_contact_allowed', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_faltu_product_ideas_id'), 'faltu_product_ideas', ['id'], unique=False)
    op.create_index(op.f('ix_faltu_product_ideas_idea_title'), 'faltu_product_ideas', ['idea_title'], unique=False)
    op.create_index(op.f('ix_faltu_product_ideas_contact_email'), 'faltu_product_ideas', ['contact_email'], unique=False)
    op.create_index(op.f('ix_faltu_product_ideas_status'), 'faltu_product_ideas', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_faltu_product_ideas_status'), table_name='faltu_product_ideas')
    op.drop_index(op.f('ix_faltu_product_ideas_contact_email'), table_name='faltu_product_ideas')
    op.drop_index(op.f('ix_faltu_product_ideas_idea_title'), table_name='faltu_product_ideas')
    op.drop_index(op.f('ix_faltu_product_ideas_id'), table_name='faltu_product_ideas')
    op.drop_table('faltu_product_ideas')
