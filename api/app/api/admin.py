import logging
import re
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_sys_admin
from app.core.config import settings
from app.db import get_db
from app.models import Admin, AuditActorType, AuditLog, Booking, BookingStatus, Master, Notification, Review, Service, ServiceCategory, Setting, WeeklyRitual
from app.services.bookings import resolve_available_slot
from app.services.audit import log_event
from app.services.telegram import (
    delete_webhook,
    get_tg_notifications_settings,
    get_webhook_info,
    normalize_tg_notifications,
    send_master_booking_confirmed,
    send_master_booking_rescheduled,
    send_message,
    set_webhook,
)
from app.utils import get_availability_slots, parse_date_param
from app.schemas import (
    AuditLogOut,
    BookingAdminCreate,
    BookingOut,
    BookingSlotOut,
    BookingUpdate,
    MasterCreate,
    MasterOut,
    MasterUpdate,
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
    MasterTelegramLinkOut,
    MasterTelegramUnlinkOut,
    TelegramTestMessageIn,
    TelegramTestMessageOut,
    WeeklyRitualCreate,
    WeeklyRitualOut,
    WeeklyRitualUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
logger = logging.getLogger(__name__)


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


def pick_unique_slug(base_slug: str, existing_slugs: set[str]) -> str:
    for candidate in slug_candidates(base_slug):
        if candidate not in existing_slugs:
            return candidate
    return base_slug


def _request_context(request: Request) -> tuple[str | None, str | None]:
    return request.client.host if request.client else None, request.headers.get("user-agent")


def _service_with_category_query():
    # We centralize eager-loading of Service.category because ServiceOut includes
    # nested category data. Returning ORM objects without this option can trigger
    # async lazy-load attempts during FastAPI response serialization.
    return select(Service).options(selectinload(Service.category))


@router.get("/services", response_model=list[ServiceOut])
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(_service_with_category_query().order_by(Service.sort_order, Service.title))
    return result.scalars().all()


@router.post("/services", response_model=ServiceOut)
async def create_service(payload: ServiceCreate, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    payload_data = payload.model_dump()
    base_slug = normalize_slug((payload.slug or payload.title) or "")
    existing_slugs = set(
        (await db.execute(select(Service.slug).where(Service.slug.like(f"{base_slug}%")))).scalars().all()
    )
    payload_data["slug"] = pick_unique_slug(base_slug, existing_slugs)

    try:
        service = Service(**payload_data)
        db.add(service)
        await db.flush()
        result = await db.execute(_service_with_category_query().where(Service.id == service.id))
        service_out = ServiceOut.model_validate(result.scalar_one())
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists") from exc
    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="service.create", entity_type="service", entity_id=service_out.id, meta={"title": service_out.title}, ip=ip, user_agent=user_agent)
    return service_out


@router.put("/services/{service_id}", response_model=ServiceOut)
async def update_service(service_id: int, payload: ServiceUpdate, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    updates = payload.model_dump(exclude_unset=True)
    title_for_slug = updates.get("title") or updates.get("slug")
    if title_for_slug:
        base_slug = normalize_slug(title_for_slug)
        existing_slugs = set(
            (await db.execute(select(Service.slug).where(Service.slug.like(f"{base_slug}%"), Service.id != service_id))).scalars().all()
        )
        updates["slug"] = pick_unique_slug(base_slug, existing_slugs)
    for key, value in updates.items():
        setattr(service, key, value)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service with this slug already exists") from exc
    result = await db.execute(_service_with_category_query().where(Service.id == service.id))
    service = result.scalar_one()
    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="service.update", entity_type="service", entity_id=service.id, meta={"fields": list(updates.keys())}, ip=ip, user_agent=user_agent)
    return service


@router.delete("/services/{service_id}")
async def delete_service(service_id: int, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    await db.delete(service)
    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="service.delete", entity_type="service", entity_id=service_id, ip=ip, user_agent=user_agent)
    return {"status": "deleted"}




@router.get("/masters", response_model=list[MasterOut])
async def list_masters(q: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Master).options(selectinload(Master.services).selectinload(Service.category)).order_by(Master.sort_order, Master.name)
    if q:
        query = query.where(or_(Master.name.ilike(f"%{q}%"), Master.slug.ilike(f"%{q}%")))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/masters", response_model=MasterOut)
async def create_master(payload: MasterCreate, db: AsyncSession = Depends(get_db)):
    payload_data = payload.model_dump()
    service_ids = payload_data.pop("service_ids", [])
    base_slug = normalize_slug(payload.name or "")
    existing_slugs = set((await db.execute(select(Master.slug).where(Master.slug.like(f"{base_slug}%")))).scalars().all())
    payload_data["slug"] = pick_unique_slug(base_slug, existing_slugs)
    master = Master(**payload_data)
    if service_ids:
        services = (await db.execute(select(Service).where(Service.id.in_(service_ids)))).scalars().all()
        master.services = services
    db.add(master)
    await db.flush()
    result = await db.execute(select(Master).where(Master.id == master.id).options(selectinload(Master.services).selectinload(Service.category)))
    return result.scalar_one()


@router.put("/masters/{master_id}", response_model=MasterOut)
async def update_master(master_id: int, payload: MasterUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id).options(selectinload(Master.services)))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master not found")
    updates = payload.model_dump(exclude_unset=True)
    service_ids = updates.pop("service_ids", None)
    if "name" in updates and updates["name"]:
        normalized = normalize_slug(updates["name"])
        exists = await db.execute(select(Master.id).where(Master.slug == normalized, Master.id != master_id))
        if exists.scalar_one_or_none() is None:
            updates["slug"] = normalized
    for key, value in updates.items():
        setattr(master, key, value)
    if service_ids is not None:
        services = []
        if service_ids:
            services = (await db.execute(select(Service).where(Service.id.in_(service_ids)))).scalars().all()
        master.services = services
    await db.flush()
    result = await db.execute(select(Master).where(Master.id == master.id).options(selectinload(Master.services).selectinload(Service.category)))
    return result.scalar_one()


