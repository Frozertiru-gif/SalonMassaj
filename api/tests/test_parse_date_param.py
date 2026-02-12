import unittest
from datetime import date

from app.utils import parse_date_param


class ParseDateParamTests(unittest.TestCase):
    def test_parse_iso_date(self):
        self.assertEqual(parse_date_param("2026-02-14"), date(2026, 2, 14))

    def test_parse_dot_date(self):
        self.assertEqual(parse_date_param("14.02.2026"), date(2026, 2, 14))

    def test_parse_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "Invalid date format"):
            parse_date_param("02/14/2026")


if __name__ == "__main__":
    unittest.main()
