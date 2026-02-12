import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db import get_db
from app.models import AdminRole, AuditActorType, Booking, BookingStatus, Master
from app.services.access import resolve_telegram_role
from app.services.audit import log_event
from app.services.telegram import (
    answer_callback_query,
    booking_admin_text,
    build_admin_inline_keyboard,
    callback_data,
    edit_message_text,
    get_tg_notifications_settings,
    parse_callback_data,
    send_master_booking_notification,
    send_message,
)

router = APIRouter(tags=["telegram"])
logger = logging.getLogger(__name__)

ADMIN_MENU = "Выберите действие:\n• Новые записи\n• Ожидают подтверждения\n• Мастера\n• Помощь"


def _extract_from_id(update: dict[str, Any]) -> int | None:
    message = update.get("message") or {}
    if isinstance(message.get("from"), dict) and message["from"].get("id"):
        return int(message["from"]["id"])

    callback_query = update.get("callback_query") or {}
    if isinstance(callback_query.get("from"), dict) and callback_query["from"].get("id"):
        return int(callback_query["from"]["id"])

    return None


def _update_kind(update: dict[str, Any]) -> str:
    if "message" in update:
        return "message"
    if "callback_query" in update:
        return "callback_query"
    return "other"


def log_update_received(update: dict[str, Any]) -> None:
    logger.info(
        "tg_update.received update_id=%s update_type=%s from_id=%s",
        update.get("update_id"),
        _update_kind(update),
        _extract_from_id(update),
    )


async def _is_valid_secret(request: Request, tg_secret: str | None) -> bool:
    if not tg_secret:
        return False
    header_secret = request.headers.get("x-telegram-bot-api-secret-token")
    query_secret = request.query_params.get("secret")
    return tg_secret in {header_secret, query_secret}


def _admin_update_text(booking: Booking, action_text: str, actor_name: str | None = None) -> str:
    actor_suffix = f"\nДействие: {action_text} ({actor_name})" if actor_name else f"\nДействие: {action_text}"
    return booking_admin_text(
        {
            "booking_id": booking.id,
            "client_name": booking.client_name,
            "client_phone": booking.client_phone,
            "service_id": booking.service_id,
            "service_title": booking.service.title if booking.service else f"ID {booking.service_id}",
            "master_name": booking.master.name if booking.master else "Не назначен",
            "comment": booking.comment,
            "starts_at": booking.starts_at.isoformat(),
            "starts_at_human": booking.starts_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
            "status": booking.status.value,
        }
    ) + actor_suffix


def _master_picker_keyboard(booking_id: int, masters: list[Master]) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for master in masters:
        rows.append(
            [
                {
                    "text": master.name,
                    "callback_data": callback_data("assign", booking_id, master.id),
                }
            ]
        )
    return {"inline_keyboard": rows or [[{"text": "Нет активных мастеров", "callback_data": callback_data("choose", booking_id)}]]}


async def _send_admin_booking_list(db: AsyncSession, chat_id: int, list_type: str) -> None:
    query = select(Booking).options(selectinload(Booking.service), selectinload(Booking.master)).order_by(Booking.created_at.desc()).limit(10)
    if list_type == "new":
        query = query.where(Booking.status == BookingStatus.new)
    elif list_type == "pending":
        query = query.where(Booking.status == BookingStatus.new, Booking.is_read.is_(False))

    bookings = (await db.execute(query)).scalars().all()
    if not bookings:
        await send_message(chat_id=chat_id, text="Записей не найдено.")
        return

    for booking in bookings:
        await send_message(chat_id=chat_id, text=_admin_update_text(booking, "Ожидает действий"), reply_markup=build_admin_inline_keyboard(booking.id))


