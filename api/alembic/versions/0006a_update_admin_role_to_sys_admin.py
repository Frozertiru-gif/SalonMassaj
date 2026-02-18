"""update admin role values to SYS_ADMIN

Revision ID: 0006a_update_admin_role_to_sys_admin
Revises: 0006
Create Date: 2026-02-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006a_update_admin_role_to_sys_admin"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    admins_table_exists = bind.execute(sa.text("SELECT to_regclass('public.admins') IS NOT NULL")).scalar()
    if admins_table_exists:
        bind.execute(sa.text("UPDATE admins SET role = 'SYS_ADMIN' WHERE role = 'OWNER'"))


def downgrade() -> None:
    bind = op.get_bind()
    admins_table_exists = bind.execute(sa.text("SELECT to_regclass('public.admins') IS NOT NULL")).scalar()
    if admins_table_exists:
        bind.execute(sa.text("UPDATE admins SET role = 'OWNER' WHERE role = 'SYS_ADMIN'"))
