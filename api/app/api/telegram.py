import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db import get_db
from app.models import AdminRole, AuditActorType, Booking, BookingStatus, Master
from app.services.access import resolve_telegram_role
from app.services.audit import log_event
from app.services.backup_service import BackupBusyError, backup_service
from app.services.telegram import (
    answer_callback_query,
    booking_admin_text,
    build_admin_inline_keyboard,
    callback_data,
    edit_message_text,
    get_tg_notifications_settings,
    parse_callback_data,
    send_master_booking_notification,
    send_message,
)

router = APIRouter(tags=["telegram"])
logger = logging.getLogger(__name__)

ADMIN_MENU = "Выберите действие (нажмите кнопку ниже):\n• Новые записи\n• Ожидают подтверждения\n• Мастера\n• Помощь"
MASTER_MENU = "Раздел мастера:\n• Мои заявки\n• Помощь"
MASTER_PAGE_SIZE = 10
BACKUP_MENU_LABEL = "🛡 Резервные копии"
@dataclass(slots=True)
class PendingRestoreUpload:
    awaiting_upload: bool = False
    file_path: str | None = None
    file_name: str | None = None
    file_size_bytes: int | None = None
    detected_type: str | None = None
    uploaded_at_iso: str | None = None


PENDING_RESTORE_UPLOADS: dict[int, PendingRestoreUpload] = {}


_IDEMPOTENCY_TTL_SECONDS = 300
_PROCESSED_CALLBACKS: dict[str, float] = {}
_PROCESSED_UPDATES: dict[int, float] = {}


def _is_processed_recently(cache: dict[Any, float], key: Any, now: float | None = None) -> bool:
    if now is None:
        now = time.monotonic()
    expired = [cache_key for cache_key, ts in cache.items() if now - ts > _IDEMPOTENCY_TTL_SECONDS]
    for cache_key in expired:
        cache.pop(cache_key, None)

    ts = cache.get(key)
    if ts is None:
        cache[key] = now
        return False
    return now - ts <= _IDEMPOTENCY_TTL_SECONDS


ADMIN_ACTION_ALIASES: dict[str, set[str]] = {
    "new": {"новые записи", "новые"},
    "pending": {"ожидают подтверждения", "ожидают", "ожидание"},
    "masters": {"мастера", "мастеры", "мастера список"},
    "help": {"помощь", "help", "/help"},
    "backup": {"🛡 резервные копии", "резервные копии", "backup"},
}

MASTER_ACTION_ALIASES: dict[str, set[str]] = {
    "my": {"мои заявки", "/my", "my"},
    "help": {"помощь", "help", "/help"},
    "backup": {"🛡 резервные копии", "резервные копии", "backup"},
}


@dataclass
class TelegramAccessContext:
    tg_user_id: int
    admin_role: AdminRole | None = None
    master: Master | None = None

    @property
    def is_admin(self) -> bool:
        return self.admin_role in {AdminRole.admin, AdminRole.sys_admin}

    @property
    def is_master(self) -> bool:
        return self.master is not None


