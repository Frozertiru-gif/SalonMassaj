import asyncio
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db import AsyncSessionLocal
from app.models import Admin, AdminRole


logger = logging.getLogger(__name__)


def _seed_enabled() -> bool:
    return os.getenv("SEED_ADMIN", "false").lower() in {"1", "true", "yes", "on"}


def _read_account_credentials() -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    """
    Returns:
      (sys_admin_credentials, admin_credentials)

    Backward compatibility:
    - if SYS_ADMIN_EMAIL/SYS_ADMIN_PASSWORD are missing,
      ADMIN_EMAIL/ADMIN_PASSWORD are treated as SYS_ADMIN credentials.
    """

    sys_email = os.getenv("SYS_ADMIN_EMAIL")
    sys_password = os.getenv("SYS_ADMIN_PASSWORD")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not sys_email and not sys_password:
        # Legacy mode: ADMIN_* used to bootstrap SYS_ADMIN.
        sys_email = admin_email
        sys_password = admin_password
        admin_email = None
        admin_password = None

    if bool(sys_email) != bool(sys_password):
        logger.error("SYS_ADMIN_EMAIL and SYS_ADMIN_PASSWORD must be set together.")
        raise SystemExit(1)

    if bool(admin_email) != bool(admin_password):
        logger.error("ADMIN_EMAIL and ADMIN_PASSWORD must be set together.")
        raise SystemExit(1)

    sys_credentials = (sys_email, sys_password) if sys_email and sys_password else None
    admin_credentials = (admin_email, admin_password) if admin_email and admin_password else None

    if not sys_credentials:
        logger.error(
            "Missing SYS admin credentials. Set SYS_ADMIN_EMAIL/SYS_ADMIN_PASSWORD "
            "(or ADMIN_EMAIL/ADMIN_PASSWORD in legacy mode)."
        )
        raise SystemExit(1)

    return sys_credentials, admin_credentials


async def _upsert_admin(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    role: AdminRole,
    label: str,
) -> None:
    existing = await session.execute(select(Admin).where(Admin.email == email))
    admin = existing.scalar_one_or_none()

    password_hash = hash_password(password)

    if admin is None:
        session.add(
            Admin(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True,
            )
        )
        logger.info("Seeded %s: %s", label, email)
        return

    admin.password_hash = password_hash
    admin.role = role
    admin.is_active = True
    logger.info("Updated %s: %s", label, email)


async def seed_admin() -> None:
    if not _seed_enabled():
        logger.info("SEED_ADMIN is disabled. Skipping admin seed.")
        return

    sys_credentials, admin_credentials = _read_account_credentials()

    async with AsyncSessionLocal() as session:
        try:
            sys_email, sys_password = sys_credentials
            await _upsert_admin(
                session,
                email=sys_email,
                password=sys_password,
                role=AdminRole.sys_admin,
                label="SYS_ADMIN",
            )

            if admin_credentials:
                admin_email, admin_password = admin_credentials
                if admin_email == sys_email:
                    logger.warning(
                        "ADMIN_EMAIL matches SYS_ADMIN_EMAIL (%s). "
                        "Skipping ADMIN seed because one account cannot have two roles.",
                        admin_email,
                    )
                else:
                    await _upsert_admin(
                        session,
                        email=admin_email,
                        password=admin_password,
                        role=AdminRole.admin,
                        label="ADMIN",
                    )

            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Failed to seed admin users.")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(seed_admin())
    except Exception:
        logger.exception("Unhandled error during admin seed.")
        sys.exit(1)
