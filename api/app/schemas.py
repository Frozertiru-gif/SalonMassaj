from datetime import datetime
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
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    sort_order: int = 0
    seo_title: str | None = None
    seo_description: str | None = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = None
    slug: str | None = None
    short_description: str | None = None
    description: str | None = None
    duration_min: int | None = None
    price_from: int | None = None
    price_to: int | None = None
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


class SettingOut(BaseModel):
    key: str
    value_jsonb: dict[str, Any]
    updated_at: datetime


class SettingUpdate(BaseModel):
    value_jsonb: dict[str, Any]


class BookingBase(BaseModel):
    client_name: str
    client_phone: str
    service_id: int
    starts_at: datetime
    comment: str | None = None


class BookingCreate(BookingBase):
    pass


class BookingOut(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ends_at: datetime
    status: str
    source: str
    is_read: bool
    created_at: datetime
    service: ServiceOut | None = None


class BookingUpdate(BaseModel):
    status: str | None = None
    is_read: bool | None = None


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
