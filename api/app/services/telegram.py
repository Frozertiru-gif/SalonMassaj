import logging

import httpx

from app.core.config import settings
from app.utils import get_setting

logger = logging.getLogger(__name__)


async def send_booking_notification(db, payload: dict) -> None:
    tg_settings = await get_setting(db, "tg_notifications")
    if not tg_settings or not tg_settings.get("enabled"):
        return
    token = settings.telegram_bot_token
    if not token:
        logger.warning("Telegram bot token not set")
        return
    chat_id = tg_settings.get("chat_id")
    if not chat_id:
        logger.warning("Telegram chat_id not set")
        return

    template = tg_settings.get(
        "template",
        "Новая запись: {client_name} ({client_phone})\nУслуга: {service_id}\n{starts_at}",
    )
    text = template.format(**payload)
    data = {"chat_id": chat_id, "text": text}
    if tg_settings.get("thread_id"):
        data["message_thread_id"] = tg_settings["thread_id"]

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send telegram notification: %s", exc)
