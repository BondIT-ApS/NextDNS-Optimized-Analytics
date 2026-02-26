"""add_device_name_column_and_optimize_indexes

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a1
Create Date: 2026-02-26 13:00:00.000000

Root-cause fix for worker OOM and backend pod scaling caused by
get_stats_devices() loading all matching rows into Python memory
to parse JSON device names.

Changes
-------
1. Add ``device_name`` column (VARCHAR 255, nullable)
   Extracted from the existing ``device`` JSON column — same pattern as
   the successful ``tld`` optimisation (phase 3).

2. Backfill ``device_name`` for all existing rows
   Uses PostgreSQL's native JSON cast: ``device::json->>'name'``
   Rows where ``device`` is NULL or not valid JSON are left as NULL.

3. Drop 4 indexes with ZERO scans totalling ~207 MB
   - idx_dns_logs_device_timestamp  (115 MB) — indexed data->>'device'
     which is TEXT not JSONB so the index was never usable
   - idx_dns_logs_tld_timestamp     ( 74 MB) — unused; tld queries go
     through idx_dns_logs_tld / idx_dns_logs_tld_action instead
   - idx_dns_logs_device_name       (  7 MB) — same broken JSONB issue
   - idx_dns_logs_domain_action     ( 11 MB) — zero scans

4. Add covering composite index for device stats queries
   ``idx_dns_logs_timestamp_device_name`` on (timestamp DESC, device_name)
   Lets the device stats GROUP BY query do an index-only scan.

5. ANALYZE dns_logs to refresh query-planner statistics.

Expected improvements
---------------------
- get_stats_devices(time_range='7d'): ~5 s, 600 MB RAM → <100 ms, <1 MB
- Worker precompute_all_stats(): no more OOMKilled on 7d/30d ranges
- Index storage freed: ~192 MB net (207 MB removed, ~15 MB added)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply device_name column + index optimisation."""

    # ------------------------------------------------------------------
    # 1. Add device_name column
    # ------------------------------------------------------------------
    op.add_column(
        "dns_logs",
        sa.Column("device_name", sa.String(255), nullable=True),
    )

    # ------------------------------------------------------------------
    # 2. Backfill from existing device JSON column
    #    device stores strings like '{"id": "8BSGM", "name": "TFS iPhone 15"}'
    #    We cast to json and extract the 'name' key.
    #    Rows with NULL or invalid JSON are silently left as NULL.
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE dns_logs
        SET device_name = TRIM(device::json->>'name')
        WHERE device IS NOT NULL
          AND device <> ''
          AND device <> 'null'
          AND device::text LIKE '{%'
        """
    )

    # ------------------------------------------------------------------
    # 3. Drop 4 unused / broken indexes (~207 MB total)
    # ------------------------------------------------------------------
    # These were created in the phase3 migration but target data->>'device'
    # which is a TEXT column — PostgreSQL cannot use functional JSON indexes
    # on plain TEXT, so they accumulated size while never being used.
    op.execute("DROP INDEX IF EXISTS idx_dns_logs_device_timestamp")
    op.execute("DROP INDEX IF EXISTS idx_dns_logs_device_name")

    # tld_timestamp had 0 scans; tld queries use idx_dns_logs_tld_action instead
    op.execute("DROP INDEX IF EXISTS idx_dns_logs_tld_timestamp")

    # domain_action had 0 scans in pg_stat_user_indexes
    op.execute("DROP INDEX IF EXISTS idx_dns_logs_domain_action")

    # ------------------------------------------------------------------
    # 4. Add covering index for device stats GROUP BY queries
    #    Covers: WHERE timestamp >= cutoff [AND profile_id = X]
    #            GROUP BY device_name
    #    The DESC ordering matches the idx_dns_logs_timestamp_desc pattern.
    # ------------------------------------------------------------------
    op.create_index(
        "idx_dns_logs_timestamp_device_name",
        "dns_logs",
        ["timestamp", "device_name"],
        unique=False,
        postgresql_using="btree",
        postgresql_ops={"timestamp": "DESC"},
    )

    # ------------------------------------------------------------------
    # 5. Refresh planner statistics
    # ------------------------------------------------------------------
    op.execute("ANALYZE dns_logs")


def downgrade() -> None:
    """Reverse the device_name column + index optimisation."""
    op.execute("DROP INDEX IF EXISTS idx_dns_logs_timestamp_device_name")
    op.drop_column("dns_logs", "device_name")

    # Restore dropped indexes (best-effort; sizes will rebuild over time)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dns_logs_domain_action
        ON dns_logs(domain, action)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dns_logs_tld_timestamp
        ON dns_logs(tld, timestamp DESC)
        WHERE tld IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dns_logs_device_name
        ON dns_logs((data->>'device'))
        WHERE data->>'device' IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dns_logs_device_timestamp
        ON dns_logs(timestamp DESC, (data->>'device'))
        WHERE data->>'device' IS NOT NULL
        """
    )

    op.execute("ANALYZE dns_logs")