def _admin_reply_keyboard(role: AdminRole | None = None) -> dict[str, Any]:
    keyboard = [
        [{"text": "Новые записи"}, {"text": "Ожидают подтверждения"}],
        [{"text": "Мастера"}, {"text": "Помощь"}],
    ]
    if role == AdminRole.sys_admin:
        keyboard.append([{"text": BACKUP_MENU_LABEL}])
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def _master_reply_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Мои заявки"}],
            [{"text": "Помощь"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def _normalize_action_text(text: str) -> str:
    return " ".join(text.lower().split())


def _extract_from_id(update: dict[str, Any]) -> int | None:
    message = update.get("message") or {}
    if isinstance(message.get("from"), dict) and message["from"].get("id"):
        return int(message["from"]["id"])

    callback_query = update.get("callback_query") or {}
    if isinstance(callback_query.get("from"), dict) and callback_query["from"].get("id"):
        return int(callback_query["from"]["id"])

    return None


def _update_kind(update: dict[str, Any]) -> str:
    if "message" in update:
        return "message"
    if "callback_query" in update:
        return "callback_query"
    return "other"


def log_update_received(update: dict[str, Any]) -> None:
    logger.info(
        "tg_update.received update_id=%s update_type=%s from_id=%s",
        update.get("update_id"),
        _update_kind(update),
        _extract_from_id(update),
    )


async def _is_valid_secret(request: Request, tg_secret: str | None) -> bool:
    if not tg_secret:
        return False
    header_secret = request.headers.get("x-telegram-bot-api-secret-token")
    query_secret = request.query_params.get("secret")
    return tg_secret in {header_secret, query_secret}


def _admin_update_text(booking: Booking, action_text: str, actor_name: str | None = None) -> str:
    actor_suffix = f"\nДействие: {action_text} ({actor_name})" if actor_name else f"\nДействие: {action_text}"
    return booking_admin_text(
        {
            "booking_id": booking.id,
            "client_name": booking.client_name,
            "client_phone": booking.client_phone,
            "service_id": booking.service_id,
            "service_title": booking.service.title if booking.service else f"ID {booking.service_id}",
            "master_name": booking.master.name if booking.master else "Не назначен",
            "comment": booking.comment,
            "starts_at": booking.starts_at.isoformat(),
            "starts_at_human": booking.starts_at.replace(tzinfo=None).strftime("%d.%m.%Y %H:%M"),
            "status": booking.status.value,
        },
        mask_client_phone=False,
    ) + actor_suffix


def _master_picker_keyboard(booking_id: int, masters: list[Master]) -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    for master in masters:
        rows.append(
            [
                {
                    "text": master.name,
                    "callback_data": callback_data("assign", booking_id, master.id),
                }
            ]
        )
    return {"inline_keyboard": rows or [[{"text": "Нет активных мастеров", "callback_data": callback_data("choose", booking_id)}]]}


async def _send_admin_booking_list(db: AsyncSession, chat_id: int, list_type: str) -> None:
    query = select(Booking).options(selectinload(Booking.service), selectinload(Booking.master)).order_by(Booking.created_at.desc()).limit(10)
    if list_type == "new":
        query = query.where(Booking.status == BookingStatus.new)
    elif list_type == "pending":
        query = query.where(Booking.status == BookingStatus.new, Booking.is_read.is_(False))

    bookings = (await db.execute(query)).scalars().all()
    if not bookings:
        await send_message(chat_id=chat_id, text="Записей не найдено.")
        return

    for booking in bookings:
        await send_message(chat_id=chat_id, text=_admin_update_text(booking, "Ожидает действий"), reply_markup=build_admin_inline_keyboard(booking.id))


async def _resolve_telegram_access(db: AsyncSession, tg_user_id: int) -> TelegramAccessContext:
    admin_role = await resolve_telegram_role(db, tg_user_id)
    master = (await db.execute(select(Master).where(Master.telegram_user_id == tg_user_id))).scalar_one_or_none()
    return TelegramAccessContext(tg_user_id=tg_user_id, admin_role=admin_role, master=master)


def _master_booking_card_text(booking: Booking) -> str:
    starts_at = booking.starts_at.replace(tzinfo=None).strftime("%d.%m.%Y %H:%M")
    service_title = booking.service.title if booking.service else f"ID {booking.service_id}"
    comment = booking.comment or "—"
    return (
        f"Заявка #{booking.id}\n"
        f"Дата и время: {starts_at}\n"
        f"Услуга: {service_title}\n"
        f"Клиент: {booking.client_name} ({booking.client_phone})\n"
        f"Комментарий: {comment}\n"
        f"Статус: {booking.status.value}"
    )


def _master_list_callback(page: int) -> str:
    return f"m:my:{page}"


def _parse_master_callback(value: str) -> dict[str, int | str] | None:
    parts = value.split(":")
    if len(parts) != 3 or parts[0] != "m" or parts[1] != "my":
        return None
    try:
        page = int(parts[2])
    except ValueError:
        return None
    if page < 0:
        return None
    return {"action": "my", "page": page}


def _master_pagination_markup(page: int, total: int) -> dict[str, Any] | None:
    total_pages = (total + MASTER_PAGE_SIZE - 1) // MASTER_PAGE_SIZE
    if total_pages <= 1:
        return None

    row: list[dict[str, str]] = []
    if page > 0:
        row.append({"text": "⬅️ Назад", "callback_data": _master_list_callback(page - 1)})
    if page + 1 < total_pages:
        row.append({"text": "Дальше ➡️", "callback_data": _master_list_callback(page + 1)})
    if not row:
        return None
    return {"inline_keyboard": [row]}


async def _send_master_bookings(db: AsyncSession, chat_id: int, master: Master, page: int = 0) -> None:
    total = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.master_id == master.id,
                Booking.status.in_([BookingStatus.confirmed, BookingStatus.done]),
            )
        )
    ).scalar_one()
    if total == 0:
        await send_message(chat_id=chat_id, text="У вас пока нет подтверждённых заявок.", reply_markup=_master_reply_keyboard())
        return

    max_page = max((total - 1) // MASTER_PAGE_SIZE, 0)
    page = min(page, max_page)
    offset = page * MASTER_PAGE_SIZE
    bookings = (
        await db.execute(
            select(Booking)
            .where(
                Booking.master_id == master.id,
                Booking.status.in_([BookingStatus.confirmed, BookingStatus.done]),
            )
            .options(selectinload(Booking.service))
            .order_by(Booking.starts_at.asc(), Booking.id.asc())
            .offset(offset)
            .limit(MASTER_PAGE_SIZE)
        )
    ).scalars().all()

    for booking in bookings:
        await send_message(chat_id=chat_id, text=_master_booking_card_text(booking))

    pagination = _master_pagination_markup(page, total)
    page_text = f"Страница {page + 1} из {max_page + 1}. Всего заявок: {total}."
    await send_message(chat_id=chat_id, text=page_text, reply_markup=pagination)


async def _handle_master_message(db: AsyncSession, chat_id: int, text: str, master: Master) -> None:
    normalized_text = _normalize_action_text(text)
    if normalized_text in MASTER_ACTION_ALIASES["my"]:
        await _send_master_bookings(db, chat_id, master, page=0)
        return
    if normalized_text in MASTER_ACTION_ALIASES["help"]:
        await send_message(chat_id=chat_id, text="Используйте кнопку «Мои заявки» или команду /my.", reply_markup=_master_reply_keyboard())
        return
    await send_message(chat_id=chat_id, text="Доступные действия: «Мои заявки», «Помощь».", reply_markup=_master_reply_keyboard())


def _is_private_chat(message: dict[str, Any]) -> bool:
    return ((message.get("chat") or {}).get("type") == "private")


def _backup_menu_markup(has_pending_upload: bool = False) -> dict[str, Any]:
    rows = [
        [{"text": "📦 Статус", "callback_data": "bk:status"}],
        [{"text": "▶ Сделать сейчас", "callback_data": "bk:run"}],
        [{"text": "📤 Отправить в backup-чат", "callback_data": "bk:send"}],
        [{"text": "♻ Восстановить последний", "callback_data": "bk:restore_latest:confirm"}],
        [{"text": "📎 Восстановить из файла", "callback_data": "bk:restore_file:start"}],
    ]
    if has_pending_upload:
        rows.append([{"text": "✅ Подтвердить восстановление", "callback_data": "bk:restore_file:confirm"}])
    rows.append([{"text": "🛑 Отмена", "callback_data": "bk:cancel"}])
    return {"inline_keyboard": rows}


def _detect_uploaded_restore_type(file_name: str) -> str:
    lowered = file_name.lower()
    if lowered.endswith(".gpg"):
        return "gpg"
    if lowered.endswith(".sql") or lowered.endswith(".sql.gz"):
        return "sql"
    if lowered.endswith(".dump") or lowered.endswith(".backup"):
        return "custom"
    return "unknown"


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024 * 1024:
        return f"{size_bytes} B"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _restore_confirmation_markup() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "✅ Подтвердить восстановление", "callback_data": "bk:restore_file:confirm"}],
            [{"text": "❌ Отмена", "callback_data": "bk:cancel"}],
        ]
    }


