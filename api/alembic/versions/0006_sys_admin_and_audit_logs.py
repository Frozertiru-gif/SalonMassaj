"""add sys admin role and audit logs

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    with op.get_context().autocommit_block():
        sys_admin_exists = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_enum e ON e.enumtypid = t.oid
                    WHERE t.typname = 'adminrole'
                      AND e.enumlabel = 'SYS_ADMIN'
                )
                """
            )
        ).scalar()
        if not sys_admin_exists:
            op.execute("ALTER TYPE adminrole ADD VALUE 'SYS_ADMIN'")

    admins_table_exists = bind.execute(
        sa.text("SELECT to_regclass('public.admins') IS NOT NULL")
    ).scalar()
    if admins_table_exists:
        op.execute("UPDATE admins SET role = 'SYS_ADMIN' WHERE role = 'OWNER'")

    adminrole_enum = postgresql.ENUM(name="adminrole", create_type=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_tg_user_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_role", adminrole_enum, nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["admins.id"], name="fk_audit_logs_actor_user_id_admins"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_entity_type_entity_id", "audit_logs", ["entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_type_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    bind = op.get_bind()
    admins_table_exists = bind.execute(
        sa.text("SELECT to_regclass('public.admins') IS NOT NULL")
    ).scalar()
    if admins_table_exists:
        op.execute("UPDATE admins SET role = 'OWNER' WHERE role = 'SYS_ADMIN'")
