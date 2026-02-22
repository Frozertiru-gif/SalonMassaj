import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.services.backup_service import BackupService, RestoreExecution


class BackupServiceRestoreSmokeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._backup_dir = Path(self._tmp.name) / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_service(self) -> BackupService:
        with patch.object(settings, "backup_dir", str(self._backup_dir)):
            return BackupService()

    async def test_restore_custom_dump_path_returns_warning_status(self):
        service = self._make_service()
        dump_path = Path(self._tmp.name) / "uploaded.dump"
        dump_path.write_bytes(b"PGDMPabcdef")

        with (
            patch.object(service, "_log_pg_runtime_versions", new=AsyncMock()),
            patch("app.services.backup_service.dispose_engine", new=AsyncMock()),
            patch("app.services.backup_service.reinitialize_engine"),
            patch.object(service, "_terminate_other_db_connections", new=AsyncMock()),
            patch.object(
                service,
                "_restore_custom_dump",
                new=AsyncMock(
                    return_value=RestoreExecution(
                        stdout="done",
                        stderr='pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"\n'
                        "pg_restore: warning: errors ignored on restore: 1\n",
                        returncode=1,
                    )
                ),
            ),
            patch.object(service, "_health_check_db", new=AsyncMock()),
        ):
            result = await service.restore_from_path(path=dump_path, actor_tg_user_id=1, source="test")

        self.assertEqual(result["status"], "ok_with_warnings")
        self.assertTrue(result["warning_summary"])


if __name__ == "__main__":
    unittest.main()