async def _send_backup_menu(chat_id: int, actor_tg_user_id: int) -> None:
    pending = PENDING_RESTORE_UPLOADS.get(actor_tg_user_id)
    has_pending = bool(pending and pending.file_path)
    await send_message(chat_id=chat_id, text="Управление резервными копиями.", reply_markup=_backup_menu_markup(has_pending_upload=has_pending))


async def _handle_backup_callback(callback_id: str | None, data: str, message: dict[str, Any], actor_tg_user_id: int) -> bool:
    if not data.startswith("bk:"):
        return False

    if callback_id:
        await answer_callback_query(callback_id)

    action = data.split(":")
    chat_id = (message.get("chat") or {}).get("id")
    if chat_id is None:
        return True

    if action[1] == "status":
        metadata = backup_service.get_latest_metadata()
        if not metadata:
            await send_message(chat_id=chat_id, text="Резервных копий пока нет.")
        else:
            await send_message(
                chat_id=chat_id,
                text=(
                    f"Последняя копия: {metadata.get('filename')}\n"
                    f"Создана: {metadata.get('created_at')}\n"
                    f"Размер: {metadata.get('size_bytes')} байт"
                ),
            )
    elif action[1] == "run":
        try:
            metadata = await backup_service.run_backup_script()
            await send_message(chat_id=chat_id, text=f"Бэкап создан: {metadata.get('filename')}")
        except BackupBusyError:
            await send_message(chat_id=chat_id, text="Операция уже выполняется. Попробуйте позже.")
        except Exception as exc:  # noqa: BLE001
            await send_message(chat_id=chat_id, text=f"Ошибка бэкапа: {exc}")
    elif action[1] == "send":
        try:
            await backup_service.send_latest_to_backup_chat()
            await send_message(chat_id=chat_id, text="Файл отправлен в backup-чат.")
        except Exception as exc:  # noqa: BLE001
            await send_message(chat_id=chat_id, text=f"Ошибка отправки: {exc}")
    elif action[1] == "restore_latest" and len(action) > 2 and action[2] == "confirm":
        try:
            result = await backup_service.restore_latest_local_backup(actor_tg_user_id=actor_tg_user_id)
            if result.get("status") == "ok_with_warnings":
                await send_message(chat_id=chat_id, text="⚠️ Восстановлено с warnings. Подробности в логах.")
            else:
                await send_message(chat_id=chat_id, text="Восстановление из последнего локального бэкапа завершено.")
        except BackupBusyError:
            await send_message(chat_id=chat_id, text="Операция уже выполняется. Попробуйте позже.")
        except Exception as exc:  # noqa: BLE001
            await send_message(chat_id=chat_id, text=f"❌ Ошибка восстановления: {exc}")
    elif action[1] == "restore_file" and len(action) > 2 and action[2] == "start":
        pending = PENDING_RESTORE_UPLOADS.get(actor_tg_user_id) or PendingRestoreUpload()
        pending.awaiting_upload = True
        pending.file_path = None
        pending.file_name = None
        pending.file_size_bytes = None
        pending.detected_type = None
        pending.uploaded_at_iso = None
        PENDING_RESTORE_UPLOADS[actor_tg_user_id] = pending
        await send_message(
            chat_id=chat_id,
            text=(
                "Отправьте файлом бэкап в этот чат. Поддерживается: .dump/.backup (pg_dump custom), .sql, .sql.gz, "
                "а также .gpg (если используется шифрование). После загрузки бот попросит подтверждение."
            ),
        )
    elif action[1] == "restore_file" and len(action) > 2 and action[2] == "confirm":
        pending = PENDING_RESTORE_UPLOADS.get(actor_tg_user_id)
        if not pending or not pending.file_path:
            await send_message(chat_id=chat_id, text="Сначала нажмите «📎 Восстановить из файла» и отправьте документ.")
        else:
            restore_path = Path(pending.file_path)
            restore_name = pending.file_name or restore_path.name
            PENDING_RESTORE_UPLOADS.pop(actor_tg_user_id, None)
            await send_message(chat_id=chat_id, text="Запускаю восстановление…")
            asyncio.create_task(_run_restore_and_report(chat_id=chat_id, actor_tg_user_id=actor_tg_user_id, restore_path=restore_path, restore_name=restore_name))
    elif action[1] == "cancel":
        PENDING_RESTORE_UPLOADS.pop(actor_tg_user_id, None)
        await send_message(chat_id=chat_id, text="Действие отменено.")

    return True


