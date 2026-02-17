import os
import unittest
from unittest.mock import patch

from app.scripts.seed_admin import _read_account_credentials


class SeedAdminCredentialsTests(unittest.TestCase):
    def test_reads_both_sys_admin_and_admin_accounts(self):
        with patch.dict(
            os.environ,
            {
                "SYS_ADMIN_EMAIL": "owner@example.com",
                "SYS_ADMIN_PASSWORD": "owner123",
                "ADMIN_EMAIL": "manager@example.com",
                "ADMIN_PASSWORD": "manager123",
            },
            clear=True,
        ):
            sys_credentials, admin_credentials = _read_account_credentials()

        self.assertEqual(sys_credentials, ("owner@example.com", "owner123"))
        self.assertEqual(admin_credentials, ("manager@example.com", "manager123"))

    def test_legacy_mode_uses_admin_as_sys_admin(self):
        with patch.dict(
            os.environ,
            {
                "ADMIN_EMAIL": "legacy@example.com",
                "ADMIN_PASSWORD": "legacy123",
            },
            clear=True,
        ):
            sys_credentials, admin_credentials = _read_account_credentials()

        self.assertEqual(sys_credentials, ("legacy@example.com", "legacy123"))
        self.assertIsNone(admin_credentials)

    def test_fails_on_partial_sys_admin_pair(self):
        with patch.dict(
            os.environ,
            {
                "SYS_ADMIN_EMAIL": "owner@example.com",
            },
            clear=True,
        ):
            with self.assertRaises(SystemExit):
                _read_account_credentials()

    def test_fails_when_sys_admin_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                _read_account_credentials()


if __name__ == "__main__":
    unittest.main()
