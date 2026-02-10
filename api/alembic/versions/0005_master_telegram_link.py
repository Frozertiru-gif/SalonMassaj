"""add telegram link fields for masters

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("masters", sa.Column("telegram_user_id", sa.BigInteger(), nullable=True))
    op.add_column("masters", sa.Column("telegram_link_code", sa.String(length=128), nullable=True))
    op.add_column("masters", sa.Column("telegram_linked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_masters_telegram_user_id", "masters", ["telegram_user_id"])
    op.create_unique_constraint("uq_masters_telegram_link_code", "masters", ["telegram_link_code"])
    op.create_index("ix_masters_telegram_link_code", "masters", ["telegram_link_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_masters_telegram_link_code", table_name="masters")
    op.drop_constraint("uq_masters_telegram_link_code", "masters", type_="unique")
    op.drop_constraint("uq_masters_telegram_user_id", "masters", type_="unique")
    op.drop_column("masters", "telegram_linked_at")
    op.drop_column("masters", "telegram_link_code")
    op.drop_column("masters", "telegram_user_id")
