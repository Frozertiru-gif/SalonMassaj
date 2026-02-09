import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class AdminRole(str, enum.Enum):
    owner = "OWNER"
    admin = "ADMIN"


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


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value_jsonb: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255))
    client_phone: Mapped[str] = mapped_column(String(50))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[BookingStatus] = mapped_column(BOOKING_STATUS_ENUM, default=BookingStatus.new)
    source: Mapped[str] = mapped_column(String(50), default="WEB")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service: Mapped[Service] = relationship()

    __table_args__ = (
        Index("ix_bookings_starts_at", "starts_at"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_is_read", "is_read"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[NotificationType] = mapped_column(NOTIFICATION_TYPE_ENUM)
    payload: Mapped[dict] = mapped_column(JSONB)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "Admin",
    "AdminRole",
    "Base",
    "Booking",
    "BookingStatus",
    "Notification",
    "NotificationType",
    "Service",
    "ServiceCategory",
    "Setting",
]
