"""Add stock analysis tables

Revision ID: d8f9e5c2a1b3
Revises: a7ff7ed5c8c4
Create Date: 2025-12-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f9e5c2a1b3'
down_revision: Union[str, None] = 'a7ff7ed5c8c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create stock_analyses table
    op.create_table(
        'stock_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_question', sa.Text(), nullable=False),
        sa.Column('stock_symbol', sa.String(length=20), nullable=True),
        sa.Column('stock_name', sa.String(length=255), nullable=True),
        sa.Column('analysis_plan', sa.Text(), nullable=True),
        sa.Column('research_data', sa.Text(), nullable=True),
        sa.Column('final_report', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('analysis_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for stock_analyses
    op.create_index('ix_stock_analyses_id', 'stock_analyses', ['id'])
    op.create_index('ix_stock_analyses_user_id', 'stock_analyses', ['user_id'])
    op.create_index('ix_stock_analyses_stock_symbol', 'stock_analyses', ['stock_symbol'])
    op.create_index('idx_user_created', 'stock_analyses', ['user_id', 'created_at'])
    op.create_index('idx_stock_symbol', 'stock_analyses', ['stock_symbol', 'created_at'])
    op.create_index('idx_status', 'stock_analyses', ['analysis_status'])
    
    # Create stock_analysis_cache table
    op.create_table(
        'stock_analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_symbol', sa.String(length=20), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('cached_data', sa.Text(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cache_hits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for stock_analysis_cache
    op.create_index('ix_stock_analysis_cache_id', 'stock_analysis_cache', ['id'])
    op.create_index('ix_stock_analysis_cache_stock_symbol', 'stock_analysis_cache', ['stock_symbol'])
    op.create_index('ix_stock_analysis_cache_query_hash', 'stock_analysis_cache', ['query_hash'])
    op.create_index('idx_cache_lookup', 'stock_analysis_cache', ['stock_symbol', 'data_type', 'query_hash'])
    op.create_index('idx_cache_expiry', 'stock_analysis_cache', ['expires_at', 'is_valid'])


def downgrade() -> None:
    # Drop indexes for stock_analysis_cache
    op.drop_index('idx_cache_expiry', 'stock_analysis_cache')
    op.drop_index('idx_cache_lookup', 'stock_analysis_cache')
    op.drop_index('ix_stock_analysis_cache_query_hash', 'stock_analysis_cache')
    op.drop_index('ix_stock_analysis_cache_stock_symbol', 'stock_analysis_cache')
    op.drop_index('ix_stock_analysis_cache_id', 'stock_analysis_cache')
    
    # Drop stock_analysis_cache table
    op.drop_table('stock_analysis_cache')
    
    # Drop indexes for stock_analyses
    op.drop_index('idx_status', 'stock_analyses')
    op.drop_index('idx_stock_symbol', 'stock_analyses')
    op.drop_index('idx_user_created', 'stock_analyses')
    op.drop_index('ix_stock_analyses_stock_symbol', 'stock_analyses')
    op.drop_index('ix_stock_analyses_user_id', 'stock_analyses')
    op.drop_index('ix_stock_analyses_id', 'stock_analyses')
    
    # Drop stock_analyses table
    op.drop_table('stock_analyses')
