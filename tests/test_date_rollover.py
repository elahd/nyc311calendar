"""Regression coverage for dates advancing without a Python restart."""
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo
import unittest

from nyc311calendar import NYC311API
from nyc311calendar.services import ServiceType
from nyc311calendar import util


class DateRolloverTests(unittest.TestCase):
    def test_default_date_advances_after_midnight(self):
        for current in (date(2026, 11, 10), date(2026, 11, 11)):
            with self.subTest(current=current), patch.object(util, "today", return_value=current):
                self.assertEqual(util.date_mod(0), current)
                self.assertEqual(util.date_mod(2), date.fromordinal(current.toordinal() + 2))

    def test_explicit_date_remains_independent_of_clock(self):
        with patch.object(util, "today", return_value=date(2026, 11, 11)):
            self.assertEqual(util.date_mod(1, date(2026, 12, 31)), date(2027, 1, 1))

    def test_week_ahead_reindexes_existing_calendar_after_rollover(self):
        days = {date(2026, 11, day): {service: (day, service) for service in ServiceType}
                for day in range(9, 19)}
        for day in (10, 11):
            with self.subTest(day=day), patch.object(util, "today", return_value=date(2026, 11, day)):
                result = NYC311API._NYC311API__build_days_ahead(days)
                self.assertEqual(result[0]["date"], date(2026, 11, day))
                self.assertEqual(result[2]["date"], date(2026, 11, day + 2))
                self.assertEqual(result[0]["services"][ServiceType.PARKING], (day, ServiceType.PARKING))

    def test_today_uses_new_york_before_utc_midnight_rollover(self):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 11, 11, 2, tzinfo=ZoneInfo("UTC")).astimezone(tz)
        with patch.object(util, "datetime", Clock):
            self.assertEqual(util.today(), date(2026, 11, 10))
