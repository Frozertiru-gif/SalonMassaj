import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, auth, public, telegram
from app.core.config import settings
from app.db import AsyncSessionLocal
from app.services.backup_service import BackupBusyError, backup_service
from app.services.telegram import TelegramError, get_me, get_updates


def _configure_logging() -> None:
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


_configure_logging()

logger = logging.getLogger(__name__)
app = FastAPI(title="SalonMassaj API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(telegram.router)


@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    if backup_service.is_maintenance:
        path = request.url.path
        if path not in {"/health", "/telegram/health", "/telegram/webhook"}:
            return JSONResponse(status_code=503, content={"detail": "maintenance: restore in progress"})
    return await call_next(request)



async def _telegram_polling_loop() -> None:
    logger.info("Telegram polling worker started")
    offset: int | None = None
    backoff_seconds = 1
    while True:
        try:
            if backup_service.is_maintenance:
                await asyncio.sleep(1)
                continue
            logger.info("polling: request sent offset=%s", offset)
            response = await get_updates(offset=offset, timeout=30, allowed_updates=["message", "callback_query"])
            updates = response.get("result") or []
            logger.info("polling: got %s updates", len(updates))
            backoff_seconds = 1
            for update in updates:
                async with AsyncSessionLocal() as db:
                    async with db.begin():
                        await telegram.process_update(update, db)
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
        except asyncio.CancelledError:
            logger.info("Telegram polling worker stopped")
            raise
        except httpx.ReadTimeout:
            logger.info("polling: timeout (ok)")
            continue
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.HTTPError) as exc:
            logger.warning("polling: network error (retry in %ss): %s", backoff_seconds, exc)
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 30)
            continue
        except TelegramError:
            logger.warning("polling: Telegram API error (retry in %ss)", backoff_seconds, exc_info=True)
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 30)
            continue
        except Exception:  # noqa: BLE001
            logger.exception("polling: unexpected error (retry in 2s)")
            await asyncio.sleep(2)
            continue


async def _run_scheduled_backup() -> None:
    try:
        await backup_service.run_backup_script()
        await backup_service.send_latest_to_backup_chat()
    except BackupBusyError:
        logger.info("backup.scheduler skipped: operation already in progress")
    except Exception as exc:  # noqa: BLE001
        logger.exception("backup.scheduler failed")
        await backup_service.notify_sys_admins(f"⚠️ Автобэкап завершился ошибкой: {exc}")


async def _backup_scheduler_loop() -> None:
    logger.info("backup scheduler started")
    if backup_service.is_catchup_required():
        logger.info("backup scheduler catch-up triggered")
        await _run_scheduled_backup()

    while True:
        now = datetime.now(timezone.utc)
        run_at = now.replace(hour=settings.backup_cron_hour, minute=settings.backup_cron_minute, second=0, microsecond=0)
        if run_at <= now:
            run_at = run_at + timedelta(days=1)
        delay_seconds = (run_at - now).total_seconds()
        logger.info("backup scheduler sleeping for %.0f sec until %s", delay_seconds, run_at.isoformat())
        await asyncio.sleep(delay_seconds)
        await _run_scheduled_backup()


@app.on_event("startup")
async def startup_event() -> None:
    mode = (settings.telegram_mode or "webhook").strip().lower()
    logger.info("Telegram startup config: mode=%s token_set=%s webhook_secret_set=%s", mode, bool(settings.telegram_bot_token), bool(settings.telegram_webhook_secret))

    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured; Telegram handlers are disabled")
    else:
        try:
            await get_me(timeout_seconds=10.0)
            logger.info("Telegram startup check: getMe success")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram startup check: getMe failed (%s)", exc)

    if mode == "polling":
        app.state.telegram_polling_task = asyncio.create_task(_telegram_polling_loop())
        logger.warning("Telegram mode polling is enabled; webhook endpoints are not used")
    else:
        app.state.telegram_polling_task = None
        if not settings.telegram_webhook_secret:
            logger.error("TELEGRAM_WEBHOOK_SECRET is not configured; webhook requests will be rejected")

    app.state.backup_scheduler_task = None
    if settings.backup_enabled and settings.backup_chat_id:
        app.state.backup_scheduler_task = asyncio.create_task(_backup_scheduler_loop())
    else:
        logger.info("backup scheduler disabled (BACKUP_ENABLED=%s BACKUP_CHAT_ID=%s)", settings.backup_enabled, settings.backup_chat_id)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    task = getattr(app.state, "telegram_polling_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    backup_task = getattr(app.state, "backup_scheduler_task", None)
    if backup_task:
        backup_task.cancel()
        try:
            await backup_task
        except asyncio.CancelledError:
            pass


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