async def _run_restore_and_report(chat_id: int, actor_tg_user_id: int, restore_path: Path, restore_name: str) -> None:
    try:
        file_size = restore_path.stat().st_size if restore_path.exists() else 0
        result = await backup_service.restore_from_path(
            path=restore_path,
            actor_tg_user_id=actor_tg_user_id,
            source=f"telegram_upload:{restore_name}",
        )
        status = result.get("status")
        warning_summary = result.get("warning_summary")
        if status == "ok_with_warnings":
            text = (
                "⚠️ Восстановление завершено с warnings\n"
                f"Файл: {result.get('file')}\n"
                f"Тип: {result.get('file_type')}\n"
                f"Время: {result.get('duration_seconds')} сек\n"
                f"Размер: {file_size} байт\n"
                f"Подробности: {warning_summary or 'см. логи'}"
            )
        else:
            text = (
                "✅ Восстановление завершено\n"
                f"Файл: {result.get('file')}\n"
                f"Тип: {result.get('file_type')}\n"
                f"Время: {result.get('duration_seconds')} сек\n"
                f"Размер: {file_size} байт"
            )
        await send_message(chat_id=chat_id, text=text)
    except BackupBusyError:
        await send_message(chat_id=chat_id, text="Операция уже выполняется. Попробуйте позже.")
    except Exception as exc:  # noqa: BLE001
        await send_message(chat_id=chat_id, text=f"❌ Восстановление завершилось ошибкой: {exc}")


