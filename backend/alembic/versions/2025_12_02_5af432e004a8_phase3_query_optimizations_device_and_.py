"""phase3_query_optimizations_device_and_tld

Revision ID: 5af432e004a8
Revises: 330627608c30
Create Date: 2025-12-02 14:38:41.777268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5af432e004a8'
down_revision: Union[str, Sequence[str], None] = '330627608c30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Phase 3 Query Optimizations.
    
    Fixes identified in Phase 2 performance testing:
    1. Device stats regression (32.5s on 7d range) - Add device-optimized index
    2. TLD stats slowness (2.5s on 24h range) - Add computed TLD column
    
    Expected improvements:
    - /stats/devices?time_range=7d: 32.5s → <1s (32x+ faster)
    - /stats/tlds?time_range=24h: 2.5s → <100ms (25x+ faster)
    """
    
    # 1. Add computed TLD column for fast TLD aggregation
    # This eliminates the need for Python-side regex extraction
    op.add_column('dns_logs', 
        sa.Column('tld', sa.String(255), nullable=True)
    )
    
    # 2. Populate TLD column using PostgreSQL regex
    # Extract TLD from existing domains (e.g., "gateway.icloud.com" → "icloud.com")
    op.execute("""
        UPDATE dns_logs 
        SET tld = (
            SELECT LOWER(regexp_replace(
                domain,
                '^(?:.*\\.)?(\\w[\\w-]*\\.[a-zA-Z]{2,})$',
                '\\1'
            ))
        )
        WHERE tld IS NULL AND domain IS NOT NULL
    """)
    
    # 3. Create index on TLD column for fast aggregation
    op.create_index(
        'idx_dns_logs_tld',
        'dns_logs',
        ['tld'],
        unique=False
    )
    
    # 4. Create composite index for TLD + timestamp queries
    op.create_index(
        'idx_dns_logs_tld_timestamp',
        'dns_logs',
        ['tld', 'timestamp'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'timestamp': 'DESC'}
    )
    
    # 5. Create composite index for TLD + action (blocked/allowed TLDs)
    op.create_index(
        'idx_dns_logs_tld_action',
        'dns_logs',
        ['tld', 'action'],
        unique=False
    )
    
    # 6. Create functional index on device from JSONB data column
    # This fixes the devices regression by providing optimized device queries
    # Note: PostgreSQL automatically handles JSONB extraction in indexes
    op.execute("""
        CREATE INDEX idx_dns_logs_device_name 
        ON dns_logs((data->>'device')) 
        WHERE data->>'device' IS NOT NULL
    """)
    
    # 7. Create composite index for device + timestamp
    # Optimizes device stats queries with time range filtering
    op.execute("""
        CREATE INDEX idx_dns_logs_device_timestamp 
        ON dns_logs(timestamp DESC, (data->>'device')) 
        WHERE data->>'device' IS NOT NULL
    """)
    
    # 8. Run ANALYZE to update statistics
    op.execute('ANALYZE dns_logs')


def downgrade() -> None:
    """Downgrade schema - Remove Phase 3 optimizations."""
    # Drop indexes (reverse order)
    op.execute('DROP INDEX IF EXISTS idx_dns_logs_device_timestamp')
    op.execute('DROP INDEX IF EXISTS idx_dns_logs_device_name')
    op.drop_index('idx_dns_logs_tld_action', table_name='dns_logs')
    op.drop_index('idx_dns_logs_tld_timestamp', table_name='dns_logs')
    op.drop_index('idx_dns_logs_tld', table_name='dns_logs')
    
    # Drop TLD column
    op.drop_column('dns_logs', 'tld')
