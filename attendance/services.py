"""Attendance business logic: check-in/out, working hours, day status.

This module is the single source of truth for status computation so the
logic is not scattered across views or templates. All \"days\" are calendar
days in the project's local timezone (settings.TIME_ZONE); storage is UTC.
"""
import calendar
import datetime as dt
from collections import Counter

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from leaves import services as leave_services

from .models import Attendance

# Day status values
PRESENT = "present"
HALF_DAY = "half_day"
INCOMPLETE = "incomplete"   # past day: checked in but never checked out
WORKING = "working"         # today: checked in, not yet checked out
ON_LEAVE = "on_leave"
ABSENT = "absent"           # past weekday: no check-in and no approved leave
WEEKEND = "weekend"
NOT_MARKED = "not_marked"   # today: not checked in yet


class AttendanceError(Exception):
    """Raised for invalid attendance operations; message is user-facing."""


def local_date(moment=None):
    return timezone.localtime(moment or timezone.now()).date()


def check_in(user):
    """Create today's record with a server-side timestamp.

    Exactly one check-in per day is allowed; enforced here and by the
    unique(user, date) database constraint.
    """
    today = local_date()
    with transaction.atomic():
        record, _ = Attendance.objects.get_or_create(user=user, date=today)
        if record.check_in:
            raise AttendanceError("You have already checked in today.")
        record.check_in = timezone.now()
        record.save(update_fields=["check_in"])
    return record


def check_out(user):
    """Close today's record; rejects check-out without/before check-in."""
    today = local_date()
    record = Attendance.objects.filter(user=user, date=today).first()
    if record is None or record.check_in is None:
        raise AttendanceError("You cannot check out before checking in.")
    if record.check_out:
        raise AttendanceError("You have already checked out today.")
    record.check_out = timezone.now()
    record.save(update_fields=["check_out"])
    return record


def worked_hours(record):
    return record.worked_hours if record else None


def day_status(date, record, on_leave=False, today=None):
    """Derive the status of a single day for one employee.

    Precedence: an actual check-in wins over everything (working on an
    approved leave day counts as present), then approved leave, then
    weekend, then absent/not-marked.
    """
    today = today or local_date()
    if record and record.check_in:
        if record.check_out:
            hours = record.worked_hours
            if hours >= settings.HALF_DAY_THRESHOLD_HOURS:
                return PRESENT
            return HALF_DAY
        return WORKING if date == today else INCOMPLETE
    if on_leave:
        return ON_LEAVE
    if date.weekday() >= 5:
        return WEEKEND
    return NOT_MARKED if date == today else ABSENT


def status_history(user, start, end, today=None):
    """Per-day status dicts for [start, end], clamped so future days are
    never reported (a future weekday is not \"absent\")."""
    today = today or local_date()
    end = min(end, today)
    days = []
    if start > end:
        return days
    records = {
        r.date: r
        for r in Attendance.objects.filter(user=user, date__range=(start, end))
    }
    leave_dates = leave_services.approved_leave_dates(user, start, end)
    day = start
    while day <= end:
        record = records.get(day)
        days.append(
            {
                "date": day,
                "record": record,
                "status": day_status(day, record, day in leave_dates, today=today),
                "hours": record.worked_hours if record else None,
            }
        )
        day += dt.timedelta(days=1)
    return days


def summarize(user, start, end, today=None):
    """Aggregate a date range into totals used by dashboards."""
    days = status_history(user, start, end, today=today)
    counts = Counter(day["status"] for day in days)
    total_hours = round(sum(day["hours"] or 0 for day in days), 2)
    return {
        "start": start,
        "end": end,
        "days": days,
        "total_hours": total_hours,
        "present": counts[PRESENT],
        "half_days": counts[HALF_DAY],
        "on_leave": counts[ON_LEAVE],
        "absent": counts[ABSENT],
        "incomplete": counts[INCOMPLETE],
    }


def week_bounds(ref):
    monday = ref - dt.timedelta(days=ref.weekday())
    return monday, monday + dt.timedelta(days=6)


def month_bounds(ref):
    first = ref.replace(day=1)
    last = ref.replace(day=calendar.monthrange(ref.year, ref.month)[1])
    return first, last
