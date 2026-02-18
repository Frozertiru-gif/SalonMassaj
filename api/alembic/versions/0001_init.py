"""init

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    adminrole_enum = postgresql.ENUM("OWNER", "ADMIN", name="adminrole", create_type=False)
    bookingstatus_enum = postgresql.ENUM(
        "NEW", "CONFIRMED", "CANCELLED", "DONE", name="bookingstatus", create_type=False
    )
    notificationtype_enum = postgresql.ENUM("BOOKING_CREATED", name="notificationtype", create_type=False)

    bind = op.get_bind()
    adminrole_enum.create(bind, checkfirst=True)
    bookingstatus_enum.create(bind, checkfirst=True)
    notificationtype_enum.create(bind, checkfirst=True)

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", adminrole_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_admins_email", "admins", ["email"], unique=True)

    op.create_table(
        "service_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_service_categories_slug", "service_categories", ["slug"], unique=True)

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("service_categories.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("price_from", sa.Integer(), nullable=False),
        sa.Column("price_to", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_services_slug", "services", ["slug"], unique=True)

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=255), primary_key=True),
        sa.Column("value_jsonb", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("client_phone", sa.String(length=50), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", bookingstatus_enum, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="WEB"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_bookings_starts_at", "bookings", ["starts_at"], unique=False)
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)
    op.create_index("ix_bookings_is_read", "bookings", ["is_read"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", notificationtype_enum, nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    adminrole_enum = postgresql.ENUM("OWNER", "ADMIN", name="adminrole", create_type=False)
    bookingstatus_enum = postgresql.ENUM(
        "NEW", "CONFIRMED", "CANCELLED", "DONE", name="bookingstatus", create_type=False
    )
    notificationtype_enum = postgresql.ENUM("BOOKING_CREATED", name="notificationtype", create_type=False)

    op.drop_table("notifications")
    op.drop_index("ix_bookings_is_read", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_starts_at", table_name="bookings")
    op.drop_table("bookings")
    op.drop_table("settings")
    op.drop_index("ix_services_slug", table_name="services")
    op.drop_table("services")
    op.drop_index("ix_service_categories_slug", table_name="service_categories")
    op.drop_table("service_categories")
    op.drop_index("ix_admins_email", table_name="admins")
    op.drop_table("admins")
    bind = op.get_bind()
    notificationtype_enum.drop(bind, checkfirst=True)
    bookingstatus_enum.drop(bind, checkfirst=True)
    adminrole_enum.drop(bind, checkfirst=True)
