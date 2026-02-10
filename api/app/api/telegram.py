import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db import get_db
from app.models import Booking, BookingStatus, Master
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
            "starts_at": booking.starts_at.isoformat(),
            "starts_at_human": booking.starts_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
            "status": booking.status.value,
        }
    ) + actor_suffix


def _master_picker_keyboard(booking_id: int, masters: list[Master]) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for master in masters:
        rows.append([
            {
                "text": master.name,
                "callback_data": callback_data("set", booking_id, master.id),
            }
        ])
    return {"inline_keyboard": rows or [[{"text": "Нет активных мастеров", "callback_data": callback_data("pick", booking_id)}]]}


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    tg_settings = await get_tg_notifications_settings(db)
    required_secret = settings.telegram_webhook_secret or tg_settings.webhook_secret
    if not await _is_valid_secret(request, required_secret):
        return {"ok": False, "detail": "invalid secret"}

    try:
        update = await request.json()
    except Exception:  # noqa: BLE001
        return {"ok": True}

    try:
        if "message" in update:
            await _handle_message(update["message"], db)
        elif "callback_query" in update:
            await _handle_callback(update["callback_query"], db)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to process Telegram webhook update")

    return {"ok": True}


async def _handle_message(message: dict[str, Any], db: AsyncSession) -> None:
    text = str(message.get("text") or "").strip()
    if not text.startswith("/start"):
        return

    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return
    link_code = parts[1].strip()
    tg_user = message.get("from") or {}
    telegram_user_id = tg_user.get("id")
    if not telegram_user_id:
        return

    result = await db.execute(select(Master).where(Master.telegram_link_code == link_code))
    master = result.scalar_one_or_none()
    if not master:
        await send_message(chat_id=telegram_user_id, text="Код привязки не найден или устарел.")
        return

    master.telegram_user_id = int(telegram_user_id)
    master.telegram_linked_at = datetime.now(timezone.utc)
    master.telegram_link_code = None
    await db.flush()

    await send_message(chat_id=telegram_user_id, text=f"Telegram успешно привязан к мастеру {master.name}.")


async def _handle_callback(callback_query: dict[str, Any], db: AsyncSession) -> None:
    callback_id = callback_query.get("id")
    data = callback_query.get("data")
    message = callback_query.get("message") or {}
    actor = callback_query.get("from") or {}
    actor_name = actor.get("username") or actor.get("first_name")

    parsed = parse_callback_data(str(data or ""))
    if not parsed:
        if callback_id:
            await answer_callback_query(callback_id, "Неизвестное действие")
        return

    booking_id = int(parsed["booking_id"])
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.service), selectinload(Booking.master), selectinload(Booking.master).selectinload(Master.services))
    )
    booking = result.scalar_one_or_none()

    if not booking:
        if callback_id:
            await answer_callback_query(callback_id, "Запись не найдена")
        return

    action = parsed["action"]
    if action == "pick":
        masters_result = await db.execute(select(Master).where(Master.is_active.is_(True)).order_by(Master.sort_order, Master.name))
        masters = masters_result.scalars().all()
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Выбор мастера"),
            reply_markup=_master_picker_keyboard(booking.id, masters),
        )
        if callback_id:
            await answer_callback_query(callback_id)
        return

    if action == "set":
        master_id = int(parsed["master_id"])
        master = (await db.execute(select(Master).where(Master.id == master_id, Master.is_active.is_(True)))).scalar_one_or_none()
        if not master:
            if callback_id:
                await answer_callback_query(callback_id, "Мастер не найден")
            return
        booking.master_id = master.id
        booking.master = master
        await db.flush()
        text = _admin_update_text(booking, f"Мастер назначен: {master.name}", actor_name)
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=text,
            reply_markup=build_admin_inline_keyboard(booking.id),
        )
        if booking.status == BookingStatus.confirmed and master.telegram_user_id:
            await send_master_booking_notification(booking)
        if callback_id:
            await answer_callback_query(callback_id, "Мастер назначен")
        return

    if action == "confirm":
        if booking.status != BookingStatus.confirmed:
            booking.status = BookingStatus.confirmed
            booking.is_read = True
            await db.flush()
        text = _admin_update_text(booking, "Подтверждено", actor_name)
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=text,
            reply_markup=build_admin_inline_keyboard(booking.id),
        )
        if booking.master and booking.master.telegram_user_id:
            await send_master_booking_notification(booking)
        elif booking.master_id:
            await send_message(chat_id=message.get("chat", {}).get("id"), text=f"Booking #{booking.id}: мастер не привязан к TG")

        if callback_id:
            await answer_callback_query(callback_id, "Подтверждено")
        return

    if action == "cancel":
        if booking.status != BookingStatus.cancelled:
            booking.status = BookingStatus.cancelled
            booking.is_read = True
            await db.flush()
        text = _admin_update_text(booking, "Отменено", actor_name)
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=text,
            reply_markup=None,
        )
        if booking.master and booking.master.telegram_user_id:
            await send_master_booking_notification(booking, status_text="Отменена")

        if callback_id:
            await answer_callback_query(callback_id, "Отменено")
