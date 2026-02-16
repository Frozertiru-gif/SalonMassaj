from collections.abc import Callable
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_db
from app.models import Admin, AdminRole

security = HTTPBearer()


class CurrentAdmin(BaseModel):
    role: Literal["SYS_ADMIN", "ADMIN"]


def _resolve_role_from_token(token: str) -> Literal["SYS_ADMIN", "ADMIN"] | None:
    if token in settings.sys_admin_tokens:
        return "SYS_ADMIN"
    if token in settings.admin_tokens:
        return "ADMIN"
    return None


async def _resolve_db_admin(token: str, db: AsyncSession) -> Admin:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(Admin).where(Admin.email == subject))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive admin")
    return admin


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentAdmin:
    token = credentials.credentials
    role = _resolve_role_from_token(token)
    if role:
        return CurrentAdmin(role=role)

    db_admin = await _resolve_db_admin(token, db)
    return CurrentAdmin(role="SYS_ADMIN" if db_admin.role == AdminRole.sys_admin else "ADMIN")


async def get_current_admin_for_audit(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[CurrentAdmin, Admin | None]:
    token = credentials.credentials
    role = _resolve_role_from_token(token)
    if role:
        return CurrentAdmin(role=role), None

    db_admin = await _resolve_db_admin(token, db)
    current_admin = CurrentAdmin(role="SYS_ADMIN" if db_admin.role == AdminRole.sys_admin else "ADMIN")
    return current_admin, db_admin


def require_role(required_role: Literal["SYS_ADMIN", "ADMIN"]) -> Callable[[CurrentAdmin], CurrentAdmin]:
    role_priority = {
        "ADMIN": 1,
        "SYS_ADMIN": 2,
    }

    async def _role_guard(admin: CurrentAdmin = Depends(get_current_admin)) -> CurrentAdmin:
        current_priority = role_priority.get(admin.role, 0)
        required_priority = role_priority[required_role]
        if current_priority < required_priority:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return admin

    return _role_guard


async def require_admin(admin: CurrentAdmin = Depends(require_role("ADMIN"))) -> CurrentAdmin:
    return admin


async def require_sys_admin(admin: CurrentAdmin = Depends(require_role("SYS_ADMIN"))) -> CurrentAdmin:
    return admin
