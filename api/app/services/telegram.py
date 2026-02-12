import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Booking, BookingStatus, Master, Service
from app.schemas import TgNotificationsSettings
from app.utils import get_setting

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_TEMPLATE = (
    "🆕 Новая запись #{booking_id}\n"
    "Клиент: {client_name} ({client_phone})\n"
    "Услуга: {service_title}\n"
    "Дата и время: {starts_at_human}\n"
    "Мастер: {master_name}\n"
    "Комментарий: {comment}"
)
DEFAULT_CONFIRMED_ADMIN_TEMPLATE = "✅ Запись #{booking_id} подтверждена. Мастер: {master_name}."
DEFAULT_MASTER_TEMPLATE = (
    "📌 Новая подтверждённая запись\n"
    "Дата и время: {starts_at_human}\n"
    "Услуга: {service_title}\n"
    "Клиент: {client_name} ({client_phone_masked})\n"
    "Комментарий: {comment}"
)


class TelegramError(RuntimeError):
    pass


def _short_response_text(value: str, limit: int = 500) -> str:
    normalized = value.replace("\n", " ").strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}…"


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "—"
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


def normalize_tg_notifications(raw: dict[str, Any] | None) -> TgNotificationsSettings:
    data = dict(raw or {})
    if "admin_chat_id" not in data and "chat_id" in data:
        data["admin_chat_id"] = data.get("chat_id")
    if "thread_id" not in data and "admin_thread_id" in data:
        data["thread_id"] = data.get("admin_thread_id")
    if "template_booking_created" not in data and "template_admin" in data:
        data["template_booking_created"] = data.get("template_admin")
    if "send_inline_actions" not in data:
        data["send_inline_actions"] = True
    return TgNotificationsSettings.model_validate(data)


def booking_time_human(starts_at: datetime) -> str:
    normalized = starts_at if starts_at.tzinfo else starts_at.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def booking_admin_text(payload: dict[str, Any], template: str | None = None, *, mask_client_phone: bool = True) -> str:
    text_template = template or DEFAULT_ADMIN_TEMPLATE
    base_payload = {
        "booking_id": payload.get("booking_id") or "—",
        "client_name": payload.get("client_name") or "—",
        "client_phone": payload.get("client_phone") or "—",
        "client_phone_masked": mask_phone(payload.get("client_phone")) if mask_client_phone else (payload.get("client_phone") or "—"),
        "service_title": payload.get("service_title") or f"ID {payload.get('service_id')}",
        "starts_at": payload.get("starts_at") or "—",
        "starts_at_human": payload.get("starts_at_human") or payload.get("starts_at") or "—",
        "status": payload.get("status") or BookingStatus.new.value,
        "master_name": payload.get("master_name") or "Не назначен",
        "comment": payload.get("comment") or "—",
    }
    return text_template.format(**base_payload)


def build_admin_inline_keyboard(booking_id: int) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Подтвердить", "callback_data": callback_data("confirm", booking_id)},
                {"text": "❌ Отменить", "callback_data": callback_data("cancel", booking_id)},
            ],
            [{"text": "👤 Назначить мастера", "callback_data": callback_data("choose", booking_id)}],
        ]
    }


def _build_telegram_timeout(method: str, payload: dict[str, Any], timeout_override: httpx.Timeout | None = None) -> httpx.Timeout:
    if timeout_override is not None:
        return timeout_override

    payload_timeout = float(payload.get("timeout") or 0)
    read_timeout = max(60.0, payload_timeout + 10.0)
    return httpx.Timeout(connect=10.0, read=read_timeout, write=10.0, pool=10.0)


