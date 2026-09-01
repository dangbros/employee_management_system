"""Seed demo data so the app is immediately demoable.

Creates one HR user, four employees across departments, three weeks of
attendance history (including a half-day, an incomplete day and an
unapproved absence), one approved leave and one pending leave request.
Idempotent: refuses to run twice.
"""
import datetime as dt
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import Attendance
from leaves import services as leave_services

PASSWORD = "DemoPass123!"

EMPLOYEES = [
    ("EMP001", "Asha", "Verma", "Engineering"),
    ("EMP002", "Rahul", "Nair", "Engineering"),
    ("EMP003", "Meera", "Iyer", "Finance"),
    ("EMP004", "Dev", "Patel", "Sales"),
]


class Command(BaseCommand):
    help = "Seed demo users, three weeks of attendance history and sample leave data."

    def aware(self, day, hour, minute):
        return timezone.make_aware(
            dt.datetime.combine(day, dt.time(hour, minute)),
            timezone.get_default_timezone(),
        )

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(employee_id="HR001").exists():
            self.stdout.write(self.style.WARNING("Demo data already seeded; nothing to do."))
            return

        hr = User.objects.create_user(
            username="HR001",
            employee_id="HR001",
            email="hr@innereye.example",
            password=PASSWORD,
            first_name="Harini",
            last_name="Rao",
            department="People Ops",
            role=User.Role.HR,
            is_staff=True,
        )
        employees = [
            User.objects.create_user(
                username=eid,
                employee_id=eid,
                email=f"{eid.lower()}@innereye.example",
                password=PASSWORD,
                first_name=first,
                last_name=last,
                department=dept,
            )
            for eid, first, last, dept in EMPLOYEES
        ]

        today = timezone.localtime().date()

        # Approved two-day leave for EMP001 about a week ago (Mon-Thu start so
        # both days are business days).
        leave_start = today - dt.timedelta(days=9)
        while leave_start.weekday() >= 4:
            leave_start -= dt.timedelta(days=1)
        leave_end = leave_start + dt.timedelta(days=1)
        approved = leave_services.create_request(
            employees[0], leave_start, leave_end, "Family function"
        )
        leave_services.approve(approved, hr)
        leave_dates = {leave_start, leave_end}

        for emp in employees:
            rng = random.Random(emp.employee_id)  # deterministic per employee
            absent_offset = rng.randrange(3, 15)
            incomplete_offset = rng.randrange(3, 15)
            for offset in range(20, -1, -1):
                day = today - dt.timedelta(days=offset)
                if day.weekday() >= 5:
                    continue  # weekends are not working days
                if emp is employees[0] and day in leave_dates:
                    continue  # on approved leave
                if offset == absent_offset:
                    continue  # unapproved absence (no check-in, no leave)
                record = Attendance.objects.create(
                    user=emp, date=day, check_in=self.aware(day, 9, rng.randrange(0, 40))
                )
                if offset == 0:
                    continue  # today: checked in, still working
                if emp.employee_id == "EMP003" and offset == incomplete_offset:
                    continue  # missed check-out -> incomplete day
                if emp.employee_id == "EMP002" and offset == 7:
                    record.check_out = self.aware(day, 13, 0)  # half-day
                else:
                    record.check_out = self.aware(day, 17, 30 + rng.randrange(0, 25))
                record.save(update_fields=["check_out"])

        # Pending leave for EMP004 starting next Monday.
        next_monday = today + dt.timedelta(days=(7 - today.weekday()) or 7)
        leave_services.create_request(
            employees[3], next_monday, next_monday + dt.timedelta(days=2), "Travel"
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))
        self.stdout.write(f"  HR login:        HR001 / {PASSWORD}")
        self.stdout.write(f"  Employee logins: EMP001, EMP002, EMP003, EMP004 / {PASSWORD}")
