from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_db
from app.models import Admin, AdminRole

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    token = credentials.credentials
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


def require_role(required_role: AdminRole) -> Callable[[Admin], Admin]:
    role_priority = {
        AdminRole.admin: 1,
        AdminRole.sys_admin: 2,
    }

    async def _role_guard(admin: Admin = Depends(get_current_admin)) -> Admin:
        current_priority = role_priority.get(admin.role, 0)
        required_priority = role_priority[required_role]
        if current_priority < required_priority:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return admin

    return _role_guard


async def require_admin(admin: Admin = Depends(require_role(AdminRole.admin))) -> Admin:
    return admin


async def require_sys_admin(admin: Admin = Depends(require_role(AdminRole.sys_admin))) -> Admin:
    return admin
