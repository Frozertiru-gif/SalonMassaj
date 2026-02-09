from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Service, Setting

DAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


async def get_setting(db: AsyncSession, key: str) -> dict:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value_jsonb if setting else {}


def parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


async def get_availability_slots(
    db: AsyncSession,
    service_id: int,
    target_date: date,
    now: datetime,
) -> list[tuple[datetime, datetime]]:
    service_result = await db.execute(select(Service).where(Service.id == service_id))
    service = service_result.scalar_one_or_none()
    if not service:
        return []

    business_hours = await get_setting(db, "business_hours")
    slot_step_min = await get_setting(db, "slot_step_min")
    booking_rules = await get_setting(db, "booking_rules")

    day_key = DAY_MAP[target_date.weekday()]
    ranges = business_hours.get(day_key, [])
    step = int(slot_step_min.get("value", 30)) if isinstance(slot_step_min, dict) else int(slot_step_min or 30)
    min_lead = int(booking_rules.get("min_lead_min", 0))
    max_days = int(booking_rules.get("max_days_ahead", 60))

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

    result = await db.execute(
        select(Booking).where(
            Booking.service_id == service_id,
            Booking.status.in_([BookingStatus.new, BookingStatus.confirmed]),
            Booking.starts_at < slots[-1][1],
            Booking.ends_at > slots[0][0],
        )
    )
    bookings = result.scalars().all()

    available: list[tuple[datetime, datetime]] = []
    for slot_start, slot_end in slots:
        overlaps = any(
            booking.starts_at < slot_end and booking.ends_at > slot_start for booking in bookings
        )
        if not overlaps:
            available.append((slot_start, slot_end))
    return available