@router.get("/telegram/health")
async def telegram_health() -> dict[str, bool]:
    return {"ok": True}


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    tg_settings = await get_tg_notifications_settings(db)
    required_secret = settings.telegram_webhook_secret or tg_settings.webhook_secret
    if not required_secret:
        logger.error("tg_webhook.reject reason=no_secret")
        return {"ok": False, "detail": "webhook secret is not configured"}
    if not await _is_valid_secret(request, required_secret):
        logger.warning("tg_webhook.reject reason=invalid_secret")
        return {"ok": False, "detail": "invalid secret"}

    try:
        update = await request.json()
    except Exception:  # noqa: BLE001
        return {"ok": True}

    await process_update(update, db)
    return {"ok": True}


async def process_update(update: dict[str, Any], db: AsyncSession) -> None:
    log_update_received(update)
    try:
        if "message" in update:
            await _handle_message(update["message"], db)
        elif "callback_query" in update:
            await _handle_callback(update["callback_query"], db)
    except Exception:  # noqa: BLE001
        logger.exception("tg_update.failed")


async def _handle_message(message: dict[str, Any], db: AsyncSession) -> None:
    text = str(message.get("text") or "").strip()
    tg_user = message.get("from") or {}
    telegram_user_id = tg_user.get("id")
    if not telegram_user_id:
        return

    chat_id = (message.get("chat") or {}).get("id")
    role = await resolve_telegram_role(db, int(telegram_user_id))
    has_admin_access = role in {AdminRole.admin, AdminRole.sys_admin}

    if text in {"/admin", "/sys"}:
        if text == "/sys" and role != AdminRole.sys_admin:
            await send_message(chat_id=telegram_user_id, text="⛔️ Доступ запрещен")
            return
        if role not in {AdminRole.admin, AdminRole.sys_admin}:
            await send_message(chat_id=telegram_user_id, text="⛔️ Доступ запрещен")
            return
        await send_message(chat_id=telegram_user_id, text=f"✅ Доступ разрешен. Ваша роль: {role.value}")
        return

    if text.startswith("/start"):
        payload = ""
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            payload = parts[1].strip()
        linked_master = False

        if payload:
            result = await db.execute(select(Master).where(Master.telegram_link_code == payload))
            master = result.scalar_one_or_none()
            if master:
                master.telegram_user_id = int(telegram_user_id)
                master.telegram_chat_id = int(chat_id) if chat_id is not None else None
                master.telegram_username = tg_user.get("username")
                master.telegram_linked_at = datetime.now(timezone.utc)
                master.telegram_link_code = None
                await db.flush()
                await send_message(chat_id=telegram_user_id, text=f"Telegram успешно привязан к мастеру {master.name}.")
                linked_master = True
            else:
                await send_message(chat_id=telegram_user_id, text="Код привязки не найден или устарел.")

        if linked_master and not has_admin_access:
            await send_message(chat_id=telegram_user_id, text="OK, бот жив")
            return

        if not has_admin_access:
            logger.info("tg_admin denied user_id=%s", telegram_user_id)
            await send_message(chat_id=telegram_user_id, text="Нет доступа")
            return

        await send_message(chat_id=telegram_user_id, text=ADMIN_MENU)
        return

    if not has_admin_access:
        logger.info("tg_admin denied user_id=%s", telegram_user_id)
        return

    if text == "Новые записи":
        await _send_admin_booking_list(db, int(chat_id), "new")
    elif text == "Ожидают подтверждения":
        await _send_admin_booking_list(db, int(chat_id), "pending")
    elif text == "Мастера":
        masters = (await db.execute(select(Master).where(Master.is_active.is_(True)).order_by(Master.sort_order, Master.name))).scalars().all()
        text_rows = [f"• {m.name} (id={m.id})" for m in masters] or ["Активные мастера не найдены."]
        await send_message(chat_id=int(chat_id), text="\n".join(text_rows))
    elif text == "Помощь":
        await send_message(chat_id=int(chat_id), text="Используйте кнопки: Новые записи / Ожидают подтверждения / Мастера")


