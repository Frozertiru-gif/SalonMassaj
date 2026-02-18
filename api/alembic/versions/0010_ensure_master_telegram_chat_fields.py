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


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = ANY (current_schemas(false))
                      AND table_name = :table_name
                      AND column_name = :column_name
                )
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE masters ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT"))
    op.execute(sa.text("ALTER TABLE masters ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255)"))

    if _column_exists("masters", "telegram_user_id"):
        op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_masters_telegram_user_id ON masters (telegram_user_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_masters_telegram_chat_id ON masters (telegram_chat_id)"))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_chat_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_user_id"))
    op.execute(sa.text("ALTER TABLE masters DROP COLUMN IF EXISTS telegram_username"))
    op.execute(sa.text("ALTER TABLE masters DROP COLUMN IF EXISTS telegram_chat_id"))
