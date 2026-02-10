import asyncio
from datetime import datetime, timezone

from app.db import AsyncSessionLocal
from app.models import Setting


DEFAULT_SETTINGS = {
    "business_hours": {
        "mon": [{"start": "10:00", "end": "21:00"}],
        "tue": [{"start": "10:00", "end": "21:00"}],
        "wed": [{"start": "10:00", "end": "21:00"}],
        "thu": [{"start": "10:00", "end": "21:00"}],
        "fri": [{"start": "10:00", "end": "21:00"}],
        "sat": [{"start": "11:00", "end": "20:00"}],
        "sun": [{"start": "11:00", "end": "20:00"}],
    },
    "slot_step_min": {"value": 30},
    "booking_rules": {"min_lead_min": 120, "max_days_ahead": 30},
    "contacts": {
        "phone": "+7 (999) 123-45-67",
        "address": "Москва, ул. Пудровая, 12",
        "socials": ["https://t.me/salonmassaj"],
    },
    "tg_admin_ids": [],
    "tg_sys_admin_ids": [],
    "tg_notifications": {
        "enabled": False,
        "admin_chat_id": None,
        "admin_thread_id": None,
        "template_admin": "Новая запись: {client_name} ({client_phone})\nУслуга: {service_title}\nВремя: {starts_at_human}",
        "send_inline_actions": True,
        "public_webhook_base_url": None,
        "webhook_secret": None,
    },
}


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        for key, value in DEFAULT_SETTINGS.items():
            existing = await session.get(Setting, key)
            if existing:
                continue
            session.add(Setting(key=key, value_jsonb=value, updated_at=datetime.now(timezone.utc)))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
