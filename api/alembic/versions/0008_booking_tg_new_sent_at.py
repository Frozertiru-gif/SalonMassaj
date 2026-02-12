"""add booking tg_new_sent_at flag

Revision ID: 0008_booking_tg_new_sent_at
Revises: 0007_master_telegram_chat_fields
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_booking_tg_new_sent_at"
down_revision = "0007_master_telegram_chat_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("tg_new_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "tg_new_sent_at")