@router.get("/telegram/health")
async def telegram_health() -> dict[str, bool]:
    return {"ok": True}


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if backup_service.is_maintenance:
        return {"ok": True, "detail": "maintenance: restore in progress"}
    tg_settings = await get_tg_notifications_settings(db)
    required_secret = settings.telegram_webhook_secret or tg_settings.webhook_secret
    if not required_secret:
        logger.error("tg_webhook.reject reason=no_secret")
        return {"ok": False, "detail": "webhook secret is not configured"}
    if not await _is_valid_secret(request, required_secret):
        logger.warning("tg_webhook.reject reason=invalid_secret")
        return {"ok": False, "detail": "invalid secret"}

    try:
        update = await request.json()
    except Exception:  # noqa: BLE001
        return {"ok": True}

    await process_update(update, db)
    return {"ok": True}


async def process_update(update: dict[str, Any], db: AsyncSession) -> None:
    update_id = update.get("update_id")
    if isinstance(update_id, int) and _is_processed_recently(_PROCESSED_UPDATES, update_id):
        logger.info("tg_update.skipped reason=duplicate update_id=%s", update_id)
        return

    log_update_received(update)
    try:
        if "message" in update:
            await _handle_message(update["message"], db)
        elif "callback_query" in update:
            await _handle_callback(update["callback_query"], db)
    except Exception:  # noqa: BLE001
        logger.exception("tg_update.failed")


