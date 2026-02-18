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


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_column("masters", "telegram_chat_id"):
        op.add_column("masters", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))

    if not _has_column("masters", "telegram_username"):
        op.add_column("masters", sa.Column("telegram_username", sa.String(length=255), nullable=True))

    if _has_column("masters", "telegram_user_id") and not _has_index("masters", "ix_masters_telegram_user_id"):
        op.create_index("ix_masters_telegram_user_id", "masters", ["telegram_user_id"], unique=False)

    if _has_column("masters", "telegram_chat_id") and not _has_index("masters", "ix_masters_telegram_chat_id"):
        op.create_index("ix_masters_telegram_chat_id", "masters", ["telegram_chat_id"], unique=False)


def downgrade() -> None:
    if _has_index("masters", "ix_masters_telegram_chat_id"):
        op.drop_index("ix_masters_telegram_chat_id", table_name="masters")

    if _has_index("masters", "ix_masters_telegram_user_id"):
        op.drop_index("ix_masters_telegram_user_id", table_name="masters")

    if _has_column("masters", "telegram_username"):
        op.drop_column("masters", "telegram_username")

    if _has_column("masters", "telegram_chat_id"):
        op.drop_column("masters", "telegram_chat_id")