@router.delete("/masters/{master_id}")
async def delete_master(master_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master not found")
    master.is_active = False
    return {"status": "deactivated"}



@router.post("/masters/{master_id}/telegram-link", response_model=MasterTelegramLinkOut)
async def regenerate_master_telegram_link(master_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master not found")

    code = secrets.token_urlsafe(18)
    master.telegram_link_code = code
    await db.flush()

    bot_username = settings.telegram_bot_username
    bot_start_link = f"https://t.me/{bot_username}?start={code}" if bot_username else None
    return MasterTelegramLinkOut(master_id=master.id, code=code, bot_start_link=bot_start_link)


@router.post("/masters/{master_id}/telegram-unlink", response_model=MasterTelegramUnlinkOut)
async def unlink_master_telegram(master_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Master).where(Master.id == master_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master not found")

    master.telegram_user_id = None
    master.telegram_chat_id = None
    master.telegram_username = None
    master.telegram_linked_at = None
    await db.flush()
    return MasterTelegramUnlinkOut(master_id=master.id, unlinked=True)


@router.get("/categories", response_model=list[ServiceCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceCategory).order_by(ServiceCategory.sort_order, ServiceCategory.title))
    return result.scalars().all()


@router.post("/categories", response_model=ServiceCategoryOut)
async def create_category(payload: ServiceCategoryCreate, db: AsyncSession = Depends(get_db)):
    payload_data = payload.model_dump()
    base_slug = normalize_slug((payload.slug or payload.title) or "")
    existing_slugs = set(
        (await db.execute(select(ServiceCategory.slug).where(ServiceCategory.slug.like(f"{base_slug}%")))).scalars().all()
    )
    payload_data["slug"] = pick_unique_slug(base_slug, existing_slugs)
    category = ServiceCategory(**payload_data)
    db.add(category)
    try:
        await db.flush()
    except IntegrityError as exc:
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
    title_for_slug = updates.get("title") or updates.get("slug")
    if title_for_slug:
        base_slug = normalize_slug(title_for_slug)
        existing_slugs = set(
            (await db.execute(select(ServiceCategory.slug).where(ServiceCategory.slug.like(f"{base_slug}%"), ServiceCategory.id != category_id))).scalars().all()
        )
        updates["slug"] = pick_unique_slug(base_slug, existing_slugs)
    for key, value in updates.items():
        setattr(category, key, value)
    try:
        await db.flush()
    except IntegrityError as exc:
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
    return {"status": "deleted"}


@router.get("/weekly-rituals", response_model=list[WeeklyRitualOut])
async def list_weekly_rituals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyRitual).order_by(WeeklyRitual.sort_order, WeeklyRitual.created_at.desc()))
    return result.scalars().all()


@router.post("/weekly-rituals", response_model=WeeklyRitualOut)
async def create_weekly_ritual(payload: WeeklyRitualCreate, db: AsyncSession = Depends(get_db)):
    if payload.start_date and payload.end_date and payload.start_date > payload.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date")
    payload_data = payload.model_dump()
    base_slug = normalize_slug((payload.slug or payload.title) or "")
    existing_slugs = set(
        (await db.execute(select(WeeklyRitual.slug).where(WeeklyRitual.slug.like(f"{base_slug}%")))).scalars().all()
    )
    payload_data["slug"] = pick_unique_slug(base_slug, existing_slugs)
    ritual = WeeklyRitual(**payload_data)
    db.add(ritual)
    try:
        await db.flush()
    except IntegrityError as exc:
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
    title_for_slug = updates.get("title") or updates.get("slug")
    if title_for_slug:
        base_slug = normalize_slug(title_for_slug)
        existing_slugs = set(
            (await db.execute(select(WeeklyRitual.slug).where(WeeklyRitual.slug.like(f"{base_slug}%"), WeeklyRitual.id != ritual_id))).scalars().all()
        )
        updates["slug"] = pick_unique_slug(base_slug, existing_slugs)
    new_start = updates.get("start_date", ritual.start_date)
    new_end = updates.get("end_date", ritual.end_date)
    if new_start and new_end and new_start > new_end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date")
    for key, value in updates.items():
        setattr(ritual, key, value)
    try:
        await db.flush()
    except IntegrityError as exc:
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
    return {"status": "deleted"}


@router.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).order_by(Review.sort_order, Review.created_at.desc()))
    return result.scalars().all()


