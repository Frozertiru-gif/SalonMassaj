"""booking datetime without timezone

Revision ID: 0008_booking_datetime_without_timezone
Revises: 0007
Create Date: 2026-02-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_booking_datetime_without_timezone"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "bookings",
        "starts_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        postgresql_using="starts_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        "bookings",
        "ends_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        postgresql_using="ends_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "bookings",
        "starts_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="starts_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        "bookings",
        "ends_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        postgresql_using="ends_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
