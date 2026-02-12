"""alias revision id for master telegram chat fields

Revision ID: 0007_master_telegram_chat_fields
Revises: 0007
Create Date: 2026-02-12 00:00:01
"""


# revision identifiers, used by Alembic.
revision = "0007_master_telegram_chat_fields"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op alias migration for backward-compatible revision graph."""


def downgrade() -> None:
    """No-op alias migration for backward-compatible revision graph."""