async def _handle_message(message: dict[str, Any], db: AsyncSession) -> None:
    text = str(message.get("text") or "").strip()
    tg_user = message.get("from") or {}
    telegram_user_id = tg_user.get("id")
    if not telegram_user_id:
        return
    telegram_user_id = int(telegram_user_id)

    chat_id = (message.get("chat") or {}).get("id")
    access = await _resolve_telegram_access(db, telegram_user_id)

    if text in {"/admin", "/sys"}:
        if text == "/sys" and access.admin_role != AdminRole.sys_admin:
            await send_message(chat_id=telegram_user_id, text="⛔️ Доступ запрещен")
            return
        if not access.is_admin:
            await send_message(chat_id=telegram_user_id, text="⛔️ Доступ запрещен")
            return
        await send_message(
            chat_id=telegram_user_id,
            text=f"✅ Доступ разрешен. Ваша роль: {access.admin_role.value}\n\n{ADMIN_MENU}",
            reply_markup=_admin_reply_keyboard(access.admin_role),
        )
        return

    if text.startswith("/start"):
        payload = ""
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            payload = parts[1].strip()
        linked_master = False

        if payload:
            result = await db.execute(select(Master).where(Master.telegram_link_code == payload))
            master = result.scalar_one_or_none()
            if master:
                master.telegram_user_id = int(telegram_user_id)
                master.telegram_chat_id = int(chat_id) if chat_id is not None else None
                master.telegram_username = tg_user.get("username")
                master.telegram_linked_at = datetime.now(timezone.utc)
                master.telegram_link_code = None
                await db.flush()
                await send_message(chat_id=telegram_user_id, text=f"Telegram успешно привязан к мастеру {master.name}.")
                linked_master = True
                access.master = master
            else:
                await send_message(chat_id=telegram_user_id, text="Код привязки не найден или устарел.")

        if access.is_admin:
            await send_message(chat_id=telegram_user_id, text=ADMIN_MENU, reply_markup=_admin_reply_keyboard(access.admin_role))
            return

        if access.is_master:
            start_text = "Мастерский доступ активирован." if linked_master else "Вы в мастерском разделе."
            await send_message(chat_id=telegram_user_id, text=f"{start_text}\n\n{MASTER_MENU}", reply_markup=_master_reply_keyboard())
            return

        logger.info("tg_access denied user_id=%s", telegram_user_id)
        await send_message(chat_id=telegram_user_id, text="Нет доступа. Используйте /start <token> для привязки Telegram к мастеру.")
        return


    if access.admin_role == AdminRole.sys_admin and _is_private_chat(message):
        pending = PENDING_RESTORE_UPLOADS.get(telegram_user_id)
        if pending and pending.awaiting_upload:
            document = message.get("document") or {}
            file_id = document.get("file_id")
            file_name = str(document.get("file_name") or "")
            file_size = int(document.get("file_size") or 0)
            if not file_id:
                await send_message(chat_id=telegram_user_id, text="Ожидаю документ с файлом бэкапа.")
                return

            allowed_suffixes = (".dump", ".backup", ".sql", ".sql.gz", ".gpg")
            lowered = file_name.lower()
            if not lowered.endswith(allowed_suffixes):
                await send_message(chat_id=telegram_user_id, text="Неподдерживаемый формат. Разрешено: .dump, .backup, .sql, .sql.gz, .gpg")
                return

            max_bytes = int(settings.restore_max_mb) * 1024 * 1024
            if file_size and file_size > max_bytes:
                await send_message(
                    chat_id=telegram_user_id,
                    text=f"Файл слишком большой: {_format_file_size(file_size)}. Лимит: {settings.restore_max_mb} MB.",
                )
                return

            stored_path, actual_size = await backup_service.download_telegram_document(file_id=str(file_id), original_name=file_name or "restore_upload.bin")
            detected_type = _detect_uploaded_restore_type(file_name or stored_path.name)
            pending.awaiting_upload = False
            pending.file_path = str(stored_path)
            pending.file_name = file_name or stored_path.name
            pending.file_size_bytes = actual_size
            pending.detected_type = detected_type
            pending.uploaded_at_iso = datetime.now(timezone.utc).isoformat()
            PENDING_RESTORE_UPLOADS[telegram_user_id] = pending

            await send_message(
                chat_id=telegram_user_id,
                text=(
                    "Файл принят. Проверьте данные перед восстановлением:\n"
                    f"Имя: {pending.file_name}\n"
                    f"Размер: {_format_file_size(pending.file_size_bytes or actual_size)}\n"
                    f"Тип: {pending.detected_type}\n"
                    f"Загружен: {pending.uploaded_at_iso}"
                ),
                reply_markup=_restore_confirmation_markup(),
            )
            return

    if access.is_admin:
        normalized_text = _normalize_action_text(text)

        if normalized_text in ADMIN_ACTION_ALIASES["new"]:
            await _send_admin_booking_list(db, int(chat_id), "new")
        elif normalized_text in ADMIN_ACTION_ALIASES["pending"]:
            await _send_admin_booking_list(db, int(chat_id), "pending")
        elif normalized_text in ADMIN_ACTION_ALIASES["masters"]:
            masters = (await db.execute(select(Master).where(Master.is_active.is_(True)).order_by(Master.sort_order, Master.name))).scalars().all()
            text_rows = [f"• {m.name} (id={m.id})" for m in masters] or ["Активные мастера не найдены."]
            await send_message(chat_id=int(chat_id), text="\n".join(text_rows))
        elif normalized_text in ADMIN_ACTION_ALIASES["help"]:
            await send_message(chat_id=int(chat_id), text="Используйте кнопки: Новые записи / Ожидают подтверждения / Мастера", reply_markup=_admin_reply_keyboard(access.admin_role))
        elif normalized_text in ADMIN_ACTION_ALIASES["backup"]:
            if access.admin_role != AdminRole.sys_admin or not _is_private_chat(message):
                await send_message(chat_id=int(chat_id), text="Раздел резервных копий доступен только SYS_ADMIN в личном чате.")
            else:
                await _send_backup_menu(chat_id=int(chat_id), actor_tg_user_id=telegram_user_id)
        else:
            await send_message(chat_id=int(chat_id), text="Не понял команду. Выберите действие кнопкой ниже.", reply_markup=_admin_reply_keyboard(access.admin_role))
        return

    if access.is_master:
        await _handle_master_message(db, int(chat_id), text, access.master)
        return

    logger.info("tg_access denied user_id=%s", telegram_user_id)
    await send_message(chat_id=telegram_user_id, text="Нет доступа")


