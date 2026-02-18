"""add_system_settings_and_nextdns_profiles

Revision ID: a1b2c3d4e5f6
Revises: 5af432e004a8
Create Date: 2026-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "5af432e004a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create system_settings and nextdns_profiles tables.

    system_settings — generic key/value store for application configuration.
      First key: nextdns_api_key (migrates from API_KEY env var on first boot).
      Additional keys will be added in issue #115.

    nextdns_profiles — managed list of NextDNS profiles the scheduler fetches.
      Replaces the PROFILE_IDS env var (seeded from it on first boot).
    """
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "nextdns_profiles",
        sa.Column("profile_id", sa.String(50), primary_key=True),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "idx_nextdns_profiles_enabled",
        "nextdns_profiles",
        ["enabled"],
        unique=False,
    )


def downgrade() -> None:
    """Drop system_settings and nextdns_profiles tables."""
    op.drop_index("idx_nextdns_profiles_enabled", table_name="nextdns_profiles")
    op.drop_table("nextdns_profiles")
    op.drop_table("system_settings")
