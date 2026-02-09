from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db import get_db
from app.models import Booking, BookingStatus, Notification, Service, ServiceCategory, Setting
from app.schemas import (
    BookingOut,
    BookingUpdate,
    NotificationOut,
    ServiceCategoryCreate,
    ServiceCategoryOut,
    ServiceCategoryUpdate,
    ServiceCreate,
    ServiceOut,
    ServiceUpdate,
    SettingOut,
    SettingUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/services", response_model=list[ServiceOut])
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).options(selectinload(Service.category)).order_by(Service.sort_order, Service.title))
    return result.scalars().all()


@router.post("/services", response_model=ServiceOut)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)):
    service = Service(**payload.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.put("/services/{service_id}", response_model=ServiceOut)
async def update_service(service_id: int, payload: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/services/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    await db.delete(service)
    await db.commit()
    return {"status": "deleted"}


@router.get("/categories", response_model=list[ServiceCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).order_by(ServiceCategory.sort_order, ServiceCategory.title))
    return result.scalars().all()


@router.post("/categories", response_model=ServiceCategoryOut)
async def create_category(payload: ServiceCategoryCreate, db: AsyncSession = Depends(get_db)):
    category = ServiceCategory(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=ServiceCategoryOut)
async def update_category(category_id: int, payload: ServiceCategoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await db.delete(category)
    await db.commit()
    return {"status": "deleted"}


@router.get("/settings/{key}", response_model=SettingOut)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in {"business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return setting


@router.put("/settings/{key}", response_model=SettingOut)
async def update_setting(key: str, payload: SettingUpdate, db: AsyncSession = Depends(get_db)):
    if key not in {"business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting key")
    if not isinstance(payload.value_jsonb, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting value")
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value_jsonb = payload.value_jsonb
    else:
        setting = Setting(key=key, value_jsonb=payload.value_jsonb)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


@router.get("/bookings", response_model=list[BookingOut])
async def list_bookings(
    status: str | None = None,
    unread: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking).order_by(Booking.starts_at.desc())
    if status:
        try:
            status_enum = BookingStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc
        query = query.where(Booking.status == status_enum)
    if unread is True:
        query = query.where(Booking.is_read.is_(False))
    if unread is False:
        query = query.where(Booking.is_read.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: int, payload: BookingUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] is not None:
        try:
            updates["status"] = BookingStatus(updates["status"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc
    for key, value in updates.items():
        setattr(booking, key, value)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).order_by(Notification.created_at.desc()))
    return result.scalars().all()
