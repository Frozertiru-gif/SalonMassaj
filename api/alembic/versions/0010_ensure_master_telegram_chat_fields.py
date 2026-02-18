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


def _masters_schema() -> str:
    bind = op.get_bind()
    schema = bind.execute(
        sa.text(
            """
            SELECT t.table_schema
            FROM information_schema.tables AS t
            WHERE t.table_name = 'masters'
              AND t.table_type = 'BASE TABLE'
              AND t.table_schema = ANY (current_schemas(false))
            ORDER BY array_position(current_schemas(false), t.table_schema)
            LIMIT 1
            """
        )
    ).scalar()
    return schema or "public"


def _qualified_masters_table() -> str:
    bind = op.get_bind()
    schema = _masters_schema()
    preparer = bind.dialect.identifier_preparer
    return f"{preparer.quote(schema)}.{preparer.quote('masters')}"


def upgrade() -> None:
    masters_table = _qualified_masters_table()

    op.execute(sa.text(f"ALTER TABLE {masters_table} ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT"))
    op.execute(sa.text(f"ALTER TABLE {masters_table} ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255)"))
    op.execute(sa.text(f"CREATE INDEX IF NOT EXISTS ix_masters_telegram_user_id ON {masters_table} (telegram_user_id)"))
    op.execute(sa.text(f"CREATE INDEX IF NOT EXISTS ix_masters_telegram_chat_id ON {masters_table} (telegram_chat_id)"))


def downgrade() -> None:
    masters_table = _qualified_masters_table()

    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_chat_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_masters_telegram_user_id"))
    op.execute(sa.text(f"ALTER TABLE {masters_table} DROP COLUMN IF EXISTS telegram_username"))
    op.execute(sa.text(f"ALTER TABLE {masters_table} DROP COLUMN IF EXISTS telegram_chat_id"))