async def _telegram_api(method: str, payload: dict[str, Any], timeout_override: httpx.Timeout | None = None) -> dict[str, Any]:
    token = settings.telegram_bot_token
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN is not set")

    timeout = _build_telegram_timeout(method=method, payload=payload, timeout_override=timeout_override)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
        )

    short_text = _short_response_text(response.text)

    if not response.is_success:
        logger.error("Telegram API request failed: method=%s status=%s body=%s", method, response.status_code, short_text)
        raise TelegramError(f"Telegram API request failed with status {response.status_code}")

    data = response.json()
    if not data.get("ok"):
        logger.error("Telegram API error response: method=%s status=%s body=%s", method, response.status_code, short_text)
        raise TelegramError(data.get("description") or "Telegram API returned non-ok response")
    return data


async def get_webhook_info() -> dict[str, Any]:
    return await _telegram_api("getWebhookInfo", {})


async def get_me(timeout_seconds: float = 10.0) -> dict[str, Any]:
    timeout = httpx.Timeout(connect=timeout_seconds, read=timeout_seconds, write=10.0, pool=10.0)
    return await _telegram_api("getMe", {}, timeout_override=timeout)


async def set_webhook(url: str, secret_token: str, allowed_updates: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"url": url, "secret_token": secret_token, "drop_pending_updates": False}
    if allowed_updates is not None:
        payload["allowed_updates"] = allowed_updates
    return await _telegram_api("setWebhook", payload)


async def delete_webhook(drop_pending_updates: bool = False) -> dict[str, Any]:
    return await _telegram_api("deleteWebhook", {"drop_pending_updates": drop_pending_updates})


async def get_updates(offset: int | None = None, timeout: int = 30, allowed_updates: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"timeout": timeout}
    if offset is not None:
        payload["offset"] = offset
    if allowed_updates is not None:
        payload["allowed_updates"] = allowed_updates
    return await _telegram_api("getUpdates", payload)


