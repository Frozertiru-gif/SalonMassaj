import unittest

from pydantic import ValidationError

from app.core.config import Settings


class SettingsBackupConfigTests(unittest.TestCase):
    def test_empty_backup_chat_id_string_becomes_none(self):
        settings = Settings(backup_enabled=False, backup_chat_id="   ")
        self.assertIsNone(settings.backup_chat_id)

    def test_backup_requires_chat_id_when_enabled(self):
        with self.assertRaises(ValidationError) as context:
            Settings(backup_enabled=True, backup_chat_id="")

        self.assertIn("BACKUP_CHAT_ID must be configured when BACKUP_ENABLED=true", str(context.exception))

    def test_backup_accepts_chat_id_when_enabled(self):
        settings = Settings(backup_enabled=True, backup_chat_id="-1001234567890")
        self.assertEqual(settings.backup_chat_id, -1001234567890)


if __name__ == "__main__":
    unittest.main()
