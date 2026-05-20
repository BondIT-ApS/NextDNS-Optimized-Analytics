"""drop_unused_dns_logs_indexes

Revision ID: d3e4f5a6b7c8
Revises: c1d2e3f4a5b6
Create Date: 2026-05-20 14:00:00.000000

Drop six dns_logs indexes that have ZERO scans on both DEV and PROD
clusters (issue #183, ~13M rows). Combined size at the time of the
investigation: ~800 MB on DEV, ~2.5 GB on PROD.

Indexes removed:
- idx_dns_logs_tld                (0 scans DEV+PROD)
- idx_dns_logs_tld_action         (0 scans DEV+PROD)
- idx_dns_logs_timestamp_domain   (0 scans DEV+PROD)
- idx_dns_logs_domain             (0 scans DEV+PROD)
- idx_dns_logs_profile_id         (0 scans DEV, 1 scan PROD)
- idx_dns_logs_action             (0 scans DEV, 2 scans PROD)

Indexes KEPT despite low scans on one cluster:
- idx_dns_logs_timestamp_action       — 945 scans on DEV
- idx_dns_logs_timestamp_profile_desc — 47k scans on PROD

Why this helps
--------------
1. Every INSERT updates every index on the table. The worker fetches
   logs every few minutes and inserts hundreds–thousands of rows per
   cycle; removing six write-amplification entries speeds up the
   worker and reduces WAL volume.
2. Smaller index footprint = better PostgreSQL buffer cache hit rate
   on the indexes we actually use.
3. Reclaims ~2.5 GB on PROD without affecting any read path.

Concurrency
-----------
Indexes are dropped with ``DROP INDEX CONCURRENTLY`` so existing
queries are not blocked. This requires running outside an explicit
transaction — Alembic's autocommit_block() handles that.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Indexes confirmed unused on both DEV and PROD as of 2026-05-20.
_UNUSED_INDEXES = (
    "idx_dns_logs_tld",
    "idx_dns_logs_tld_action",
    "idx_dns_logs_timestamp_domain",
    "idx_dns_logs_domain",
    "idx_dns_logs_profile_id",
    "idx_dns_logs_action",
)


def upgrade() -> None:
    """Drop unused indexes concurrently (non-blocking on production)."""
    with op.get_context().autocommit_block():
        for idx in _UNUSED_INDEXES:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {idx}")


def downgrade() -> None:
    """Re-create the dropped indexes (best-effort; concurrent rebuild)."""
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dns_logs_tld "
            "ON dns_logs (tld)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dns_logs_tld_action "
            "ON dns_logs (tld, action)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "idx_dns_logs_timestamp_domain ON dns_logs (timestamp, domain)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dns_logs_domain "
            "ON dns_logs (domain)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dns_logs_profile_id "
            "ON dns_logs (profile_id)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dns_logs_action "
            "ON dns_logs (action)"
        )
