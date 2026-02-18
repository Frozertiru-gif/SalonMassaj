"""ensure master telegram chat fields exist

Revision ID: 0010_ensure_master_telegram_chat_fields
Revises: 0009_merge_heads
Create Date: 2026-02-18 22:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0010_ensure_master_telegram_chat_fields"
down_revision = "0009_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE masters ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT"))
    op.execute(sa.text("ALTER TABLE masters ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255)"))

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_masters_telegram_user_id ON masters (telegram_user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_masters_telegram_chat_id ON masters (telegram_chat_id)"))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_chat_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_user_id"))
    op.execute(sa.text("ALTER TABLE masters DROP COLUMN IF EXISTS telegram_username"))
    op.execute(sa.text("ALTER TABLE masters DROP COLUMN IF EXISTS telegram_chat_id"))
