"""add ln_subscription preference columns

Revision ID: f3b5e2a1d789
Revises: e4a7f2c8b91d
Create Date: 2026-05-02

Adds three nullable JSON columns to ln_subscriptions so users can personalise
what topics they want to follow or avoid, and which sources to include.
"""
from alembic import op
import sqlalchemy as sa

revision = 'f3b5e2a1d789'
down_revision = 'e4a7f2c8b91d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'ln_subscriptions',
        sa.Column('topics_follow', sa.JSON(), nullable=True, comment='List of topic keywords to prioritise'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('topics_exclude', sa.JSON(), nullable=True, comment='List of topic keywords to suppress'),
    )
    op.add_column(
        'ln_subscriptions',
        sa.Column('sources_enabled', sa.JSON(), nullable=True,
                  comment='Enabled source names, e.g. ["github","hackernews","reddit","arxiv","articles"]. Null = all enabled.'),
    )


def downgrade() -> None:
    op.drop_column('ln_subscriptions', 'sources_enabled')
    op.drop_column('ln_subscriptions', 'topics_exclude')
    op.drop_column('ln_subscriptions', 'topics_follow')