@router.post("/reviews", response_model=ReviewOut)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    review = Review(**payload.model_dump())
    db.add(review)
    await db.flush()
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
    await db.flush()
    await db.refresh(review)
    return review


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    await db.delete(review)
    return {"status": "deleted"}


@router.get("/settings/{key}", response_model=SettingOut)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in {"business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications", "tg_admins", "tg_mode"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        if key == "tg_notifications":
            return {"key": key, "value_jsonb": normalize_tg_notifications({}).model_dump(), "updated_at": None}
        if key == "tg_admins":
            return {"key": key, "value_jsonb": {"user_ids": []}, "updated_at": None}
        if key == "tg_mode":
            return {"key": key, "value_jsonb": {"mode": settings.telegram_mode}, "updated_at": None}
        return {"key": key, "value_jsonb": {}, "updated_at": None}
    if key == "tg_notifications":
        setting.value_jsonb = normalize_tg_notifications(setting.value_jsonb).model_dump()
    return setting


@router.put("/settings/{key}", response_model=SettingOut)
async def update_setting(key: str, payload: SettingUpdate, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    if key not in {"business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications", "tg_admins", "tg_mode"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting key")
    if not isinstance(payload.value_jsonb, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting value")

    value_jsonb = payload.value_jsonb
    if key == "tg_notifications":
        value_jsonb = normalize_tg_notifications(value_jsonb).model_dump()

    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value_jsonb = value_jsonb
    else:
        setting = Setting(key=key, value_jsonb=value_jsonb)
        db.add(setting)
    await db.flush()
    await db.refresh(setting)
    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="settings.update", entity_type="settings", entity_id=key, meta={"keys": list(payload.value_jsonb.keys())[:10]}, ip=ip, user_agent=user_agent)
    return setting




@router.post("/telegram/test-message", response_model=TelegramTestMessageOut)
async def send_telegram_test_message(payload: TelegramTestMessageIn, db: AsyncSession = Depends(get_db)):
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN is not configured")

    tg_settings = await get_tg_notifications_settings(db)
    if not tg_settings.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram notifications are disabled")
    if not tg_settings.admin_chat_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="admin_chat_id is not configured")

    await send_message(
        chat_id=tg_settings.admin_chat_id,
        text=payload.text,
        thread_id=tg_settings.thread_id,
    )
    return TelegramTestMessageOut(ok=True, detail="Test message sent")


@router.get("/telegram/test")
async def telegram_test(db: AsyncSession = Depends(get_db)):
    if not settings.telegram_bot_token:
        return {"ok": False, "reason": "no_token"}

    tg_settings = await get_tg_notifications_settings(db)
    if not tg_settings.enabled:
        return {"ok": False, "reason": "disabled"}
    if not tg_settings.admin_chat_id:
        return {"ok": False, "reason": "no_admin_chat_id"}

    try:
        await send_message(
            chat_id=tg_settings.admin_chat_id,
            text="Telegram test from /admin/telegram/test",
            thread_id=tg_settings.thread_id,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"send_failed:{exc.__class__.__name__}"}
    return {"ok": True, "reason": "sent"}




@router.get("/telegram/webhook-info")
async def telegram_webhook_info():
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN is not configured")

    info = await get_webhook_info()
    result = info.get("result") if isinstance(info, dict) else None
    current_url = result.get("url") if isinstance(result, dict) else None
    return {
        "telegram": info,
        "diagnostics": {
            "telegram_mode": settings.telegram_mode,
            "token_configured": bool(settings.telegram_bot_token),
            "webhook_secret_configured": bool(settings.telegram_webhook_secret),
            "has_webhook_url": bool(current_url),
            "current_webhook_url": current_url,
            "last_error_message": result.get("last_error_message") if isinstance(result, dict) else None,
        },
    }


@router.post("/telegram/set-webhook")
async def telegram_set_webhook(base_url: str = Query(..., min_length=8)):
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN is not configured")
    if not settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_WEBHOOK_SECRET is not configured")

    normalized = base_url.strip().rstrip("/")
    webhook_url = f"{normalized}/telegram/webhook"
    return await set_webhook(
        url=webhook_url,
        secret_token=settings.telegram_webhook_secret,
        allowed_updates=["message", "callback_query"],
    )


@router.post("/telegram/delete-webhook")
async def telegram_delete_webhook(drop_pending_updates: bool = Query(default=False)):
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TELEGRAM_BOT_TOKEN is not configured")
    return await delete_webhook(drop_pending_updates=drop_pending_updates)

@router.get("/bookings", response_model=list[BookingOut])
async def list_bookings(
    booking_status: str | None = Query(default=None, alias="status"),
    unread: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    service_id: int | None = None,
    master_id: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Booking)
        .options(
            selectinload(Booking.service),
            selectinload(Booking.service).selectinload(Service.category),
            selectinload(Booking.master).selectinload(Master.services),
        )
        .order_by(Booking.starts_at.desc())
    )
    if booking_status:
        try:
            status_enum = BookingStatus(booking_status)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc
        query = query.where(Booking.status == status_enum)
    if unread is True:
        query = query.where(Booking.is_read.is_(False))
    if unread is False:
        query = query.where(Booking.is_read.is_(True))
    if date_from:
        query = query.where(Booking.starts_at >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.where(Booking.starts_at <= datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59))
    if service_id is not None:
        query = query.where(Booking.service_id == service_id)
    if master_id is not None:
        query = query.where(Booking.master_id == master_id)
    if q:
        query = query.where(or_(Booking.client_name.ilike(f"%{q}%"), Booking.client_phone.ilike(f"%{q}%")))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/bookings/slots", response_model=list[BookingSlotOut])
async def list_booking_slots(service_id: int, date: str, master_id: int | None = None, db: AsyncSession = Depends(get_db)):
    try:
        target_date = parse_date_param(date)
    except ValueError as exc:
        logger.warning("Invalid date in admin booking slots request: %s", date)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    slots = await get_availability_slots(db, service_id, target_date, datetime.now(), master_id=master_id)
    return [{"time": slot[0].strftime("%H:%M"), "starts_at": slot[0], "ends_at": slot[1]} for slot in slots]


@router.post("/bookings", response_model=BookingOut)
async def create_booking(payload: BookingAdminCreate, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    requested_start = datetime.combine(payload.date, payload.time)
    chosen = await resolve_available_slot(db, payload.service_id, requested_start, datetime.now(), master_id=payload.master_id)

    try:
        booking_status = BookingStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc

    if booking_status == BookingStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="final_price is required when closing booking",
        )

    booking = Booking(
        client_name=payload.client_name or payload.client_phone,
        client_phone=payload.client_phone,
        service_id=payload.service_id,
        master_id=payload.master_id,
        starts_at=chosen[0],
        ends_at=chosen[1],
        comment=payload.comment,
        status=booking_status,
        source="ADMIN",
        is_read=True,
    )
    db.add(booking)
    await db.flush()

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking.id)
        .options(selectinload(Booking.service), selectinload(Booking.service).selectinload(Service.category), selectinload(Booking.master).selectinload(Master.services))
    )
    booking_out = result.scalar_one()
    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="booking.create", entity_type="booking", entity_id=booking_out.id, meta={"status": booking_out.status.value}, ip=ip, user_agent=user_agent)
    return booking_out


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: int, payload: BookingUpdate, request: Request, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_admin)):
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.service), selectinload(Booking.service).selectinload(Service.category), selectinload(Booking.master).selectinload(Master.services))
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    old_status = booking.status
    old_starts_at = booking.starts_at
    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates and updates["status"] is not None:
        try:
            updates["status"] = BookingStatus(updates["status"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc

    target_master_id = updates.get("master_id", booking.master_id)
    if "master_id" in updates and updates["master_id"] is not None:
        master = (await db.execute(select(Master).where(Master.id == updates["master_id"]))).scalar_one_or_none()
        if not master or not master.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid master")

    if "starts_at" in updates and updates["starts_at"] is not None:
        requested_start = updates["starts_at"].replace(tzinfo=None, second=0, microsecond=0)
        slot_start, slot_end = await resolve_available_slot(
            db,
            booking.service_id,
            requested_start,
            datetime.now(),
            master_id=target_master_id,
        )
        updates["starts_at"] = slot_start
        updates["ends_at"] = slot_end

    target_status = updates.get("status", booking.status)
    if target_status == BookingStatus.done:
        final_price_cents = updates.get("final_price_cents", booking.final_price_cents)
        if final_price_cents is None or final_price_cents <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="final_price is required when closing booking",
            )

    for key, value in updates.items():
        setattr(booking, key, value)
    await db.flush()

    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.service), selectinload(Booking.service).selectinload(Service.category), selectinload(Booking.master).selectinload(Master.services))
    )
    updated_booking = result.scalar_one()

    status_changed_to_confirmed = old_status != BookingStatus.confirmed and updated_booking.status == BookingStatus.confirmed
    datetime_changed = old_starts_at != updated_booking.starts_at

    if status_changed_to_confirmed:
        await send_master_booking_confirmed(db, updated_booking)

    if datetime_changed:
        await send_master_booking_rescheduled(db, updated_booking, old_starts_at)

    ip, user_agent = _request_context(request)
    await log_event(db, actor_type=AuditActorType.web, actor_admin=admin, action="booking.update", entity_type="booking", entity_id=updated_booking.id, meta={"fields": list(updates.keys())}, ip=ip, user_agent=user_agent)
    return updated_booking




@router.get("/logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(require_sys_admin),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).order_by(Notification.created_at.desc()))
    return result.scalars().all()
