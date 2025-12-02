"""add_performance_indexes_for_4m_records

Revision ID: 330627608c30
Revises: df503aed36c8
Create Date: 2025-12-02 13:47:49.894124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '330627608c30'
down_revision: Union[str, Sequence[str], None] = 'df503aed36c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add strategic indexes for 4M+ record performance.
    
    These indexes target the main performance bottlenecks identified in Phase 1:
    - Time range queries (stats/overview, stats/timeseries)
    - Action filtering (blocked vs allowed)
    - Profile-specific queries
    - Combined timestamp + profile queries for optimal filtering
    
    Expected impact:
    - /stats/overview?time_range=7d: 42s → ~1-2s (20-40x improvement)
    - /devices?time_range=24h: 8s → ~500ms (16x improvement)
    - All time-based queries will benefit from these indexes
    """
    # Index for time range filtering (descending for recent-first queries)
    # This is the most critical index for stats queries
    op.create_index(
        'idx_dns_logs_timestamp_desc',
        'dns_logs',
        ['timestamp'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'timestamp': 'DESC'}
    )
    
    # Combined index for time + profile filtering
    # Optimizes queries that filter by both time range and profile_id
    op.create_index(
        'idx_dns_logs_timestamp_profile_desc',
        'dns_logs',
        ['timestamp', 'profile_id'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'timestamp': 'DESC'}
    )
    
    # Index for action filtering (blocked/allowed stats)
    # Speeds up queries that aggregate by action type
    op.create_index(
        'idx_dns_logs_action',
        'dns_logs',
        ['action'],
        unique=False
    )
    
    # Combined index for time + action filtering
    # Optimizes stats queries that need both time range and action filtering
    op.create_index(
        'idx_dns_logs_timestamp_action',
        'dns_logs',
        ['timestamp', 'action'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'timestamp': 'DESC'}
    )
    
    # Run ANALYZE to update table statistics for the query planner
    # This ensures PostgreSQL knows about the new indexes and can use them optimally
    op.execute('ANALYZE dns_logs')


def downgrade() -> None:
    """Downgrade schema - Remove performance indexes."""
    op.drop_index('idx_dns_logs_timestamp_action', table_name='dns_logs')
    op.drop_index('idx_dns_logs_action', table_name='dns_logs')
    op.drop_index('idx_dns_logs_timestamp_profile_desc', table_name='dns_logs')
    op.drop_index('idx_dns_logs_timestamp_desc', table_name='dns_logs')
