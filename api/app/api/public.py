from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.sql import nullslast
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Booking, BookingStatus, Notification, NotificationType, Review, Service, ServiceCategory, WeeklyRitual
from app.schemas import AvailabilityOut, BookingCreate, BookingOut, BookingSlotOut, ReviewOut, ServiceCategoryOut, ServiceOut, WeeklyRitualOut
from app.utils import get_availability_slots, get_setting
from app.services.bookings import booking_validation_error, normalize_booking_start, resolve_available_slot
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
async def get_availability(service_id: int, date: date, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    slots = await get_availability_slots(db, service_id, date, now)
    return {"slots": [{"starts_at": slot[0], "ends_at": slot[1]} for slot in slots]}


@router.get("/bookings/slots", response_model=list[BookingSlotOut])
async def get_booking_slots(service_id: int, date: date, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    slots = await get_availability_slots(db, service_id, date, now)
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

    chosen = await resolve_available_slot(db, payload.service_id, requested_start, now)

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
    await db.flush()

    notification = {
        "booking_id": booking.id,
        "service_id": booking.service_id,
        "starts_at": booking.starts_at.isoformat(),
        "client_name": booking.client_name,
        "client_phone": booking.client_phone,
    }

    db.add(Notification(type=NotificationType.booking_created, payload=notification, is_read=False))

    await send_booking_notification(db, notification)

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking.id)
        .options(selectinload(Booking.service), selectinload(Booking.service).selectinload(Service.category))
    )
    return result.scalar_one()
