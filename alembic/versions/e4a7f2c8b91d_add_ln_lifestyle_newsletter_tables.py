"""add_ln_lifestyle_newsletter_tables

Revision ID: e4a7f2c8b91d
Revises: 9d1c7f8a4b21
Create Date: 2026-05-02 00:00:00.000000

Creates tables for the Lifestyle Newsletter feature (ln_ prefix).
  - ln_podcast_episodes : shared global podcast episode store
  - ln_subscriptions    : per-user subscription + BYOK ElevenLabs key (encrypted)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4a7f2c8b91d'
down_revision: Union[str, None] = '9d1c7f8a4b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ln_podcast_episodes ---
    op.create_table(
        'ln_podcast_episodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('sources_metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ln_podcast_episodes_id'), 'ln_podcast_episodes', ['id'], unique=False)
    op.create_index(op.f('ix_ln_podcast_episodes_status'), 'ln_podcast_episodes', ['status'], unique=False)

    # --- ln_subscriptions ---
    op.create_table(
        'ln_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.String(length=10), nullable=False, server_default='weekly'),
        sa.Column('delivery_time', sa.String(length=5), nullable=True, server_default='08:00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('elevenlabs_api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_ln_subscriptions_user_id'),
    )
    op.create_index(op.f('ix_ln_subscriptions_id'), 'ln_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_ln_subscriptions_user_id'), 'ln_subscriptions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ln_subscriptions_user_id'), table_name='ln_subscriptions')
    op.drop_index(op.f('ix_ln_subscriptions_id'), table_name='ln_subscriptions')
    op.drop_table('ln_subscriptions')

    op.drop_index(op.f('ix_ln_podcast_episodes_status'), table_name='ln_podcast_episodes')
    op.drop_index(op.f('ix_ln_podcast_episodes_id'), table_name='ln_podcast_episodes')
    op.drop_table('ln_podcast_episodes')
