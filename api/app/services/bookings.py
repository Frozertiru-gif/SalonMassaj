from datetime import date, datetime, time

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import get_availability_slots


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("date must be in YYYY-MM-DD or DD.MM.YYYY format")


def _parse_time(value: str) -> time:
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    raise ValueError("time must be in HH:MM format")


def normalize_booking_start(starts_at: datetime | None = None, booking_date: str | date | None = None, booking_time: str | time | None = None) -> datetime:
    if starts_at is not None:
        return starts_at.replace(tzinfo=None, second=0, microsecond=0)

    if booking_date is None:
        raise ValueError("field 'starts_at' is required")

    if isinstance(booking_date, str):
        parsed_date = _parse_date(booking_date)
    else:
        parsed_date = booking_date

    if booking_time is None:
        raise ValueError("field 'time' is required when 'starts_at' is not provided")

    if isinstance(booking_time, str):
        parsed_time = _parse_time(booking_time)
    else:
        parsed_time = booking_time.replace(second=0, microsecond=0)

    return datetime.combine(parsed_date, parsed_time)


async def resolve_available_slot(
    db: AsyncSession,
    service_id: int,
    requested_start: datetime,
    now: datetime,
    master_id: int | None = None,
) -> tuple[datetime, datetime]:
    slots = await get_availability_slots(db, service_id, requested_start.date(), now, master_id=master_id)
    for slot_start, slot_end in slots:
        if slot_start == requested_start:
            return slot_start, slot_end
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="slot busy")


def booking_validation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
