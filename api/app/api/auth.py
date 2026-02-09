from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.security import create_access_token, verify_password
from app.db import get_db
from app.models import Admin
from app.schemas import AdminLogin, AdminOut, Token

router = APIRouter(prefix="/admin/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login(payload: AdminLogin, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Admin).where(Admin.email == payload.email))
        admin = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Failed to fetch admin during login.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database unavailable. Please try again later.",
        )
    if not admin or not admin.is_active or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(admin.email)
    return {"access_token": token}


@router.get("/me", response_model=AdminOut)
async def me(admin: Admin = Depends(get_current_admin)):
    return admin
