import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import settings
from app.services.backup_service import BackupService, RestoreExecution


class BackupServiceRestoreCompatTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._backup_dir = Path(self._tmp.name) / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_service(self) -> BackupService:
        with patch.object(settings, "backup_dir", str(self._backup_dir)):
            return BackupService()

    def test_detect_dump_format_custom(self):
        service = self._make_service()
        dump_path = Path(self._tmp.name) / "custom.dump"
        dump_path.write_bytes(b"PGDMP\x01\x02\x03")

        self.assertEqual(service._detect_dump_format(dump_path), "custom")

    def test_detect_dump_format_plain_sql(self):
        service = self._make_service()
        dump_path = Path(self._tmp.name) / "plain.sql"
        dump_path.write_text("SET statement_timeout = 0;\n", encoding="utf-8")

        self.assertEqual(service._detect_dump_format(dump_path), "plain_sql")

    def test_filter_incompatible_sql_settings_removes_only_transaction_timeout(self):
        service = self._make_service()
        source_path = Path(self._tmp.name) / "source.sql"
        target_path = Path(self._tmp.name) / "target.sql"
        source_path.write_text(
            "SET statement_timeout = 0;\n"
            "SET transaction_timeout = 0;\n"
            "SET transaction_timeout TO '10s';\n"
            "SELECT 1;\n",
            encoding="utf-8",
        )

        removed_count = service._filter_incompatible_sql_settings(source_path=source_path, target_path=target_path)

        self.assertEqual(removed_count, 2)
        self.assertEqual(
            target_path.read_text(encoding="utf-8"),
            "SET statement_timeout = 0;\n"
            "SELECT 1;\n",
        )

    def test_restore_stderr_classifier_known_non_fatal(self):
        service = self._make_service()
        stderr = (
            'pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"\n'
            "pg_restore: warning: errors ignored on restore: 1\n"
        )

        self.assertTrue(service._is_known_non_fatal_restore_stderr(stderr))

    def test_restore_stderr_classifier_fatal(self):
        service = self._make_service()
        stderr = "pg_restore: error: relation \"admins\" does not exist"

        self.assertFalse(service._is_known_non_fatal_restore_stderr(stderr))

    def test_restore_execution_non_fatal_error_code_is_accepted(self):
        service = self._make_service()
        execution = RestoreExecution(
            stdout="",
            stderr='pg_restore: error: could not execute query: ERROR:  unrecognized configuration parameter "transaction_timeout"\n'
            "pg_restore: warning: errors ignored on restore: 1\n",
            returncode=1,
        )

        service._handle_restore_execution(execution)

    def test_restore_execution_fatal_error_code_raises(self):
        service = self._make_service()
        execution = RestoreExecution(stdout="", stderr='pg_restore: error: syntax error at or near "BAD"', returncode=1)

        with self.assertRaises(RuntimeError):
            service._handle_restore_execution(execution)


if __name__ == "__main__":
    unittest.main()
