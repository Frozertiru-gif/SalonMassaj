from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool


class ServiceCategoryBase(BaseModel):
    title: str
    slug: str
    sort_order: int = 0
    is_active: bool = True


class ServiceCategoryCreate(ServiceCategoryBase):
    pass


class ServiceCategoryUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ServiceCategoryOut(ServiceCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ServiceBase(BaseModel):
    category_id: int
    title: str
    slug: str
    short_description: str
    description: str
    duration_min: int
    price_from: int
    price_to: int | None = None
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    sort_order: int = 0
    seo_title: str | None = None
    seo_description: str | None = None


class ServiceCreate(ServiceBase):
    slug: str | None = None


class ServiceUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = None
    slug: str | None = None
    short_description: str | None = None
    description: str | None = None
    duration_min: int | None = None
    price_from: int | None = None
    price_to: int | None = None
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    image_url: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    seo_title: str | None = None
    seo_description: str | None = None


class ServiceOut(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    category: ServiceCategoryOut | None = None


class MasterBase(BaseModel):
    name: str
    photo_url: str | None = None
    short_bio: str | None = None
    bio: str | None = None
    is_active: bool = True
    sort_order: int = 0
    service_ids: list[int] = Field(default_factory=list)


class MasterCreate(MasterBase):
    pass


class MasterUpdate(BaseModel):
    name: str | None = None
    photo_url: str | None = None
    short_bio: str | None = None
    bio: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    service_ids: list[int] | None = None




class MasterPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    photo_url: str | None = None
    short_bio: str | None = None
    bio: str | None = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    services: list[ServiceOut] = Field(default_factory=list)


class MasterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    photo_url: str | None = None
    short_bio: str | None = None
    bio: str | None = None
    is_active: bool
    sort_order: int
    telegram_user_id: int | None = None
    telegram_link_code: str | None = None
    telegram_linked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    services: list[ServiceOut] = Field(default_factory=list)


class MasterTelegramLinkOut(BaseModel):
    master_id: int
    code: str
    bot_start_link: str | None = None


class MasterTelegramUnlinkOut(BaseModel):
    master_id: int
    unlinked: bool


class WeeklyRitualBase(BaseModel):
    title: str
    slug: str | None = None
    short_description: str | None = None
    description: str
    image_url: str | None = None
    cta_text: str | None = None
    cta_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
    sort_order: int = 0


class WeeklyRitualCreate(WeeklyRitualBase):
    pass


class WeeklyRitualUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    short_description: str | None = None
    description: str | None = None
    image_url: str | None = None
    cta_text: str | None = None
    cta_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class WeeklyRitualOut(WeeklyRitualBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ReviewBase(BaseModel):
    author_name: str
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str
    source: str | None = None
    source_url: str | None = None
    review_date: date | None = None
    is_published: bool = True
    sort_order: int = 0


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    author_name: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str | None = None
    source: str | None = None
    source_url: str | None = None
    review_date: date | None = None
    is_published: bool | None = None
    sort_order: int | None = None


class ReviewOut(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class SettingOut(BaseModel):
    key: str
    value_jsonb: dict[str, Any]
    updated_at: datetime | None = None


class SettingUpdate(BaseModel):
    value_jsonb: dict[str, Any]


class TgNotificationsSettings(BaseModel):
    enabled: bool = False
    admin_chat_id: str | int | None = None
    admin_thread_id: int | None = None
    template_admin: str = "Новая запись: {client_name} ({client_phone})\nУслуга: {service_title}\n{starts_at_human}"
    send_inline_actions: bool = True
    public_webhook_base_url: str | None = None
    webhook_secret: str | None = None


class TelegramTestMessageIn(BaseModel):
    text: str = "Тестовое сообщение из админ-панели SalonMassaj"


class TelegramTestMessageOut(BaseModel):
    ok: bool
    detail: str


class BookingBase(BaseModel):
    client_name: str
    client_phone: str
    service_id: int
    starts_at: datetime
    comment: str | None = None
    master_id: int | None = None


class BookingCreate(BookingBase):
    starts_at: datetime | None = None
    date: date | str | None = None
    time: time | str | None = None


class BookingOut(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ends_at: datetime
    status: str
    source: str
    is_read: bool
    admin_comment: str | None = None
    final_price_cents: int | None = Field(default=None, ge=0)
    created_at: datetime
    service: ServiceOut | None = None
    master: MasterPublicOut | None = None


class BookingUpdate(BaseModel):
    status: str | None = None
    is_read: bool | None = None
    master_id: int | None = None
    admin_comment: str | None = None
    final_price_cents: int | None = Field(default=None, ge=0)


class BookingAdminCreate(BaseModel):
    client_name: str | None = None
    client_phone: str
    service_id: int
    master_id: int | None = None
    date: date
    time: time
    comment: str | None = None
    status: str = "NEW"


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime


class AvailabilitySlot(BaseModel):
    starts_at: datetime
    ends_at: datetime


class AvailabilityOut(BaseModel):
    slots: list[AvailabilitySlot]


class BookingSlotOut(BaseModel):
    time: str
    starts_at: datetime
    ends_at: datetime
