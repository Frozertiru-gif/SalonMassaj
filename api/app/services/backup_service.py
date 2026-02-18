import asyncio
import fcntl
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
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
    CUSTOM_DUMP_MAGIC = b"PGDMP"
    TRANSACTION_TIMEOUT_SET_RE = re.compile(br"^\s*SET\s+transaction_timeout\s*(?:=|TO)\s*[^;]+;\s*$", re.IGNORECASE)

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

            script_path, bash_path = self._validate_backup_runtime()
            script_head = self._read_script_head(script_path)
            logger.info(
                "backup.runtime launch bash=%s script=%s head=%s",
                bash_path,
                script_path,
                script_head,
            )

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

    def _validate_backup_runtime(self) -> tuple[Path, str]:
        script_path = Path(settings.backup_script_path)
        bash_path = shutil.which("bash")

        validation_errors: list[str] = []
        if not bash_path:
            validation_errors.append("bash is required to run backup script")
        if not script_path.exists():
            validation_errors.append(f"backup script not found: {script_path}")
        elif not script_path.is_file():
            validation_errors.append(f"backup script path is not a file: {script_path}")

        if validation_errors:
            message = "Backup runtime validation failed: " + "; ".join(validation_errors)
            logger.error(message)
            raise RuntimeError(message)

        logger.info("backup.runtime resolved bash=%s", bash_path)
        self._check_bash_pipefail(str(bash_path))
        self._log_script_diagnostics(script_path)
        return script_path, str(bash_path)

    @staticmethod
    def _check_bash_pipefail(bash_path: str) -> None:
        check = subprocess.run(
            [bash_path, "-lc", "set -o pipefail"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode != 0:
            stderr = (check.stderr or "").strip()
            message = f"bash self-check failed for pipefail: {stderr or 'unknown error'}"
            logger.error(message)
            raise RuntimeError(message)

    @staticmethod
    def _read_script_head(script_path: Path) -> list[str]:
        return script_path.read_text(encoding="utf-8", errors="replace").splitlines()[:2]

    def _log_script_diagnostics(self, script_path: Path) -> None:
        script_bytes = script_path.read_bytes()
        if b"\r\n" in script_bytes:
            logger.warning("backup script has CRLF line endings path=%s", script_path)

        logger.info("backup.script head path=%s head=%s", script_path, self._read_script_head(script_path))

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

        with tempfile.TemporaryDirectory(prefix="restore_") as tmp_dir:
            decrypted_dump_path = Path(tmp_dir) / "decrypted.dump"
            await self._decrypt_backup(
                encrypted_dump_path=encrypted_dump_path,
                decrypted_dump_path=decrypted_dump_path,
                passphrase=passphrase,
            )

            dump_format = self._detect_dump_format(decrypted_dump_path)
            logger.info("backup.restore format_detected format=%s file=%s", dump_format, encrypted_dump_path)

            if dump_format == "custom":
                stdout = await self._restore_custom_dump(
                    dump_path=decrypted_dump_path,
                    db_host=db_host,
                    db_port=db_port,
                    db_user=db_user,
                    db_name=db_name,
                    env=env,
                )
            else:
                filtered_sql_path = Path(tmp_dir) / "filtered.sql"
                removed_count = self._filter_incompatible_sql_settings(
                    source_path=decrypted_dump_path,
                    target_path=filtered_sql_path,
                )
                if removed_count:
                    logger.info(
                        "backup.restore compatibility_filter removed=%s parameter=transaction_timeout reason=compat_with_pg",
                        removed_count,
                    )
                stdout = await self._restore_plain_sql_dump(
                    sql_path=filtered_sql_path,
                    db_host=db_host,
                    db_port=db_port,
                    db_user=db_user,
                    db_name=db_name,
                    env=env,
                )

        logger.info("backup.restore success file=%s stdout=%s", encrypted_dump_path, stdout)
        return {"ok": True, "file": encrypted_dump_path.name}

    async def _decrypt_backup(self, encrypted_dump_path: Path, decrypted_dump_path: Path, passphrase: str) -> None:
        process = await asyncio.create_subprocess_exec(
            "gpg",
            "--batch",
            "--yes",
            "--decrypt",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            passphrase,
            "--output",
            str(decrypted_dump_path),
            str(encrypted_dump_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Restore failed during decrypt: {(stderr or b'').decode().strip()}")

    def _detect_dump_format(self, decrypted_dump_path: Path) -> str:
        with decrypted_dump_path.open("rb") as handle:
            header = handle.read(len(self.CUSTOM_DUMP_MAGIC))
        if header == self.CUSTOM_DUMP_MAGIC:
            return "custom"
        return "plain_sql"

    def _filter_incompatible_sql_settings(self, source_path: Path, target_path: Path) -> int:
        removed_count = 0
        with source_path.open("rb") as source, target_path.open("wb") as target:
            for raw_line in source:
                if self.TRANSACTION_TIMEOUT_SET_RE.match(raw_line.rstrip(b"\r\n")):
                    removed_count += 1
                    continue
                target.write(raw_line)
        return removed_count

    async def _restore_custom_dump(self, dump_path: Path, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> str:
        process = await asyncio.create_subprocess_exec(
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            str(dump_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Restore failed: {(stderr or b'').decode().strip()}")
        return (stdout or b"").decode().strip()

    async def _restore_plain_sql_dump(self, sql_path: Path, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> str:
        process = await asyncio.create_subprocess_exec(
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-f",
            str(sql_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Restore failed: {(stderr or b'').decode().strip()}")
        return (stdout or b"").decode().strip()

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
