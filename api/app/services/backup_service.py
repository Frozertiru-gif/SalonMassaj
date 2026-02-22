import asyncio
import fcntl
import gzip
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from app.core.config import settings
from app.db import dispose_engine
from app.services.telegram import TelegramError, get_file, send_document, send_message

logger = logging.getLogger(__name__)


class BackupBusyError(RuntimeError):
    pass


@dataclass(slots=True)
class RestoreResult:
    ok: bool
    status: str
    file: str
    file_type: str
    duration_seconds: float
    removed_incompatible_sets: int = 0
    stderr_tail: str | None = None
    warning_summary: str | None = None


@dataclass(slots=True)
class RestoreExecution:
    stdout: str
    stderr: str
    returncode: int


class BackupService:
    CUSTOM_DUMP_MAGIC = b"PGDMP"
    SQL_SET_TIMEOUT_RE = re.compile(br"^\s*SET\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|TO)\s*[^;]+;\s*$", re.IGNORECASE)
    SUPPORTED_TIMEOUT_SETTINGS = {
        b"statement_timeout",
        b"lock_timeout",
        b"idle_in_transaction_session_timeout",
        b"idle_session_timeout",
        b"deadlock_timeout",
    }
    REQUIRED_RESTORED_TABLES = ("alembic_version", "admins", "masters", "services", "bookings")

    def __init__(self) -> None:
        self._async_lock = asyncio.Lock()
        self.backup_dir = Path(settings.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = self.backup_dir / ".backup.lock"
        self.metadata_path = self.backup_dir / "last_backup.json"
        self.restore_log_path = self.backup_dir / "restore.log"
        self.restore_dir = self.backup_dir / "restores"
        self.restore_dir.mkdir(parents=True, exist_ok=True)
        self._maintenance_event = asyncio.Event()

    @property
    def is_maintenance(self) -> bool:
        return self._maintenance_event.is_set()

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
            database_url = env.get("DATABASE_URL") or settings.database_url
            db_host, db_port, db_name, db_user, db_password = self._parse_database_url(database_url)
            env["PGPASSWORD"] = db_password
            await self._log_pg_runtime_versions(env, db_host=db_host, db_port=db_port, db_user=db_user, db_name=db_name)

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

        return await self.restore_from_path(path=path, actor_tg_user_id=actor_tg_user_id, source=f"local:{path.name}")

    async def restore_from_uploaded_document(self, file_id: str, actor_tg_user_id: int) -> dict[str, Any]:
        file_path, _ = await self.download_telegram_document(file_id=file_id, original_name=f"uploaded_{file_id}.gpg")
        return await self.restore_from_path(path=file_path, actor_tg_user_id=actor_tg_user_id, source=f"telegram:{file_id}")

    async def download_telegram_document(self, file_id: str, original_name: str) -> tuple[Path, int]:
        file_info = await get_file(file_id)
        info = (file_info or {}).get("result") or {}
        file_path = info.get("file_path")
        file_size = int(info.get("file_size") or 0)
        if not file_path:
            raise RuntimeError("Telegram file path is missing")

        token = settings.telegram_bot_token
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        destination = self.restore_dir / f"restore_{timestamp}_{self._sanitize_filename(original_name)}"
        url = f"https://api.telegram.org/file/bot{token}/{file_path}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            destination.write_bytes(response.content)

        return destination, int(destination.stat().st_size or file_size)

    async def restore_from_path(self, path: Path, actor_tg_user_id: int, source: str | None = None) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            started = datetime.now(tz=timezone.utc)
            self._maintenance_event.set()
            try:
                result = await self._restore_from_file(path)
            except Exception as exc:  # noqa: BLE001
                stderr_tail = self._error_tail(str(exc))
                logger.exception("backup.restore failed file=%s source=%s", path, source or f"path:{path.name}")
                self._append_restore_log(actor_tg_user_id=actor_tg_user_id, source=source or f"path:{path.name}", status="error", detail=stderr_tail)
                raise RuntimeError(stderr_tail) from exc
            finally:
                self._maintenance_event.clear()

            duration = (datetime.now(tz=timezone.utc) - started).total_seconds()
            result.duration_seconds = duration
            self._append_restore_log(
                actor_tg_user_id=actor_tg_user_id,
                source=source or f"path:{path.name}",
                status="ok",
                detail=f"type={result.file_type} removed_sets={result.removed_incompatible_sets} duration={duration:.2f}s",
            )
            return {
                "ok": result.ok,
                "status": result.status,
                "file": result.file,
                "file_type": result.file_type,
                "duration_seconds": round(duration, 2),
                "removed_incompatible_sets": result.removed_incompatible_sets,
                "warning_summary": result.warning_summary,
            }

        return await self._with_operation_lock(_run)

    async def _restore_from_file(self, input_path: Path) -> RestoreResult:
        if not input_path.exists() or not input_path.is_file():
            raise RuntimeError("Restore file is missing")

        env = os.environ.copy()
        backup_env_path = Path(settings.backup_env_path)
        if backup_env_path.exists():
            env.update(self._read_env_file(backup_env_path))

        database_url = env.get("DATABASE_URL") or settings.database_url
        db_host, db_port, db_name, db_user, db_password = self._parse_database_url(database_url)
        passphrase = env.get("BACKUP_PASSPHRASE") or settings.backup_passphrase

        env["PGPASSWORD"] = db_password
        removed_count = 0
        detected_type = "unknown"
        execution = RestoreExecution(stdout="", stderr="", returncode=0)
        await self._log_pg_runtime_versions(env, db_host=db_host, db_port=db_port, db_user=db_user, db_name=db_name)
        logger.info("backup.restore started file=%s", input_path)

        with tempfile.TemporaryDirectory(prefix="restore_") as tmp_dir:
            await dispose_engine()
            try:
                restore_input_path = input_path
                if input_path.suffix.lower() == ".gpg":
                    if not passphrase:
                        raise RuntimeError("BACKUP_PASSPHRASE is not configured")
                    decrypted_dump_path = Path(tmp_dir) / "decrypted.restore"
                    await self._decrypt_backup(
                        encrypted_dump_path=input_path,
                        decrypted_dump_path=decrypted_dump_path,
                        passphrase=passphrase,
                    )
                    restore_input_path = decrypted_dump_path

                if restore_input_path.suffix.lower() == ".gz":
                    gunzipped_path = Path(tmp_dir) / "restore.sql"
                    with gzip.open(restore_input_path, "rb") as source, gunzipped_path.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    restore_input_path = gunzipped_path

                await self._ensure_restore_runtime_compatibility(db_host=db_host, db_port=db_port, db_user=db_user, db_name=db_name, env=env)
                await self._terminate_other_db_connections(db_host, db_port, db_user, db_name, env)
                await self._reset_public_schema(db_host, db_port, db_user, db_name, env)
                dump_format = self._detect_dump_format(restore_input_path)
                detected_type = dump_format
                logger.info("backup.restore format_detected format=%s file=%s", dump_format, input_path)

                if dump_format == "custom":
                    execution = await self._restore_custom_dump(
                        dump_path=restore_input_path,
                        db_host=db_host,
                        db_port=db_port,
                        db_user=db_user,
                        db_name=db_name,
                        env=env,
                    )
                else:
                    filtered_sql_path = Path(tmp_dir) / "filtered.sql"
                    removed_count = self._filter_incompatible_sql_settings(
                        source_path=restore_input_path,
                        target_path=filtered_sql_path,
                    )
                    if removed_count:
                        logger.info(
                            "backup.restore compatibility_filter removed=%s parameter=transaction_timeout reason=compat_with_pg",
                            removed_count,
                        )
                    execution = await self._restore_plain_sql_dump(
                        sql_path=filtered_sql_path,
                        db_host=db_host,
                        db_port=db_port,
                        db_user=db_user,
                        db_name=db_name,
                        env=env,
                    )

                self._handle_restore_execution(execution)
                await self._health_check_db(db_host=db_host, db_port=db_port, db_user=db_user, db_name=db_name, env=env)
                await self._verify_restored_schema(db_host=db_host, db_port=db_port, db_user=db_user, db_name=db_name, env=env)
            finally:
                await dispose_engine()

        warning_summary = self._summarize_warnings(execution.stderr)
        status = "ok_with_warnings" if warning_summary else "ok"
        logger.info("backup.restore success file=%s status=%s stdout=%s", input_path, status, execution.stdout)
        return RestoreResult(
            ok=True,
            status=status,
            file=input_path.name,
            file_type=detected_type,
            duration_seconds=0,
            removed_incompatible_sets=removed_count,
            warning_summary=warning_summary,
        )

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
                if self._should_remove_timeout_set(raw_line):
                    removed_count += 1
                    continue
                target.write(raw_line)
        return removed_count

    def _should_remove_timeout_set(self, raw_line: bytes) -> bool:
        match = self.SQL_SET_TIMEOUT_RE.match(raw_line.rstrip(b"\r\n"))
        if not match:
            return False

        parameter_name = match.group(1).lower()
        return parameter_name.endswith(b"timeout") and parameter_name not in self.SUPPORTED_TIMEOUT_SETTINGS

    async def _restore_custom_dump(self, dump_path: Path, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> RestoreExecution:
        command = [
            "pg_restore",
            "--exit-on-error",
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
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        stdout_text = (stdout or b"").decode(errors="replace").strip()
        stderr_text = (stderr or b"").decode(errors="replace").strip()
        self._log_restore_process_result("custom_dump", command, process.returncode, stderr_text)
        return RestoreExecution(stdout=stdout_text, stderr=stderr_text, returncode=process.returncode)

    async def _restore_plain_sql_dump(self, sql_path: Path, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> RestoreExecution:
        command = [
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
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        stdout_text = (stdout or b"").decode(errors="replace").strip()
        stderr_text = (stderr or b"").decode(errors="replace").strip()
        self._log_restore_process_result("plain_sql", command, process.returncode, stderr_text)
        return RestoreExecution(stdout=stdout_text, stderr=stderr_text, returncode=process.returncode)

    def _handle_restore_execution(self, execution: RestoreExecution) -> None:
        if execution.returncode != 0:
            raise RuntimeError(f"Restore failed: {self._error_tail(execution.stderr)}")

    def _summarize_warnings(self, stderr_text: str) -> str | None:
        lines = [line.strip() for line in stderr_text.splitlines() if line.strip()]
        warnings = [line for line in lines if "warning" in line.lower()]
        if not warnings:
            return None
        return "; ".join(warnings[:2])

    def _log_restore_process_result(self, dump_format: str, command: list[str], returncode: int, stderr_text: str) -> None:
        stderr_preview = " | ".join(stderr_text.splitlines()[:8])
        logger.info(
            "backup.restore exec format=%s command=%s returncode=%s stderr_preview=%s",
            dump_format,
            " ".join(command),
            returncode,
            stderr_preview,
        )

    async def _log_pg_runtime_versions(
        self,
        env: dict[str, str],
        db_host: str | None = None,
        db_port: str | None = None,
        db_user: str | None = None,
        db_name: str | None = None,
    ) -> None:
        for executable in ("pg_dump", "pg_restore"):
            process = await asyncio.create_subprocess_exec(
                executable,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await process.communicate()
            logger.info(
                "backup.runtime version tool=%s rc=%s output=%s",
                executable,
                process.returncode,
                ((stdout or stderr or b"").decode(errors="replace").strip()),
            )

        if all([db_host, db_port, db_user, db_name]):
            process = await asyncio.create_subprocess_exec(
                "psql",
                "-h",
                str(db_host),
                "-p",
                str(db_port),
                "-U",
                str(db_user),
                "-d",
                str(db_name),
                "-Atqc",
                "SELECT version()",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await process.communicate()
            logger.info(
                "backup.runtime db_version rc=%s output=%s",
                process.returncode,
                ((stdout or stderr or b"").decode(errors="replace").strip()),
            )

    async def _ensure_restore_runtime_compatibility(self, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> None:
        pg_restore_version = await self._read_command_output(["pg_restore", "--version"], env)
        pg_dump_version = await self._read_command_output(["pg_dump", "--version"], env)
        server_version_num = await self._read_command_output(
            [
                "psql",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-Atqc",
                "SHOW server_version_num",
            ],
            env,
        )
        server_version = await self._read_command_output(
            [
                "psql",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-Atqc",
                "SHOW server_version",
            ],
            env,
        )

        restore_major = self._extract_pg_major(pg_restore_version)
        dump_major = self._extract_pg_major(pg_dump_version)
        server_major = self._extract_server_major(server_version_num, server_version)
        logger.info(
            "backup.restore version_check pg_restore=%s pg_dump=%s server=%s",
            pg_restore_version,
            pg_dump_version,
            server_version,
        )
        if not restore_major or not dump_major or not server_major:
            raise RuntimeError("Не удалось определить версии PostgreSQL (pg_restore/pg_dump/server). Восстановление остановлено.")
        if restore_major != server_major or dump_major != server_major:
            raise RuntimeError(
                "Несовместимые версии PostgreSQL: "
                f"pg_restore={restore_major}, pg_dump={dump_major}, server={server_major}. "
                "Нужен клиент той же мажорной версии (иначе возможна ошибка transaction_timeout)."
            )

    async def _read_command_output(self, command: list[str], env: dict[str, str]) -> str:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        output = (stdout or b"").decode(errors="replace").strip() or (stderr or b"").decode(errors="replace").strip()
        if process.returncode != 0:
            raise RuntimeError(f"Команда завершилась с ошибкой: {' '.join(command)} :: {self._error_tail(output)}")
        return output

    @staticmethod
    def _extract_pg_major(version_text: str) -> int | None:
        match = re.search(r"(\d+)(?:\.\d+)?", version_text)
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_server_major(server_version_num: str, server_version_text: str) -> int | None:
        raw = (server_version_num or "").strip()
        if raw.isdigit() and len(raw) >= 2:
            return int(raw[:2]) if len(raw) > 2 else int(raw)
        match = re.search(r"(\d+)(?:\.\d+)?", server_version_text)
        return int(match.group(1)) if match else None

    async def _terminate_other_db_connections(self, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> None:
        sql = (
            "SELECT pg_terminate_backend(pid) "
            "FROM pg_stat_activity "
            f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid()"
        )
        process = await asyncio.create_subprocess_exec(
            "psql",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-Atqc",
            sql,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            logger.warning("backup.restore terminate_connections failed: %s", (stderr or b"").decode(errors="replace").strip())

    async def _reset_public_schema(self, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> None:
        logger.info("backup.restore step=reset_schema database=%s", db_name)
        sql = (
            "DROP SCHEMA IF EXISTS public CASCADE;"
            "CREATE SCHEMA public;"
            "GRANT ALL ON SCHEMA public TO postgres;"
            "GRANT ALL ON SCHEMA public TO public;"
        )
        process = await asyncio.create_subprocess_exec(
            "psql",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-v",
            "ON_ERROR_STOP=1",
            "-Atqc",
            sql,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Не удалось очистить схему public: {(stderr or b'').decode(errors='replace').strip()}")

    async def _health_check_db(self, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> None:
        process = await asyncio.create_subprocess_exec(
            "psql",
            "-h",
            db_host,
            "-p",
            db_port,
            "-U",
            db_user,
            "-d",
            db_name,
            "-v",
            "ON_ERROR_STOP=1",
            "-Atqc",
            "SELECT 1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0 or (stdout or b"").decode().strip() != "1":
            raise RuntimeError(f"Restore health-check failed: {(stderr or b'').decode().strip()}")

    async def _verify_restored_schema(self, db_host: str, db_port: str, db_user: str, db_name: str, env: dict[str, str]) -> None:
        logger.info("backup.restore step=verify_schema")
        for table_name in self.REQUIRED_RESTORED_TABLES:
            sql = f"SELECT to_regclass('public.{table_name}') IS NOT NULL"
            process = await asyncio.create_subprocess_exec(
                "psql",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-Atqc",
                sql,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await process.communicate()
            exists = (stdout or b"").decode(errors="replace").strip().lower()
            if process.returncode != 0 or exists not in {"t", "true", "1"}:
                raise RuntimeError(
                    f"Restore verify failed: table public.{table_name} missing or unreadable: "
                    f"{(stderr or b'').decode(errors='replace').strip()}"
                )

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

    def _append_restore_log(self, actor_tg_user_id: int, source: str, status: str = "ok", detail: str | None = None) -> None:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        self.restore_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.restore_log_path.open("a", encoding="utf-8") as handle:
            suffix = f" detail={detail}" if detail else ""
            handle.write(f"{timestamp} actor={actor_tg_user_id} source={source} status={status}{suffix}\n")

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
        return safe or "upload.bin"

    @staticmethod
    def _error_tail(text: str, max_chars: int = 300) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_chars:
            return compact
        return f"…{compact[-max_chars:]}"


backup_service = BackupService()
