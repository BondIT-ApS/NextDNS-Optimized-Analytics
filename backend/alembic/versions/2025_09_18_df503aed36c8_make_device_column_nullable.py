"""Make device column nullable

Revision ID: df503aed36c8
Revises: duplicate_prevention
Create Date: 2025-09-18 10:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "df503aed36c8"
down_revision: Union[str, Sequence[str], None] = "duplicate_prevention"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make device column nullable."""
    # Modify the device column to be nullable
    # Also change it from String to Text to match our model
    op.alter_column(
        "dns_logs",
        "device",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    """Make device column non-nullable."""
    # Note: This will fail if there are NULL values in the device column
    # You may need to update NULL values before running this downgrade
    op.alter_column(
        "dns_logs",
        "device",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        nullable=False,
        existing_nullable=True,
    )
