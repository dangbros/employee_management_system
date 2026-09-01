import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from leaves import services as leave_services

from . import services
from .models import Attendance

User = get_user_model()

# Fixed historical dates so tests are deterministic (2024-06-03 is a Monday).
MON = dt.date(2024, 6, 3)
TUE = dt.date(2024, 6, 4)
WED = dt.date(2024, 6, 5)
THU = dt.date(2024, 6, 6)
FRI = dt.date(2024, 6, 7)
SAT = dt.date(2024, 6, 8)
SUN = dt.date(2024, 6, 9)
LATER = dt.date(2024, 6, 10)


def aware(day, hour, minute=0):
    return timezone.make_aware(
        dt.datetime.combine(day, dt.time(hour, minute)),
        timezone.get_default_timezone(),
    )


def make_record(user, day, in_hour=None, in_minute=0, out_hour=None, out_minute=0):
    return Attendance.objects.create(
        user=user,
        date=day,
        check_in=aware(day, in_hour, in_minute) if in_hour is not None else None,
        check_out=aware(day, out_hour, out_minute) if out_hour is not None else None,
    )


class WorkingHoursTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="EMP100",
            employee_id="EMP100",
            email="emp100@example.com",
            password="x",
        )

    def test_full_day_hours(self):
        record = make_record(self.user, MON, in_hour=9, out_hour=17, out_minute=30)
        self.assertEqual(record.worked_hours, 8.5)

    def test_hours_none_when_check_out_missing(self):
        record = make_record(self.user, MON, in_hour=9)
        self.assertIsNone(record.worked_hours)
        self.assertIsNone(services.worked_hours(None))

    def test_week_and_month_bounds(self):
        self.assertEqual(services.week_bounds(WED), (MON, SUN))
        start, end = services.month_bounds(dt.date(2024, 6, 15))
        self.assertEqual(start, dt.date(2024, 6, 1))
        self.assertEqual(end, dt.date(2024, 6, 30))


class CheckInOutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="EMP102",
            employee_id="EMP102",
            email="emp102@example.com",
            password="x",
        )

    def test_check_in_creates_todays_record(self):
        record = services.check_in(self.user)
        self.assertEqual(record.date, services.local_date())
        self.assertIsNotNone(record.check_in)

    def test_duplicate_check_in_rejected(self):
        services.check_in(self.user)
        with self.assertRaises(services.AttendanceError):
            services.check_in(self.user)
        self.assertEqual(Attendance.objects.filter(user=self.user).count(), 1)

    def test_check_out_without_check_in_rejected(self):
        with self.assertRaises(services.AttendanceError):
            services.check_out(self.user)

    def test_check_out_flow_and_double_check_out(self):
        services.check_in(self.user)
        record = services.check_out(self.user)
        self.assertIsNotNone(record.check_out)
        with self.assertRaises(services.AttendanceError):
            services.check_out(self.user)


class DayStatusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="EMP103",
            employee_id="EMP103",
            email="emp103@example.com",
            password="x",
        )

    def test_present(self):
        record = make_record(self.user, MON, in_hour=9, out_hour=17, out_minute=30)
        self.assertEqual(services.day_status(MON, record, today=LATER), services.PRESENT)

    def test_half_day_below_threshold(self):
        record = make_record(self.user, MON, in_hour=9, out_hour=12, out_minute=30)
        self.assertEqual(services.day_status(MON, record, today=LATER), services.HALF_DAY)

    def test_exactly_threshold_counts_as_present(self):
        record = make_record(self.user, MON, in_hour=9, out_hour=13)
        self.assertEqual(services.day_status(MON, record, today=LATER), services.PRESENT)

    def test_missed_check_out_is_incomplete_not_zero_hours(self):
        record = make_record(self.user, MON, in_hour=9)
        self.assertEqual(
            services.day_status(MON, record, today=LATER), services.INCOMPLETE
        )
        self.assertIsNone(record.worked_hours)

    def test_checked_in_today_is_working(self):
        record = make_record(self.user, MON, in_hour=9)
        self.assertEqual(services.day_status(MON, record, today=MON), services.WORKING)

    def test_no_check_in_today_is_not_marked(self):
        self.assertEqual(services.day_status(MON, None, today=MON), services.NOT_MARKED)

    def test_no_check_in_past_weekday_is_absent(self):
        self.assertEqual(services.day_status(MON, None, today=LATER), services.ABSENT)

    def test_weekend(self):
        self.assertEqual(services.day_status(SAT, None, today=LATER), services.WEEKEND)

    def test_approved_leave(self):
        self.assertEqual(
            services.day_status(THU, None, on_leave=True, today=LATER),
            services.ON_LEAVE,
        )


class SummaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="EMP101",
            employee_id="EMP101",
            email="emp101@example.com",
            password="x",
        )
        cls.hr = User.objects.create_user(
            username="HR100",
            employee_id="HR100",
            email="hr100@example.com",
            password="x",
            role=User.Role.HR,
        )
        make_record(cls.user, MON, in_hour=9, out_hour=17)  # present, 8h
        make_record(cls.user, TUE, in_hour=9, out_hour=12)  # half-day, 3h
        make_record(cls.user, WED, in_hour=9)  # incomplete
        # THU: absent (no record, no leave filed)
        leave = leave_services.create_request(cls.user, FRI, FRI, "PTO")
        leave_services.approve(leave, cls.hr)  # FRI: approved leave

    def test_summary_counts_and_hours(self):
        summary = services.summarize(self.user, MON, SUN, today=LATER)
        self.assertEqual(summary["total_hours"], 11.0)
        self.assertEqual(summary["present"], 1)
        self.assertEqual(summary["half_days"], 1)
        self.assertEqual(summary["incomplete"], 1)
        self.assertEqual(summary["absent"], 1)
        self.assertEqual(summary["on_leave"], 1)

    def test_unapproved_absence_distinct_from_approved_leave(self):
        days = {
            d["date"]: d["status"]
            for d in services.status_history(self.user, MON, SUN, today=LATER)
        }
        self.assertEqual(days[THU], services.ABSENT)
        self.assertEqual(days[FRI], services.ON_LEAVE)

    def test_history_never_reports_future_days(self):
        days = services.status_history(self.user, MON, SUN, today=WED)
        self.assertEqual(len(days), 3)
