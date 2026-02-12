import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class AdminRole(str, enum.Enum):
    admin = "ADMIN"
    sys_admin = "SYS_ADMIN"


class BookingStatus(str, enum.Enum):
    new = "NEW"
    confirmed = "CONFIRMED"
    cancelled = "CANCELLED"
    done = "DONE"


class NotificationType(str, enum.Enum):
    booking_created = "BOOKING_CREATED"


# Use values_callable so SQLAlchemy persists enum .value (e.g. "OWNER") matching Postgres enums.
ADMIN_ROLE_ENUM = Enum(
    AdminRole,
    name="adminrole",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
    native_enum=True,
    validate_strings=True,
)
BOOKING_STATUS_ENUM = Enum(
    BookingStatus,
    name="bookingstatus",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
    native_enum=True,
    validate_strings=True,
)
NOTIFICATION_TYPE_ENUM = Enum(
    NotificationType,
    name="notificationtype",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
    native_enum=True,
    validate_strings=True,
)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[AdminRole] = mapped_column(ADMIN_ROLE_ENUM, default=AdminRole.admin)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    services: Mapped[list["Service"]] = relationship(back_populates="category")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    short_description: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    duration_min: Mapped[int] = mapped_column(Integer)
    price_from: Mapped[int] = mapped_column(Integer)
    price_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[ServiceCategory] = relationship(back_populates="services")
    masters: Mapped[list["Master"]] = relationship(secondary="master_services", back_populates="services")


master_services = Table(
    "master_services",
    Base.metadata,
    Column("master_id", ForeignKey("masters.id"), primary_key=True),
    Column("service_id", ForeignKey("services.id"), primary_key=True),
    UniqueConstraint("master_id", "service_id", name="uq_master_services_master_id_service_id"),
)


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    short_bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_link_code: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    telegram_linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    services: Mapped[list[Service]] = relationship(secondary="master_services", back_populates="masters")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value_jsonb: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WeeklyRitual(Base):
    __tablename__ = "weekly_rituals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cta_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cta_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_name: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255))
    client_phone: Mapped[str] = mapped_column(String(50))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    master_id: Mapped[int | None] = mapped_column(ForeignKey("masters.id"), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[BookingStatus] = mapped_column(BOOKING_STATUS_ENUM, default=BookingStatus.new)
    source: Mapped[str] = mapped_column(String(50), default="WEB")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service: Mapped[Service] = relationship()
    master: Mapped[Master | None] = relationship()

    __table_args__ = (
        Index("ix_bookings_starts_at", "starts_at"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_is_read", "is_read"),
        Index("ix_bookings_master_id", "master_id"),
        CheckConstraint("final_price_cents IS NULL OR final_price_cents >= 0", name="ck_bookings_final_price_cents_non_negative"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[NotificationType] = mapped_column(NOTIFICATION_TYPE_ENUM)
    payload: Mapped[dict] = mapped_column(JSONB)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditActorType(str, enum.Enum):
    web = "web"
    telegram = "telegram"
    system = "system"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actor_type: Mapped[AuditActorType] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_tg_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_role: Mapped[AdminRole | None] = mapped_column(ADMIN_ROLE_ENUM, nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_entity_type_entity_id", "entity_type", "entity_id"),
    )


__all__ = [
    "Admin",
    "AdminRole",
    "AuditActorType",
    "AuditLog",
    "Base",
    "Booking",
    "BookingStatus",
    "Notification",
    "NotificationType",
    "Master",
    "Review",
    "Service",
    "ServiceCategory",
    "Setting",
    "WeeklyRitual",
]
