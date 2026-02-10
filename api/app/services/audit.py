from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Admin, AdminRole, AuditActorType, AuditLog


async def log_event(
    db: AsyncSession,
    *,
    actor_type: AuditActorType,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    actor_admin: Admin | None = None,
    actor_tg_user_id: int | None = None,
    actor_role: AdminRole | None = None,
    meta: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    resolved_role = actor_role or (actor_admin.role if actor_admin else None)
    event = AuditLog(
        actor_type=actor_type,
        actor_user_id=actor_admin.id if actor_admin else None,
        actor_tg_user_id=actor_tg_user_id,
        actor_role=resolved_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        meta=meta or {},
        ip=ip,
        user_agent=user_agent,
    )
    db.add(event)
    await db.flush()
