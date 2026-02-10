import asyncio
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password
from app.db import AsyncSessionLocal
from app.models import Admin, AdminRole


logger = logging.getLogger(__name__)


def _seed_enabled() -> bool:
    return os.getenv("SEED_ADMIN", "false").lower() in {"1", "true", "yes", "on"}


async def seed_admin() -> None:
    if not _seed_enabled():
        logger.info("SEED_ADMIN is disabled. Skipping admin seed.")
        return

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        logger.error("ADMIN_EMAIL and ADMIN_PASSWORD must be set when SEED_ADMIN is enabled.")
        raise SystemExit(1)

    async with AsyncSessionLocal() as session:
        try:
            existing = await session.execute(select(Admin).where(Admin.email == admin_email))
            if existing.scalar_one_or_none():
                logger.info("Admin %s already exists. Skipping seed.", admin_email)
                return

            session.add(
                Admin(
                    email=admin_email,
                    password_hash=hash_password(admin_password),
                    role=AdminRole.sys_admin,
                    is_active=True,
                )
            )
            await session.commit()
            logger.info("Seeded SYS_ADMIN admin: %s", admin_email)
        except SQLAlchemyError:
            logger.exception("Failed to seed admin user.")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(seed_admin())
    except Exception:
        logger.exception("Unhandled error during admin seed.")
        sys.exit(1)
