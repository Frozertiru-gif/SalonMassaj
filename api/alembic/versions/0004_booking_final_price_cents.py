"""add final price for bookings

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("final_price_cents", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_bookings_final_price_cents_non_negative",
        "bookings",
        "final_price_cents IS NULL OR final_price_cents >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_bookings_final_price_cents_non_negative", "bookings", type_="check")
    op.drop_column("bookings", "final_price_cents")
