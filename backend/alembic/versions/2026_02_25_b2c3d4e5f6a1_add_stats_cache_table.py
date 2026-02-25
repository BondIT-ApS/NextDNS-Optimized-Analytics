"""add_stats_cache_table

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-02-25 00:00:00.000000

Adds the stats_cache table for the two-level stats caching system (issue #183).

The scheduler populates this table after each fetch cycle so that
dashboard API requests can be served from pre-computed results instead
of running expensive aggregation queries on the full dns_logs table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stats_cache table.

    Columns:
        cache_key  — deterministic key encoding stat type + parameters.
                     e.g. "overview:profile_all:range_24h"
        payload    — JSON-serialised stats result.
        computed_at — timestamp of last computation (for observability).
    """
    op.create_table(
        "stats_cache",
        sa.Column("cache_key", sa.String(255), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop stats_cache table."""
    op.drop_table("stats_cache")
