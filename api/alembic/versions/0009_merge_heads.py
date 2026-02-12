"""merge heads

Revision ID: 0009_merge_heads
Revises: 0008_booking_datetime_without_timezone, 0008_booking_tg_new_sent_at
Create Date: 2026-02-12 00:00:02
"""

# revision identifiers, used by Alembic.
revision = "0009_merge_heads"
down_revision = ("0008_booking_datetime_without_timezone", "0008_booking_tg_new_sent_at")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
