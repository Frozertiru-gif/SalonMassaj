import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db import AsyncSessionLocal
from app.models import Admin, AdminRole, Setting


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
    "tg_notifications": {"enabled": False, "chat_id": None, "thread_id": None, "template": "Новая запись: {client_name} ({client_phone})\n{starts_at}"},
}


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        admin_result = await session.execute(select(Admin).where(Admin.email == "owner@example.com"))
        if not admin_result.scalar_one_or_none():
            session.add(
                Admin(
                    email="owner@example.com",
                    password_hash=hash_password("owner123"),
                    role=AdminRole.owner,
                    is_active=True,
                )
            )

        for key, value in DEFAULT_SETTINGS.items():
            existing = await session.get(Setting, key)
            if existing:
                continue
            session.add(Setting(key=key, value_jsonb=value, updated_at=datetime.now(timezone.utc)))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
