from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Master, Service, Setting, master_services

DAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}

DEFAULT_BUSINESS_HOURS = {
    "mon": [{"start": "10:00", "end": "21:00"}],
    "tue": [{"start": "10:00", "end": "21:00"}],
    "wed": [{"start": "10:00", "end": "21:00"}],
    "thu": [{"start": "10:00", "end": "21:00"}],
    "fri": [{"start": "10:00", "end": "21:00"}],
    "sat": [{"start": "10:00", "end": "21:00"}],
    "sun": [{"start": "10:00", "end": "21:00"}],
}

DEFAULT_SLOT_STEP_MIN = 30
DEFAULT_BOOKING_RULES = {"min_lead_min": 0, "max_days_ahead": 60}


async def get_setting(db: AsyncSession, key: str) -> dict:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value_jsonb if setting else {}


def parse_date_param(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError as exc:
        raise ValueError("Invalid date format. Use YYYY-MM-DD or DD.MM.YYYY.") from exc


def parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


async def _service_exists(db: AsyncSession, service_id: int) -> Service | None:
    service_result = await db.execute(select(Service).where(Service.id == service_id))
    return service_result.scalar_one_or_none()


async def get_service_master_ids(db: AsyncSession, service_id: int) -> list[int]:
    query = (
        select(Master.id)
        .join(master_services, master_services.c.master_id == Master.id)
        .where(master_services.c.service_id == service_id, Master.is_active.is_(True))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_availability_slots(
    db: AsyncSession,
    service_id: int,
    target_date: date,
    now: datetime,
    master_id: int | None = None,
) -> list[tuple[datetime, datetime]]:
    service = await _service_exists(db, service_id)
    if not service:
        return []

    business_hours_setting = await get_setting(db, "business_hours")
    slot_step_min_setting = await get_setting(db, "slot_step_min")
    booking_rules_setting = await get_setting(db, "booking_rules")

    business_hours = business_hours_setting if isinstance(business_hours_setting, dict) and business_hours_setting else DEFAULT_BUSINESS_HOURS

    day_key = DAY_MAP[target_date.weekday()]
    ranges = business_hours.get(day_key, [])
    if not ranges:
        ranges = DEFAULT_BUSINESS_HOURS.get(day_key, [])
    step = (
        int(slot_step_min_setting.get("value", DEFAULT_SLOT_STEP_MIN))
        if isinstance(slot_step_min_setting, dict)
        else int(slot_step_min_setting or DEFAULT_SLOT_STEP_MIN)
    )
    booking_rules = booking_rules_setting if isinstance(booking_rules_setting, dict) else DEFAULT_BOOKING_RULES
    min_lead = int(booking_rules.get("min_lead_min", DEFAULT_BOOKING_RULES["min_lead_min"]))
    max_days = int(booking_rules.get("max_days_ahead", DEFAULT_BOOKING_RULES["max_days_ahead"]))

    if target_date > (now.date() + timedelta(days=max_days)):
        return []

    slots: list[tuple[datetime, datetime]] = []
    duration = timedelta(minutes=service.duration_min)
    for day_range in ranges:
        start_time = parse_time(day_range["start"])
        end_time = parse_time(day_range["end"])
        start_dt = datetime.combine(target_date, start_time, tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, end_time, tzinfo=timezone.utc)
        cursor = start_dt
        while cursor + duration <= end_dt:
            slot_start = cursor
            slot_end = cursor + duration
            if slot_start >= now + timedelta(minutes=min_lead):
                slots.append((slot_start, slot_end))
            cursor += timedelta(minutes=step)

    if not slots:
        return []

    from_dt = slots[0][0]
    to_dt = slots[-1][1]

    base_booking_filter = [
        Booking.status.in_([BookingStatus.new, BookingStatus.confirmed]),
        Booking.starts_at < to_dt,
        Booking.ends_at > from_dt,
    ]

    if master_id is not None:
        master_exists = await db.execute(
            select(Master.id)
            .join(master_services, and_(master_services.c.master_id == Master.id, master_services.c.service_id == service_id))
            .where(Master.id == master_id, Master.is_active.is_(True))
        )
        if master_exists.scalar_one_or_none() is None:
            return []

        result = await db.execute(select(Booking).where(*base_booking_filter, Booking.master_id == master_id))
        bookings = result.scalars().all()
        return [
            (slot_start, slot_end)
            for slot_start, slot_end in slots
            if not any(booking.starts_at < slot_end and booking.ends_at > slot_start for booking in bookings)
        ]

    master_ids = await get_service_master_ids(db, service_id)
    if not master_ids:
        return []

    result = await db.execute(select(Booking).where(*base_booking_filter))
    bookings = result.scalars().all()

    available: list[tuple[datetime, datetime]] = []
    for slot_start, slot_end in slots:
        occupied_master_ids = {
            booking.master_id
            for booking in bookings
            if booking.master_id is not None and booking.master_id in master_ids and booking.starts_at < slot_end and booking.ends_at > slot_start
        }
        unassigned_overlaps = sum(
            1
            for booking in bookings
            if booking.master_id is None and booking.starts_at < slot_end and booking.ends_at > slot_start
        )
        free_capacity = len(master_ids) - len(occupied_master_ids) - unassigned_overlaps
        if free_capacity > 0:
            available.append((slot_start, slot_end))
    return available