async def _handle_callback(callback_query: dict[str, Any], db: AsyncSession) -> None:
    callback_id = callback_query.get("id")
    data = callback_query.get("data")
    message = callback_query.get("message") or {}
    actor = callback_query.get("from") or {}
    actor_name = actor.get("username") or actor.get("first_name")
    actor_tg_user_id = actor.get("id")
    role = await resolve_telegram_role(db, int(actor_tg_user_id) if actor_tg_user_id is not None else None)
    if role not in {AdminRole.admin, AdminRole.sys_admin}:
        logger.info("tg_admin denied user_id=%s", actor_tg_user_id)
        if callback_id:
            await answer_callback_query(callback_id, "Нет доступа")
        return

    parsed = parse_callback_data(str(data or ""))
    if not parsed:
        if callback_id:
            await answer_callback_query(callback_id, "Неизвестное действие")
        return

    booking_id = int(parsed["booking_id"])
    booking = (
        await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.service), selectinload(Booking.master), selectinload(Booking.master).selectinload(Master.services))
        )
    ).scalar_one_or_none()

    if not booking:
        if callback_id:
            await answer_callback_query(callback_id, "Запись не найдена")
        return

    action = parsed["action"]
    if action == "choose":
        masters = (
            await db.execute(select(Master).where(Master.is_active.is_(True)).order_by(Master.sort_order, Master.name))
        ).scalars().all()
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Выбор мастера"),
            reply_markup=_master_picker_keyboard(booking.id, masters),
        )
        if callback_id:
            await answer_callback_query(callback_id)
        return

    if action == "assign":
        master_id = int(parsed["master_id"])
        master = (await db.execute(select(Master).where(Master.id == master_id, Master.is_active.is_(True)))).scalar_one_or_none()
        if not master:
            if callback_id:
                await answer_callback_query(callback_id, "Мастер не найден")
            return
        booking.master_id = master.id
        booking.master = master
        await db.flush()
        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=role,
            action="booking.assign_master",
            entity_type="booking",
            entity_id=booking.id,
            meta={"master_id": master.id, "master_name": master.name},
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, f"Мастер назначен: {master.name}", actor_name),
            reply_markup=build_admin_inline_keyboard(booking.id),
        )
        if callback_id:
            await answer_callback_query(callback_id, "Мастер назначен")
        return

    if action == "confirm":
        if booking.master_id is None:
            if callback_id:
                await answer_callback_query(callback_id, "Сначала назначьте мастера")
            return
        if booking.status != BookingStatus.confirmed:
            booking.status = BookingStatus.confirmed
            booking.is_read = True
            await db.flush()

        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=role,
            action="booking.confirm",
            entity_type="booking",
            entity_id=booking.id,
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Подтверждено", actor_name),
            reply_markup=build_admin_inline_keyboard(booking.id),
        )

        tg_settings = await get_tg_notifications_settings(db)
        if tg_settings.admin_chat_id:
            try:
                await send_message(
                    chat_id=tg_settings.admin_chat_id,
                    thread_id=tg_settings.thread_id,
                    text=booking_admin_text(
                        {
                            "booking_id": booking.id,
                            "master_name": booking.master.name if booking.master else "Не назначен",
                        },
                        template=tg_settings.template_booking_confirmed_admin,
                    ),
                )
            except Exception:  # noqa: BLE001
                logger.exception("tg_notify.booking_confirmed_admin failed booking_id=%s", booking.id)

        sent_to_master = await send_master_booking_notification(db, booking.id)
        if not sent_to_master:
            await send_message(
                chat_id=message.get("chat", {}).get("id"),
                text=f"Booking #{booking.id}: у мастера не привязан Telegram, уведомление не отправлено",
            )

        if callback_id:
            await answer_callback_query(callback_id, "Подтверждено")
        return

    if action == "cancel":
        if booking.status != BookingStatus.cancelled:
            booking.status = BookingStatus.cancelled
            booking.is_read = True
            await db.flush()
        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=role,
            action="booking.cancel",
            entity_type="booking",
            entity_id=booking.id,
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Отменено", actor_name),
            reply_markup=None,
        )

        if callback_id:
            await answer_callback_query(callback_id, "Отменено")