async def send_message(
    chat_id: str | int,
    text: str,
    reply_markup: dict[str, Any] | None = None,
    thread_id: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    return await _telegram_api("sendMessage", payload)


async def edit_message_text(
    chat_id: str | int,
    message_id: int,
    text: str,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return await _telegram_api("editMessageText", payload)


async def get_tg_notifications_settings(db: AsyncSession) -> TgNotificationsSettings:
    raw = await get_setting(db, "tg_notifications")
    return normalize_tg_notifications(raw)


async def build_booking_notification_payload(db: AsyncSession, booking: Booking) -> dict[str, Any]:
    service = booking.service
    if service is None:
        service = (await db.execute(select(Service).where(Service.id == booking.service_id))).scalar_one_or_none()

    master = booking.master
    if master is None and booking.master_id is not None:
        master = (await db.execute(select(Master).where(Master.id == booking.master_id))).scalar_one_or_none()

    return {
        "booking_id": booking.id,
        "service_id": booking.service_id,
        "service_title": service.title if service else f"ID {booking.service_id}",
        "master_id": booking.master_id,
        "master_name": master.name if master else "Не назначен",
        "starts_at": booking.starts_at.isoformat(),
        "starts_at_human": booking_time_human(booking.starts_at),
        "client_name": booking.client_name,
        "client_phone": booking.client_phone,
        "comment": booking.comment,
        "status": booking.status.value,
    }


async def send_booking_created_to_admin(db: AsyncSession, booking_id: int) -> None:
    logger.info("tg_notify.booking_created start booking_id=%s", booking_id)

    tg_settings = await get_tg_notifications_settings(db)
    if not tg_settings.enabled:
        logger.info("tg_notify.booking_created skip reason=disabled booking_id=%s", booking_id)
        return
    if not settings.telegram_bot_token:
        logger.warning("tg_notify.booking_created skip reason=no_token booking_id=%s", booking_id)
        return
    if not tg_settings.admin_chat_id:
        logger.warning("tg_notify.booking_created skip reason=no_admin_chat_id booking_id=%s", booking_id)
        return

    booking = (
        await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
            .options(selectinload(Booking.service), selectinload(Booking.master))
        )
    ).scalar_one_or_none()
    if not booking:
        logger.warning("tg_notify.booking_created skip reason=booking_not_found booking_id=%s", booking_id)
        return
    if booking.tg_new_sent_at is not None:
        logger.info("tg_notify.booking_created skip reason=already_sent booking_id=%s tg_new_sent_at=%s", booking_id, booking.tg_new_sent_at.isoformat())
        return

    payload = await build_booking_notification_payload(db, booking)
    text = booking_admin_text(
        payload,
        template=tg_settings.template_booking_created or tg_settings.template_admin,
        mask_client_phone=False,
    )
    reply_markup = build_admin_inline_keyboard(booking.id) if tg_settings.send_inline_actions else None

    try:
        result = await send_message(
            chat_id=tg_settings.admin_chat_id,
            text=text,
            reply_markup=reply_markup,
            thread_id=tg_settings.thread_id,
        )
    except TelegramError:
        logger.exception("tg_notify.booking_created failed booking_id=%s", booking_id)
        return
    except Exception:
        logger.exception("tg_notify.booking_created failed reason=exception booking_id=%s", booking_id)
        return

    message_id = ((result or {}).get("result") or {}).get("message_id")
    booking.tg_new_sent_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("tg_notify.booking_created sent booking_id=%s message_id=%s", booking_id, message_id)


async def send_booking_notification(db: AsyncSession, payload: dict[str, Any]) -> None:
    booking_id = payload.get("booking_id")
    if isinstance(booking_id, int):
        await send_booking_created_to_admin(db, booking_id)


async def send_master_booking_notification(db: AsyncSession, booking_id: int) -> bool:
    booking = (
        await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.service), selectinload(Booking.master))
        )
    ).scalar_one_or_none()
    if not booking:
        logger.warning("tg_notify.booking_master skip reason=booking_not_found booking_id=%s", booking_id)
        return False
    if not booking.master_id or not booking.master:
        logger.warning("tg_notify.booking_master skip reason=no_master booking_id=%s", booking_id)
        return False
    if not booking.master.telegram_chat_id:
        logger.warning("tg_notify.booking_master skip reason=no_master_chat_id booking_id=%s master_id=%s", booking_id, booking.master.id)
        return False

    payload = await build_booking_notification_payload(db, booking)
    tg_settings = await get_tg_notifications_settings(db)
    text = booking_admin_text(payload, tg_settings.template_booking_assigned_master or DEFAULT_MASTER_TEMPLATE)

    try:
        result = await send_message(chat_id=booking.master.telegram_chat_id, text=text)
    except Exception:
        logger.exception("tg_notify.booking_master failed booking_id=%s master_id=%s", booking_id, booking.master.id)
        return False

    message_id = ((result or {}).get("result") or {}).get("message_id")
    logger.info("tg_notify.booking_master sent booking_id=%s master_id=%s message_id=%s", booking_id, booking.master.id, message_id)
    return True


def callback_data(action: str, booking_id: int, master_id: int | None = None) -> str:
    if action in {"confirm", "cancel", "choose"}:
        return f"b:{booking_id}:{action}"
    if action == "assign" and master_id is not None:
        return f"b:{booking_id}:assign:{master_id}"
    raise ValueError("Unsupported callback action")


def parse_callback_data(value: str) -> dict[str, int | str] | None:
    parts = value.split(":")
    if len(parts) < 3 or parts[0] != "b":
        return None
    try:
        booking_id = int(parts[1])
    except ValueError:
        return None

    action = parts[2]
    if action in {"confirm", "cancel", "choose"} and len(parts) == 3:
        return {"booking_id": booking_id, "action": action}
    if action == "assign" and len(parts) == 4:
        try:
            master_id = int(parts[3])
        except ValueError:
            return None
        return {"booking_id": booking_id, "action": action, "master_id": master_id}
    return None


def dumps_reply_markup(markup: dict[str, Any]) -> str:
    return json.dumps(markup, ensure_ascii=False)


async def answer_callback_query(callback_query_id: str, text: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return await _telegram_api("answerCallbackQuery", payload)
