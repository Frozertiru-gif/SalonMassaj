import unittest
from unittest.mock import AsyncMock, patch

from app.api.admin import _slot_step_min
from app.utils import DEFAULT_SLOT_STEP_MIN


class AdminSlotStepMinTests(unittest.IsolatedAsyncioTestCase):
    async def test_reads_value_from_settings_helper(self):
        with patch("app.api.admin.get_setting_value", new=AsyncMock(return_value={"value": "15"})):
            result = await _slot_step_min(db=object())

        self.assertEqual(result, 15)

    async def test_falls_back_to_default_for_invalid_value(self):
        with patch("app.api.admin.get_setting_value", new=AsyncMock(return_value={"value": "abc"})):
            result = await _slot_step_min(db=object())

        self.assertEqual(result, DEFAULT_SLOT_STEP_MIN)


if __name__ == "__main__":
    unittest.main()
