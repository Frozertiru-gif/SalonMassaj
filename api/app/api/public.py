from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Booking, BookingStatus, Notification, NotificationType, Service, ServiceCategory
from app.schemas import AvailabilityOut, BookingCreate, BookingOut, ServiceCategoryOut, ServiceOut
from app.utils import get_availability_slots, get_setting
from app.services.telegram import send_booking_notification

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/services", response_model=list[ServiceOut])
async def list_services(category: str | None = None, active: bool = True, db: AsyncSession = Depends(get_db)):
    query = select(Service)
    if category:
        query = query.join(ServiceCategory).where(ServiceCategory.slug == category)
    if active:
        query = query.where(Service.is_active.is_(True))
    result = await db.execute(query.options(selectinload(Service.category)).order_by(Service.sort_order, Service.title))
    return result.scalars().all()


@router.get("/services/{slug}", response_model=ServiceOut)
async def get_service(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).options(selectinload(Service.category)).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.get("/categories", response_model=list[ServiceCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.is_active.is_(True)))
    return result.scalars().all()


@router.get("/availability", response_model=AvailabilityOut)
async def get_availability(service_id: int, date: date, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    slots = await get_availability_slots(db, service_id, date, now)
    return {"slots": [{"starts_at": slot[0], "ends_at": slot[1]} for slot in slots]}


@router.get("/settings/{key}")
async def get_public_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in {"contacts"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    value = await get_setting(db, key)
    return {"key": key, "value_jsonb": value}


@router.post("/bookings", response_model=BookingOut)
async def create_booking(payload: BookingCreate, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    available = await get_availability_slots(db, payload.service_id, payload.starts_at.date(), now)
    chosen = None
    for slot in available:
        if slot[0] == payload.starts_at:
            chosen = slot
            break
    if not chosen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot unavailable")

    booking = Booking(
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        service_id=payload.service_id,
        starts_at=chosen[0],
        ends_at=chosen[1],
        comment=payload.comment,
        status=BookingStatus.new,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    notification = {
        "booking_id": booking.id,
        "service_id": booking.service_id,
        "starts_at": booking.starts_at.isoformat(),
        "client_name": booking.client_name,
        "client_phone": booking.client_phone,
    }

    db.add(Notification(type=NotificationType.booking_created, payload=notification, is_read=False))
    await db.commit()

    await send_booking_notification(db, notification)

    return booking
