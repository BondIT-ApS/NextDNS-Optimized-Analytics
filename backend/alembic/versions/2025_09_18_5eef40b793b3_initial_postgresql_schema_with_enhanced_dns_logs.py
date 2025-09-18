"""Initial PostgreSQL schema with enhanced DNS logs

Revision ID: 5eef40b793b3
Revises: 
Create Date: 2025-09-18 08:40:19.520987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5eef40b793b3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create dns_logs table
    op.create_table('dns_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('device', sa.String(length=255), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('query_type', sa.String(length=10), nullable=True),
        sa.Column('blocked', sa.Boolean(), nullable=False),
        sa.Column('profile_id', sa.String(length=50), nullable=True),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_dns_logs_domain', 'dns_logs', ['domain'])
    op.create_index('idx_dns_logs_blocked', 'dns_logs', ['blocked'])
    op.create_index('idx_dns_logs_profile_id', 'dns_logs', ['profile_id'])
    op.create_index('idx_dns_logs_timestamp_domain', 'dns_logs', ['timestamp', 'domain'])
    op.create_index('idx_dns_logs_domain_action', 'dns_logs', ['domain', 'action'])
    op.create_index('idx_dns_logs_profile_timestamp', 'dns_logs', ['profile_id', 'timestamp'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_dns_logs_profile_timestamp', 'dns_logs')
    op.drop_index('idx_dns_logs_domain_action', 'dns_logs')
    op.drop_index('idx_dns_logs_timestamp_domain', 'dns_logs')
    op.drop_index('idx_dns_logs_profile_id', 'dns_logs')
    op.drop_index('idx_dns_logs_blocked', 'dns_logs')
    op.drop_index('idx_dns_logs_domain', 'dns_logs')
    
    # Drop table
    op.drop_table('dns_logs')
