import asyncio
import fcntl
import json
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from app.core.config import settings
from app.services.telegram import TelegramError, get_file, send_document, send_message

logger = logging.getLogger(__name__)


class BackupBusyError(RuntimeError):
    pass


class BackupService:
    def __init__(self) -> None:
        self._async_lock = asyncio.Lock()
        self.backup_dir = Path(settings.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.backup_dir / ".backup.lock"
        self.metadata_path = self.backup_dir / "last_backup.json"
        self.restore_log_path = self.backup_dir / "restore.log"

    async def _with_operation_lock(self, coro):
        if self._async_lock.locked():
            raise BackupBusyError("backup or restore operation already in progress")

        async with self._async_lock:
            with self.lock_file.open("a+") as lock_handle:
                try:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise BackupBusyError("backup or restore operation already in progress") from exc
                try:
                    return await coro()
                finally:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    async def run_backup_script(self) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            env = os.environ.copy()
            backup_env_path = Path(settings.backup_env_path)
            if backup_env_path.exists():
                env.update(self._read_env_file(backup_env_path))

            bash_path, script_path = self._validate_backup_runtime()

            process = await asyncio.create_subprocess_exec(
                bash_path,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"Backup script failed: {(stderr or b'').decode().strip()}")

            logger.info("backup.script success output=%s", (stdout or b"").decode().strip())
            return self.get_latest_metadata()

        return await self._with_operation_lock(_run)

    def _validate_backup_runtime(self) -> tuple[str, Path]:
        bash_path = shutil.which("bash")
        script_path = Path(settings.backup_script_path)

        validation_errors: list[str] = []
        if not bash_path:
            validation_errors.append("bash is not available in PATH")
        if not script_path.exists():
            validation_errors.append(f"backup script not found: {script_path}")
        elif not script_path.is_file():
            validation_errors.append(f"backup script path is not a file: {script_path}")
        elif not os.access(script_path, os.X_OK):
            validation_errors.append(f"backup script is not executable: {script_path}")

        if validation_errors:
            message = "Backup runtime validation failed: " + "; ".join(validation_errors)
            logger.error(message)
            raise RuntimeError(message)

        return bash_path, script_path

    def get_latest_metadata(self) -> dict[str, Any]:
        if self.metadata_path.exists():
            try:
                payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                logger.warning("backup.metadata invalid json path=%s", self.metadata_path)

        backups = sorted(self.backup_dir.glob("*.dump.gpg"), reverse=True)
        if not backups:
            return {}
        latest = backups[0]
        created_at = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).isoformat()
        return {
            "filename": latest.name,
            "path": str(latest),
            "created_at": created_at,
            "size_bytes": latest.stat().st_size,
        }

    async def send_latest_to_backup_chat(self) -> dict[str, Any]:
        if not settings.backup_chat_id:
            raise RuntimeError("BACKUP_CHAT_ID is not configured")

        metadata = self.get_latest_metadata()
        if not metadata.get("path"):
            raise RuntimeError("No backups found")

        backup_path = Path(str(metadata["path"]))
        if not backup_path.exists():
            raise RuntimeError("Backup file not found")

        return await send_document(chat_id=settings.backup_chat_id, file_path=str(backup_path), caption=f"DB backup: {backup_path.name}")

    async def restore_latest_local_backup(self, actor_tg_user_id: int) -> dict[str, Any]:
        metadata = self.get_latest_metadata()
        if not metadata.get("path"):
            raise RuntimeError("No backups found")
        path = Path(str(metadata["path"]))

        async def _run() -> dict[str, Any]:
            result = await self._restore_from_file(path)
            self._append_restore_log(actor_tg_user_id=actor_tg_user_id, source=f"local:{path.name}")
            return result

        return await self._with_operation_lock(_run)

    async def restore_from_uploaded_document(self, file_id: str, actor_tg_user_id: int) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            file_info = await get_file(file_id)
            file_path = ((file_info or {}).get("result") or {}).get("file_path")
            if not file_path:
                raise RuntimeError("Telegram file path is missing")

            token = settings.telegram_bot_token
            if not token:
                raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

            url = f"https://api.telegram.org/file/bot{token}/{file_path}"
            temp_file = self.backup_dir / f"uploaded_{int(datetime.now(tz=timezone.utc).timestamp())}.dump.gpg"
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                temp_file.write_bytes(response.content)

            try:
                result = await self._restore_from_file(temp_file)
                self._append_restore_log(actor_tg_user_id=actor_tg_user_id, source=f"telegram:{file_id}")
                return result
            finally:
                temp_file.unlink(missing_ok=True)

        return await self._with_operation_lock(_run)

    async def _restore_from_file(self, encrypted_dump_path: Path) -> dict[str, Any]:
        env = os.environ.copy()
        backup_env_path = Path(settings.backup_env_path)
        if backup_env_path.exists():
            env.update(self._read_env_file(backup_env_path))

        database_url = env.get("DATABASE_URL") or settings.database_url
        db_host, db_port, db_name, db_user, db_password = self._parse_database_url(database_url)
        passphrase = env.get("BACKUP_PASSPHRASE") or settings.backup_passphrase
        if not passphrase:
            raise RuntimeError("BACKUP_PASSPHRASE is not configured")

        env["PGPASSWORD"] = db_password
        env["BACKUP_PASSPHRASE"] = passphrase
        restore_cmd = (
            f"gpg --batch --yes --decrypt --pinentry-mode loopback --passphrase \"$BACKUP_PASSPHRASE\" \"{encrypted_dump_path}\" "
            f"| pg_restore --clean --if-exists --no-owner --no-privileges -h \"{db_host}\" -p \"{db_port}\" -U \"{db_user}\" -d \"{db_name}\""
        )
        process = await asyncio.create_subprocess_exec(
            "bash",
            "-lc",
            restore_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Restore failed: {(stderr or b'').decode().strip()}")

        logger.info("backup.restore success file=%s stdout=%s", encrypted_dump_path, (stdout or b"").decode().strip())
        return {"ok": True, "file": encrypted_dump_path.name}

    @staticmethod
    def _read_env_file(path: Path) -> dict[str, str]:
        env_map: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_map[key.strip()] = value.strip().strip('"').strip("'")
        return env_map

    @staticmethod
    def _parse_database_url(url: str) -> tuple[str, str, str, str, str]:
        parsed = urlparse(url)
        if parsed.scheme.startswith("postgresql+"):
            parsed = parsed._replace(scheme=parsed.scheme.split("+", 1)[0])
        host = parsed.hostname or "localhost"
        port = str(parsed.port or 5432)
        db_name = (parsed.path or "/").lstrip("/")
        if not db_name:
            raise RuntimeError("Database name missing in DATABASE_URL")
        user = unquote(parsed.username or "postgres")
        password = unquote(parsed.password or "")
        return host, port, db_name, user, password

    def is_catchup_required(self) -> bool:
        metadata = self.get_latest_metadata()
        created_at = metadata.get("created_at")
        if not created_at:
            return True
        try:
            parsed = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        except ValueError:
            return True
        return datetime.now(tz=timezone.utc) - parsed > timedelta(hours=24)

    @staticmethod
    async def notify_sys_admins(text: str) -> None:
        admin_ids: list[int] = []
        for raw in (settings.telegram_sys_admin_ids or "").split(","):
            token = raw.strip()
            if token.isdigit():
                admin_ids.append(int(token))
        for admin_id in admin_ids:
            try:
                await send_message(chat_id=admin_id, text=text)
            except TelegramError:
                logger.exception("backup.notify_sys_admin failed chat_id=%s", admin_id)

    def _append_restore_log(self, actor_tg_user_id: int, source: str) -> None:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        self.restore_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.restore_log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} actor={actor_tg_user_id} source={source}\n")


backup_service = BackupService()
