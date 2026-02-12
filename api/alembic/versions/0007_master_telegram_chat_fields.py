"""add master telegram chat fields

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-12 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("masters", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.add_column("masters", sa.Column("telegram_username", sa.String(length=255), nullable=True))
    op.create_index("ix_masters_telegram_user_id", "masters", ["telegram_user_id"], unique=False)
    op.create_index("ix_masters_telegram_chat_id", "masters", ["telegram_chat_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_masters_telegram_chat_id", table_name="masters")
    op.drop_index("ix_masters_telegram_user_id", table_name="masters")
    op.drop_column("masters", "telegram_username")
    op.drop_column("masters", "telegram_chat_id")
