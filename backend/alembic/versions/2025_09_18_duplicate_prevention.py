"""Add duplicate prevention and fetch tracking

Revision ID: duplicate_prevention
Revises: 5eef40b793b3
Create Date: 2025-09-18 08:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'duplicate_prevention'
down_revision: Union[str, Sequence[str], None] = '5eef40b793b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with duplicate prevention and fetch tracking."""
    
    # First, let's modify the existing dns_logs table
    # Add unique constraint for duplicate prevention
    op.create_unique_constraint(
        'uq_dns_logs_timestamp_domain_client',
        'dns_logs',
        ['timestamp', 'domain', 'client_ip']
    )
    
    # Create fetch_status table for tracking incremental fetches
    op.create_table('fetch_status',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('last_fetch_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_successful_fetch', sa.DateTime(timezone=True), nullable=False),
        sa.Column('records_fetched', sa.Integer(), nullable=False, default=0),
        sa.Column('profile_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes to fetch_status table
    op.create_index('ix_fetch_status_profile_id', 'fetch_status', ['profile_id'])
    
    # Add unique constraint for fetch_status (one record per profile)
    op.create_unique_constraint(
        'uq_fetch_status_profile',
        'fetch_status',
        ['profile_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop fetch_status table and its constraints/indexes
    op.drop_constraint('uq_fetch_status_profile', 'fetch_status', type_='unique')
    op.drop_index('ix_fetch_status_profile_id', 'fetch_status')
    op.drop_table('fetch_status')
    
    # Drop unique constraint from dns_logs
    op.drop_constraint('uq_dns_logs_timestamp_domain_client', 'dns_logs', type_='unique')