"""Leave business logic.

Policy (documented in README): every employee receives a fixed annual
allotment of ``settings.ANNUAL_LEAVE_DAYS`` paid leave days. Only business
days (Mon-Fri) count against the balance. The balance is deducted at
approval time; pending requests provisionally reserve balance so an
employee cannot over-book. Retroactive requests are allowed so unplanned
absences can be regularised after the fact.
"""
import datetime as dt
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest


class LeaveError(Exception):
    """Raised for invalid leave operations; message is user-facing."""


def get_balance(user):
    balance, _ = LeaveBalance.objects.get_or_create(
        user=user, defaults={"balance": settings.ANNUAL_LEAVE_DAYS}
    )
    return balance


def business_days(start, end):
    """Count Mon-Fri days in the inclusive range [start, end]."""
    count = 0
    day = start
    while day <= end:
        if day.weekday() < 5:
            count += 1
        day += dt.timedelta(days=1)
    return count


def create_request(user, start_date, end_date, reason=""):
    """Validate and create a pending leave request.

    Rejects inverted ranges, weekend-only ranges, overlaps with existing
    pending/approved requests, and requests exceeding the available balance
    (taking already-pending requests into account).
    """
    if start_date > end_date:
        raise LeaveError("Start date must be on or before the end date.")
    days = business_days(start_date, end_date)
    if days == 0:
        raise LeaveError("The selected range contains no working days.")
    overlap = LeaveRequest.objects.filter(
        user=user,
        status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).exists()
    if overlap:
        raise LeaveError("This request overlaps an existing pending or approved leave.")
    balance = get_balance(user)
    pending = LeaveRequest.objects.filter(
        user=user, status=LeaveRequest.Status.PENDING
    ).aggregate(total=Sum("days"))["total"] or Decimal("0")
    if Decimal(days) + pending > balance.balance:
        raise LeaveError(
            f"Insufficient leave balance: {days} day(s) requested, "
            f"{balance.balance} available with {pending} already pending."
        )
    return LeaveRequest.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        days=days,
    )


@transaction.atomic
def approve(leave_request, reviewer):
    """Approve a pending request and deduct the balance atomically."""
    leave_request = LeaveRequest.objects.select_for_update().get(pk=leave_request.pk)
    if leave_request.status != LeaveRequest.Status.PENDING:
        raise LeaveError("Only pending requests can be reviewed.")
    get_balance(leave_request.user)  # ensure the balance row exists
    balance = LeaveBalance.objects.select_for_update().get(user=leave_request.user)
    if balance.balance < leave_request.days:
        raise LeaveError("The employee does not have enough leave balance.")
    balance.balance -= leave_request.days
    balance.save(update_fields=["balance", "updated_at"])
    leave_request.status = LeaveRequest.Status.APPROVED
    leave_request.reviewed_by = reviewer
    leave_request.reviewed_at = timezone.now()
    leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return leave_request


@transaction.atomic
def reject(leave_request, reviewer):
    """Reject a pending request without touching the balance."""
    leave_request = LeaveRequest.objects.select_for_update().get(pk=leave_request.pk)
    if leave_request.status != LeaveRequest.Status.PENDING:
        raise LeaveError("Only pending requests can be reviewed.")
    leave_request.status = LeaveRequest.Status.REJECTED
    leave_request.reviewed_by = reviewer
    leave_request.reviewed_at = timezone.now()
    leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    return leave_request


def approved_leave_dates(user, start, end):
    """Set of business dates in [start, end] covered by approved leave."""
    dates = set()
    requests = LeaveRequest.objects.filter(
        user=user,
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=end,
        end_date__gte=start,
    )
    for leave in requests:
        day = max(start, leave.start_date)
        stop = min(end, leave.end_date)
        while day <= stop:
            if day.weekday() < 5:
                dates.add(day)
            day += dt.timedelta(days=1)
    return dates