async def _safe_log_event(
    db: AsyncSession,
    actor_tg_user_id: int,
    actor_role: AdminRole | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None,
    meta: dict[str, Any] | None = None,
) -> None:
    try:
        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=actor_tg_user_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta,
        )
    except Exception:  # noqa: BLE001
        logger.warning("tg_audit.skipped action=%s reason=db_error", action, exc_info=True)



async def _handle_callback(callback_query: dict[str, Any], db: AsyncSession) -> None:
    callback_id = callback_query.get("id")
    data = callback_query.get("data")
    message = callback_query.get("message") or {}
    actor = callback_query.get("from") or {}
    actor_name = actor.get("username") or actor.get("first_name")
    actor_tg_user_id = actor.get("id")
    if actor_tg_user_id is None:
        if callback_id:
            await answer_callback_query(callback_id, "Нет доступа")
        return

    if callback_id and _is_processed_recently(_PROCESSED_CALLBACKS, callback_id):
        logger.info("tg_callback.skipped reason=duplicate callback_id=%s", callback_id)
        await answer_callback_query(callback_id, "Уже обработано")
        return

    access = await _resolve_telegram_access(db, int(actor_tg_user_id))

    master_parsed = _parse_master_callback(str(data or ""))
    if master_parsed:
        if not access.is_master:
            logger.info("tg_master denied user_id=%s", actor_tg_user_id)
            if callback_id:
                await answer_callback_query(callback_id, "Нет доступа")
            return
        callback_chat_id = (message.get("chat") or {}).get("id")
        if callback_chat_id is None:
            if callback_id:
                await answer_callback_query(callback_id, "Не удалось определить чат")
            return
        await _send_master_bookings(
            db=db,
            chat_id=int(callback_chat_id),
            master=access.master,
            page=int(master_parsed["page"]),
        )
        if callback_id:
            await answer_callback_query(callback_id)
        return

    callback_chat = message.get("chat") or {}
    if str(data or "").startswith("bk:"):
        if access.admin_role != AdminRole.sys_admin or callback_chat.get("type") != "private":
            if callback_id:
                await answer_callback_query(callback_id, "Нет доступа")
            return
        handled = await _handle_backup_callback(
            callback_id=callback_id,
            data=str(data),
            message=message,
            actor_tg_user_id=int(actor_tg_user_id),
        )
        if handled:
            return

    if not access.is_admin:
        logger.info("tg_admin denied user_id=%s", actor_tg_user_id)
        if callback_id:
            await answer_callback_query(callback_id, "Нет доступа")
        return

    parsed = parse_callback_data(str(data or ""))
    if not parsed:
        if callback_id:
            await answer_callback_query(callback_id, "Неизвестное действие")
        return

    booking_id = int(parsed["booking_id"])
    booking = (
        await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.service), selectinload(Booking.master), selectinload(Booking.master).selectinload(Master.services))
        )
    ).scalar_one_or_none()

    if not booking:
        if callback_id:
            await answer_callback_query(callback_id, "Запись не найдена")
        return

    action = parsed["action"]
    if action == "choose":
        masters = (
            await db.execute(select(Master).where(Master.is_active.is_(True)).order_by(Master.sort_order, Master.name))
        ).scalars().all()
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Выбор мастера"),
            reply_markup=_master_picker_keyboard(booking.id, masters),
        )
        if callback_id:
            await answer_callback_query(callback_id)
        return

    if action == "assign":
        master_id = int(parsed["master_id"])
        master = (await db.execute(select(Master).where(Master.id == master_id, Master.is_active.is_(True)))).scalar_one_or_none()
        if not master:
            if callback_id:
                await answer_callback_query(callback_id, "Мастер не найден")
            return
        booking.master_id = master.id
        booking.master = master
        await db.flush()
        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=access.admin_role,
            action="booking.assign_master",
            entity_type="booking",
            entity_id=booking.id,
            meta={"master_id": master.id, "master_name": master.name},
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, f"Мастер назначен: {master.name}", actor_name),
            reply_markup=build_admin_inline_keyboard(booking.id),
        )
        if callback_id:
            await answer_callback_query(callback_id, "Мастер назначен")
        return

    if action == "confirm":
        if booking.master_id is None:
            if callback_id:
                await answer_callback_query(callback_id, "Сначала назначьте мастера")
            return
        if booking.status != BookingStatus.confirmed:
            booking.status = BookingStatus.confirmed
            booking.is_read = True
            await db.flush()

        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=access.admin_role,
            action="booking.confirm",
            entity_type="booking",
            entity_id=booking.id,
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Подтверждено", actor_name),
            reply_markup=build_admin_inline_keyboard(booking.id),
        )

        tg_settings = await get_tg_notifications_settings(db)
        if tg_settings.admin_chat_id:
            try:
                await send_message(
                    chat_id=tg_settings.admin_chat_id,
                    thread_id=tg_settings.thread_id,
                    text=booking_admin_text(
                        {
                            "booking_id": booking.id,
                            "master_name": booking.master.name if booking.master else "Не назначен",
                        },
                        template=tg_settings.template_booking_confirmed_admin,
                    ),
                )
            except Exception:  # noqa: BLE001
                logger.exception("tg_notify.booking_confirmed_admin failed booking_id=%s", booking.id)

        sent_to_master = await send_master_booking_notification(db, booking.id)
        if not sent_to_master:
            await send_message(
                chat_id=message.get("chat", {}).get("id"),
                text=f"Booking #{booking.id}: у мастера не привязан Telegram, уведомление не отправлено",
            )

        if callback_id:
            await answer_callback_query(callback_id, "Подтверждено")
        return

    if action == "cancel":
        if booking.status != BookingStatus.cancelled:
            booking.status = BookingStatus.cancelled
            booking.is_read = True
            await db.flush()
        await log_event(
            db,
            actor_type=AuditActorType.telegram,
            actor_tg_user_id=int(actor_tg_user_id),
            actor_role=access.admin_role,
            action="booking.cancel",
            entity_type="booking",
            entity_id=booking.id,
        )
        await edit_message_text(
            chat_id=message.get("chat", {}).get("id"),
            message_id=message.get("message_id"),
            text=_admin_update_text(booking, "Отменено", actor_name),
            reply_markup=None,
        )

        if callback_id:
            await answer_callback_query(callback_id, "Отменено")
