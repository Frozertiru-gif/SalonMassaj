import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db import get_db
from app.models import Booking, BookingStatus, Notification, Review, Service, ServiceCategory, Setting, WeeklyRitual
from app.schemas import (
    BookingOut,
    BookingUpdate,
    NotificationOut,
    ReviewCreate,
    ReviewOut,
    ReviewUpdate,
    ServiceCategoryCreate,
    ServiceCategoryOut,
    ServiceCategoryUpdate,
    ServiceCreate,
    ServiceOut,
    ServiceUpdate,
    SettingOut,
    SettingUpdate,
    WeeklyRitualCreate,
    WeeklyRitualOut,
    WeeklyRitualUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


CYRILLIC_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def normalize_slug(value: str) -> str:
    value = value.strip().lower()
    transliterated = "".join(CYRILLIC_TRANSLIT.get(char, char) for char in value)
    slug = re.sub(r"[^a-z0-9\s-]", "", transliterated)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "service"


def slug_candidates(base_slug: str):
    yield base_slug
    suffix = 2
    while True:
        yield f"{base_slug}-{suffix}"
        suffix += 1


@router.get("/services", response_model=list[ServiceOut])
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).options(selectinload(Service.category)).order_by(Service.sort_order, Service.title))
    return result.scalars().all()


@router.post("/services", response_model=ServiceOut)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)):
    payload_data = payload.model_dump()
    raw_slug = payload.slug
    base_slug = normalize_slug((raw_slug or payload.title) or "")
    if not base_slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug cannot be empty")

    candidates = [base_slug] if raw_slug else slug_candidates(base_slug)
    for candidate in candidates:
        payload_data["slug"] = candidate
        try:
            async with db.begin():
                service = Service(**payload_data)
                db.add(service)
                await db.flush()
                result = await db.execute(
                    select(Service).options(selectinload(Service.category)).where(Service.id == service.id)
                )
                service_out = ServiceOut.model_validate(result.scalar_one())
            return service_out
        except IntegrityError as exc:
            if raw_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists"
                ) from exc
            continue
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists")


@router.put("/services/{service_id}", response_model=ServiceOut)
async def update_service(service_id: int, payload: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] is not None:
        normalized = normalize_slug(updates["slug"])
        if not normalized:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug cannot be empty")
        exists = await db.execute(select(Service.id).where(Service.slug == normalized, Service.id != service_id))
        if exists.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists")
        updates["slug"] = normalized
    for key, value in updates.items():
        setattr(service, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists") from exc
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
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists") from exc
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=ServiceCategoryOut)
async def update_category(category_id: int, payload: ServiceCategoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] is not None:
        existing = await db.execute(
            select(ServiceCategory.id).where(ServiceCategory.slug == updates["slug"], ServiceCategory.id != category_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists")
    for key, value in updates.items():
        setattr(category, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists") from exc
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).where(ServiceCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    services = await db.execute(select(Service.id).where(Service.category_id == category_id).limit(1))
    if services.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category has services. Move or delete them before removing the category",
        )
    await db.delete(category)
    await db.commit()
    return {"status": "deleted"}


@router.get("/weekly-rituals", response_model=list[WeeklyRitualOut])
async def list_weekly_rituals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyRitual).order_by(WeeklyRitual.sort_order, WeeklyRitual.created_at.desc()))
    return result.scalars().all()


@router.post("/weekly-rituals", response_model=WeeklyRitualOut)
async def create_weekly_ritual(payload: WeeklyRitualCreate, db: AsyncSession = Depends(get_db)):
    if payload.start_date and payload.end_date and payload.start_date > payload.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date")
    ritual = WeeklyRitual(**payload.model_dump())
    db.add(ritual)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weekly ritual with this slug already exists") from exc
    await db.refresh(ritual)
    return ritual


@router.put("/weekly-rituals/{ritual_id}", response_model=WeeklyRitualOut)
async def update_weekly_ritual(ritual_id: int, payload: WeeklyRitualUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyRitual).where(WeeklyRitual.id == ritual_id))
    ritual = result.scalar_one_or_none()
    if not ritual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly ritual not found")
    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] is not None:
        existing = await db.execute(
            select(WeeklyRitual.id).where(WeeklyRitual.slug == updates["slug"], WeeklyRitual.id != ritual_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weekly ritual with this slug already exists")
    new_start = updates.get("start_date", ritual.start_date)
    new_end = updates.get("end_date", ritual.end_date)
    if new_start and new_end and new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date")
    for key, value in updates.items():
        setattr(ritual, key, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weekly ritual with this slug already exists") from exc
    await db.refresh(ritual)
    return ritual


@router.delete("/weekly-rituals/{ritual_id}")
async def delete_weekly_ritual(ritual_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyRitual).where(WeeklyRitual.id == ritual_id))
    ritual = result.scalar_one_or_none()
    if not ritual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly ritual not found")
    await db.delete(ritual)
    await db.commit()
    return {"status": "deleted"}


@router.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).order_by(Review.sort_order, Review.created_at.desc()))
    return result.scalars().all()


@router.post("/reviews", response_model=ReviewOut)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    review = Review(**payload.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.put("/reviews/{review_id}", response_model=ReviewOut)
async def update_review(review_id: int, payload: ReviewUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, key, value)
    await db.commit()
    await db.refresh(review)
    return review


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    await db.delete(review)
    await db.commit()
    return {"status": "deleted"}


@router.get("/settings/{key}", response_model=SettingOut)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in {"business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"key": key, "value_jsonb": {}, "updated_at": None}
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
