from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import nullslast
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Booking, BookingStatus, Master, Notification, NotificationType, Review, Service, ServiceCategory, WeeklyRitual
from app.schemas import (
    AvailabilityOut,
    BookingCreate,
    BookingOut,
    BookingSlotOut,
    MasterPublicOut,
    ReviewOut,
    ServiceCategoryOut,
    ServiceOut,
    WeeklyRitualOut,
)
from app.services.bookings import booking_validation_error, normalize_booking_start, resolve_available_slot
from app.services.telegram import build_booking_notification_payload, send_booking_created_to_admin
from app.utils import get_availability_slots, get_setting

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


@router.get("/masters", response_model=list[MasterPublicOut])
async def list_masters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Master)
        .where(Master.is_active.is_(True))
        .options(selectinload(Master.services).selectinload(Service.category))
        .order_by(Master.sort_order, Master.name)
    )
    return result.scalars().all()


@router.get("/masters/{slug}", response_model=MasterPublicOut)
async def get_master(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Master)
        .where(Master.slug == slug, Master.is_active.is_(True))
        .options(selectinload(Master.services).selectinload(Service.category))
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master not found")
    return master


@router.get("/categories", response_model=list[ServiceCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.is_active.is_(True)))
    return result.scalars().all()


@router.get("/weekly-rituals", response_model=list[WeeklyRitualOut])
async def list_weekly_rituals(db: AsyncSession = Depends(get_db)):
    today = date.today()
    query = select(WeeklyRitual).where(
        WeeklyRitual.is_active.is_(True),
        or_(WeeklyRitual.start_date.is_(None), WeeklyRitual.start_date <= today),
        or_(WeeklyRitual.end_date.is_(None), WeeklyRitual.end_date >= today),
    )
    result = await db.execute(query.order_by(WeeklyRitual.sort_order, WeeklyRitual.created_at.desc()))
    return result.scalars().all()


@router.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    query = (
        select(Review)
        .where(Review.is_published.is_(True))
        .order_by(Review.sort_order, nullslast(Review.review_date.desc()), Review.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/availability", response_model=AvailabilityOut)
async def get_availability(service_id: int, date: date, master_id: int | None = None, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    slots = await get_availability_slots(db, service_id, date, now, master_id=master_id)
    return {"slots": [{"starts_at": slot[0], "ends_at": slot[1]} for slot in slots]}


@router.get("/bookings/slots", response_model=list[BookingSlotOut])
async def get_booking_slots(service_id: int, date: date, master_id: int | None = None, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    slots = await get_availability_slots(db, service_id, date, now, master_id=master_id)
    return [{"time": slot[0].strftime("%H:%M"), "starts_at": slot[0], "ends_at": slot[1]} for slot in slots]


@router.get("/settings/{key}")
async def get_public_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in {"contacts"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    value = await get_setting(db, key)
    return {"key": key, "value_jsonb": value}


@router.post("/bookings", response_model=BookingOut)
async def create_booking(payload: BookingCreate, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    try:
        requested_start = normalize_booking_start(payload.starts_at, payload.date, payload.time)
    except ValueError as exc:
        raise booking_validation_error(str(exc)) from exc

    chosen = await resolve_available_slot(db, payload.service_id, requested_start, now, master_id=payload.master_id)

    booking = Booking(
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        service_id=payload.service_id,
        master_id=payload.master_id,
        starts_at=chosen[0],
        ends_at=chosen[1],
        comment=payload.comment,
        status=BookingStatus.new,
    )
    db.add(booking)
    await db.flush()

    booking_result = await db.execute(
        select(Booking)
        .where(Booking.id == booking.id)
        .options(
            selectinload(Booking.service),
            selectinload(Booking.service).selectinload(Service.category),
            selectinload(Booking.master).selectinload(Master.services),
        )
    )
    booking_full = booking_result.scalar_one()

    notification = await build_booking_notification_payload(db, booking_full)

    db.add(Notification(type=NotificationType.booking_created, payload=notification, is_read=False))

    await send_booking_created_to_admin(db, booking.id)

    return booking_full
