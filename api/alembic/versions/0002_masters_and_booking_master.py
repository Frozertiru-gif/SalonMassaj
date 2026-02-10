"""masters and booking master relation

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "masters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("short_bio", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_masters_slug", "masters", ["slug"], unique=True)

    op.create_table(
        "master_services",
        sa.Column("master_id", sa.Integer(), sa.ForeignKey("masters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("master_id", "service_id", name="uq_master_services_master_id_service_id"),
    )

    op.add_column("bookings", sa.Column("master_id", sa.Integer(), nullable=True))
    op.add_column("bookings", sa.Column("admin_comment", sa.Text(), nullable=True))
    op.create_foreign_key("fk_bookings_master_id", "bookings", "masters", ["master_id"], ["id"])
    op.create_index("ix_bookings_master_id", "bookings", ["master_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_bookings_master_id", table_name="bookings")
    op.drop_constraint("fk_bookings_master_id", "bookings", type_="foreignkey")
    op.drop_column("bookings", "admin_comment")
    op.drop_column("bookings", "master_id")

    op.drop_table("master_services")
    op.drop_index("ix_masters_slug", table_name="masters")
    op.drop_table("masters")
