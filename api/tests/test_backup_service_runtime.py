import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import settings
from app.services.backup_service import BackupService


class BackupServiceRuntimeValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._backup_dir = Path(self._tmp.name) / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_service(self) -> BackupService:
        with patch.object(settings, "backup_dir", str(self._backup_dir)):
            return BackupService()

    def test_validate_backup_runtime_fails_when_bash_is_missing(self):
        script_path = Path(self._tmp.name) / "backup_db.sh"
        script_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n", encoding="utf-8")
        script_path.chmod(0o755)

        service = self._make_service()
        with patch.object(settings, "backup_script_path", str(script_path)), patch("app.services.backup_service.shutil.which", return_value=None):
            with self.assertRaises(RuntimeError) as context:
                service._validate_backup_runtime()

        self.assertIn("bash is not available in PATH", str(context.exception))

    def test_validate_backup_runtime_fails_when_script_not_executable(self):
        script_path = Path(self._tmp.name) / "backup_db.sh"
        script_path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n", encoding="utf-8")
        script_path.chmod(0o644)

        service = self._make_service()
        with patch.object(settings, "backup_script_path", str(script_path)), patch("app.services.backup_service.shutil.which", return_value="/usr/bin/bash"):
            with self.assertRaises(RuntimeError) as context:
                service._validate_backup_runtime()

        self.assertIn("backup script is not executable", str(context.exception))


if __name__ == "__main__":
    unittest.main()
