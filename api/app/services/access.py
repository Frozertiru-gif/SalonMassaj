from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AdminRole
from app.utils import get_setting


async def _load_ids_from_setting(db: AsyncSession, key: str) -> set[int]:
    raw = await get_setting(db, key)
    values: Iterable[int | str]
    if isinstance(raw, list):
        values = raw
    elif isinstance(raw, dict) and isinstance(raw.get("ids"), list):
        values = raw["ids"]
    else:
        return set()

    parsed: set[int] = set()
    for value in values:
        try:
            parsed.add(int(value))
        except (TypeError, ValueError):
            continue
    return parsed


def _parse_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    parsed: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed.add(int(item))
        except ValueError:
            continue
    return parsed


async def get_telegram_admin_ids(db: AsyncSession) -> set[int]:
    env_ids = _parse_ids(settings.telegram_admin_ids)
    if env_ids:
        return env_ids
    return await _load_ids_from_setting(db, "tg_admin_ids")


async def get_telegram_sys_admin_ids(db: AsyncSession) -> set[int]:
    env_ids = _parse_ids(settings.telegram_sys_admin_ids)
    if env_ids:
        return env_ids
    return await _load_ids_from_setting(db, "tg_sys_admin_ids")


async def resolve_telegram_role(db: AsyncSession, tg_user_id: int | None) -> AdminRole | None:
    if tg_user_id is None:
        return None
    sys_admin_ids = await get_telegram_sys_admin_ids(db)
    if tg_user_id in sys_admin_ids:
        return AdminRole.sys_admin

    admin_ids = await get_telegram_admin_ids(db)
    if tg_user_id in admin_ids:
        return AdminRole.admin

    return None
