"""add ln_subscriptions advanced preference columns

Revision ID: a2b3c4d5e6f7
Revises: f3b5e2a1d789
Create Date: 2026-05-03

Adds 7 new columns to ln_subscriptions for:
  - presentation_mode  (news | podcast)
  - audio_provider     (elevenlabs | deepgram | both)
  - deepgram_api_key_encrypted  (BYOK, Fernet-encrypted)
  - voice_id           (ElevenLabs or Deepgram voice model)
  - fallback_enabled   (auto-switch to secondary provider on failure)
  - custom_topics      (user-defined free-text topic list)
  - priority_people    (names of people to boost in content scoring)
"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b3c4d5e6f7'
down_revision = 'f3b5e2a1d789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'ln_subscriptions',
        sa.Column('presentation_mode', sa.String(20), nullable=False, server_default='news',
                  comment='news | podcast — controls writer format and TTS rendering'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('audio_provider', sa.String(20), nullable=False, server_default='elevenlabs',
                  comment='elevenlabs | deepgram | both'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('deepgram_api_key_encrypted', sa.Text(), nullable=True,
                  comment='Fernet-encrypted Deepgram API key, NULL when not set'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('voice_id', sa.String(200), nullable=True,
                  comment='Voice ID for primary audio provider'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('fallback_enabled', sa.Boolean(), nullable=False, server_default='true',
                  comment='Auto-switch to secondary provider on primary failure'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('custom_topics', sa.JSON(), nullable=True,
                  comment='User-defined free-text topics, e.g. ["LangGraph updates", "AI in DevOps"]'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('priority_people', sa.JSON(), nullable=True,
                  comment='Names of people to boost in content scoring, e.g. ["Andrej Karpathy"]'),
    )


def downgrade() -> None:
    op.drop_column('ln_subscriptions', 'priority_people')
    op.drop_column('ln_subscriptions', 'custom_topics')
    op.drop_column('ln_subscriptions', 'fallback_enabled')
    op.drop_column('ln_subscriptions', 'voice_id')
    op.drop_column('ln_subscriptions', 'deepgram_api_key_encrypted')
    op.drop_column('ln_subscriptions', 'audio_provider')
    op.drop_column('ln_subscriptions', 'presentation_mode')
