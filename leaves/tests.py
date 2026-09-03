import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import LeaveRequest

User = get_user_model()

# 2024-06-03 is a Monday.
MON = dt.date(2024, 6, 3)
TUE = dt.date(2024, 6, 4)
FRI = dt.date(2024, 6, 7)
SAT = dt.date(2024, 6, 8)
SUN = dt.date(2024, 6, 9)
NEXT_MON = dt.date(2024, 6, 10)
NEXT_TUE = dt.date(2024, 6, 11)
NEXT_WED = dt.date(2024, 6, 12)


class BusinessDaysTests(TestCase):
    def test_full_week(self):
        self.assertEqual(services.business_days(MON, FRI), 5)

    def test_weekend_only(self):
        self.assertEqual(services.business_days(SAT, SUN), 0)

    def test_span_across_weekend(self):
        self.assertEqual(services.business_days(MON, NEXT_MON), 6)


class LeaveRequestTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="EMP200",
            employee_id="EMP200",
            email="emp200@example.com",
            password="x",
        )
        self.hr = User.objects.create_user(
            username="HR200",
            employee_id="HR200",
            email="hr200@example.com",
            password="x",
            role=User.Role.HR,
        )

    def test_create_request_counts_business_days_only(self):
        req = services.create_request(self.employee, MON, NEXT_MON, "trip")
        self.assertEqual(req.days, 6)  # weekend not counted
        self.assertEqual(req.status, LeaveRequest.Status.PENDING)

    def test_inverted_range_rejected(self):
        with self.assertRaises(services.LeaveError):
            services.create_request(self.employee, FRI, MON)

    def test_weekend_only_request_rejected(self):
        with self.assertRaises(services.LeaveError):
            services.create_request(self.employee, SAT, SUN)

    def test_overlapping_request_rejected(self):
        services.create_request(self.employee, MON, FRI)
        with self.assertRaises(services.LeaveError):
            services.create_request(self.employee, FRI, NEXT_MON)

    def test_insufficient_balance_rejected(self):
        balance = services.get_balance(self.employee)
        balance.balance = Decimal("1")
        balance.save()
        with self.assertRaises(services.LeaveError):
            services.create_request(self.employee, MON, FRI)  # 5 days > 1

    def test_pending_requests_reserve_balance(self):
        balance = services.get_balance(self.employee)
        balance.balance = Decimal("3")
        balance.save()
        services.create_request(self.employee, MON, TUE)  # 2 days pending
        with self.assertRaises(services.LeaveError):
            services.create_request(self.employee, NEXT_MON, NEXT_TUE)  # 2 > remaining 1

    def test_approve_deducts_balance(self):
        req = services.create_request(self.employee, MON, TUE)  # 2 days
        services.approve(req, self.hr)
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.Status.APPROVED)
        self.assertEqual(req.reviewed_by, self.hr)
        self.assertIsNotNone(req.reviewed_at)
        self.assertEqual(services.get_balance(self.employee).balance, Decimal("22"))

    def test_reject_does_not_deduct(self):
        req = services.create_request(self.employee, MON, TUE)
        services.reject(req, self.hr)
        req.refresh_from_db()
        self.assertEqual(req.status, LeaveRequest.Status.REJECTED)
        self.assertEqual(services.get_balance(self.employee).balance, Decimal("24"))

    def test_reviewing_twice_rejected(self):
        req = services.create_request(self.employee, MON, TUE)
        services.approve(req, self.hr)
        with self.assertRaises(services.LeaveError):
            services.approve(req, self.hr)
        with self.assertRaises(services.LeaveError):
            services.reject(req, self.hr)

    def test_approved_leave_dates_exclude_weekends(self):
        req = services.create_request(self.employee, FRI, NEXT_MON)
        services.approve(req, self.hr)
        dates = services.approved_leave_dates(self.employee, MON, NEXT_WED)
        self.assertEqual(dates, {FRI, NEXT_MON})


class LeaveViewIntegrationTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="EMP500", employee_id="EMP500", email="emp500@example.com", password="x"
        )
        self.hr = User.objects.create_user(
            username="HR500", employee_id="HR500", email="hr500@example.com", password="x",
            role=User.Role.HR,
        )

    def test_employee_submits_leave_and_hr_approves_it(self):
        self.client.force_login(self.employee)
        response = self.client.post(
            reverse("my_leaves"), {"start_date": "2024-06-03", "end_date": "2024-06-04", "reason": "Trip"},
        )
        self.assertRedirects(response, reverse("my_leaves"))
        leave = LeaveRequest.objects.get(user=self.employee)
        self.client.force_login(self.hr)
        response = self.client.post(reverse("approve_leave", args=[leave.pk]))
        self.assertRedirects(response, reverse("hr_leaves"))
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveRequest.Status.APPROVED)

    def test_employee_cannot_review_leave(self):
        leave = services.create_request(self.employee, MON, TUE)
        self.client.force_login(self.employee)
        self.assertEqual(self.client.post(reverse("approve_leave", args=[leave.pk])).status_code, 403)
