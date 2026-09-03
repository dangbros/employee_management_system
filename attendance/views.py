import csv
import datetime as dt
from collections import Counter

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import hr_required
from leaves import services as leave_services
from leaves.models import LeaveBalance, LeaveRequest

from . import services
from .models import Attendance
from .reports import monthly_employee_report


def _parse_date(value, default):
    """Safely parse a client-supplied ISO date; fall back to a default."""
    if not value:
        return default
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return default


@login_required
def employee_dashboard(request):
    user = request.user
    today = services.local_date()
    record = Attendance.objects.filter(user=user, date=today).first()
    on_leave_today = today in leave_services.approved_leave_dates(user, today, today)
    return render(
        request,
        "attendance/employee_dashboard.html",
        {
            "today": today,
            "record": record,
            "status": services.day_status(today, record, on_leave_today, today=today),
            "week": services.summarize(user, *services.week_bounds(today)),
            "month": services.summarize(user, *services.month_bounds(today)),
            "balance": leave_services.get_balance(user),
            "recent": list(
                reversed(
                    services.status_history(user, today - dt.timedelta(days=6), today)
                )
            ),
            "can_check_in": record is None or record.check_in is None,
            "can_check_out": bool(record and record.check_in and not record.check_out),
        },
    )


@login_required
@require_POST
def check_in_view(request):
    try:
        record = services.check_in(request.user)
        messages.success(
            request, f"Checked in at {timezone.localtime(record.check_in):%H:%M}."
        )
    except services.AttendanceError as exc:
        messages.error(request, str(exc))
    return redirect("employee_dashboard")


@login_required
@require_POST
def check_out_view(request):
    try:
        record = services.check_out(request.user)
        messages.success(
            request,
            f"Checked out at {timezone.localtime(record.check_out):%H:%M}. "
            f"You worked {record.worked_hours} hours today.",
        )
    except services.AttendanceError as exc:
        messages.error(request, str(exc))
    return redirect("employee_dashboard")


@login_required
def history(request):
    """Personal month-by-month attendance history (own data only)."""
    today = services.local_date()
    ref = today
    month_str = request.GET.get("month", "").strip()
    if month_str:
        try:
            ref = dt.date.fromisoformat(month_str + "-01")
        except ValueError:
            messages.error(request, "Invalid month; showing the current month.")
    start, end = services.month_bounds(ref)
    summary = services.summarize(request.user, start, end)
    return render(
        request,
        "attendance/history.html",
        {
            "summary": summary,
            "days": list(reversed(summary["days"])),
            "month_value": start.strftime("%Y-%m"),
        },
    )


@hr_required
def hr_dashboard(request):
    User = get_user_model()
    today = services.local_date()
    day = _parse_date(request.GET.get("date"), today)
    if day > today:
        day = today
    q = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()

    employees = User.objects.filter(is_active=True).order_by("employee_id")
    if q:
        employees = employees.filter(
            Q(employee_id__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    if department:
        employees = employees.filter(department=department)

    paginator = Paginator(employees, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    employees = list(page_obj.object_list)

    records = {
        a.user_id: a for a in Attendance.objects.filter(date=day, user__in=employees)
    }
    on_leave_ids = set(
        LeaveRequest.objects.filter(
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=day,
            end_date__gte=day,
            user__in=employees,
        ).values_list("user_id", flat=True)
    )
    balances = {
        b.user_id: b.balance for b in LeaveBalance.objects.filter(user__in=employees)
    }

    rows = []
    for emp in employees:
        record = records.get(emp.id)
        rows.append(
            {
                "employee": emp,
                "record": record,
                "status": services.day_status(
                    day, record, emp.id in on_leave_ids, today=today
                ),
                "hours": services.worked_hours(record),
                "balance": balances.get(emp.id, settings.ANNUAL_LEAVE_DAYS),
            }
        )

    departments = (
        User.objects.exclude(department="")
        .values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )
    all_employees = list(User.objects.filter(is_active=True).order_by("employee_id"))
    team_records = {
        record.user_id: record
        for record in Attendance.objects.filter(date=day, user__in=all_employees)
    }
    team_on_leave_ids = set(
        LeaveRequest.objects.filter(
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=day,
            end_date__gte=day,
            user__in=all_employees,
        ).values_list("user_id", flat=True)
    )
    team_statuses = Counter(
        services.day_status(
            day, team_records.get(employee.id), employee.id in team_on_leave_ids, today=today
        )
        for employee in all_employees
    )
    pending_count = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()
    return render(
        request,
        "attendance/hr_dashboard.html",
        {
            "rows": rows,
            "day": day,
            "today": today,
            "q": q,
            "department": department,
            "departments": departments,
            "page_obj": page_obj,
            "pending_count": pending_count,
            "team_summary": {
                "present": team_statuses[services.PRESENT],
                "absent": team_statuses[services.ABSENT],
                "on_leave": team_statuses[services.ON_LEAVE],
                "incomplete": team_statuses[services.INCOMPLETE],
                "pending": pending_count,
            },
        },
    )


@hr_required
def hr_employee_detail(request, user_id):
    """Working-hour trends and history for one employee (HR only)."""
    User = get_user_model()
    employee = get_object_or_404(User, pk=user_id)
    today = services.local_date()
    start = _parse_date(request.GET.get("start"), today - dt.timedelta(days=29))
    end = _parse_date(request.GET.get("end"), today)
    if start > end:
        start, end = end, start
    summary = services.summarize(employee, start, end)
    return render(
        request,
        "attendance/hr_employee_detail.html",
        {
            "employee": employee,
            "summary": summary,
            "days": list(reversed(summary["days"])),
            "start": start,
            "end": end,
            "balance": leave_services.get_balance(employee),
            "recent_leaves": employee.leave_requests.select_related("reviewed_by")[:10],
        },
    )


@hr_required
def hr_export_csv(request):
    """Download one month of attendance for all active employees as CSV.

    Uses the same status-computation service as the dashboards, so the
    export can never disagree with what HR sees on screen.
    """
    User = get_user_model()
    today = services.local_date()
    ref = today
    month_str = request.GET.get("month", "").strip()
    if month_str:
        try:
            ref = dt.date.fromisoformat(month_str + "-01")
        except ValueError:
            ref = today
    start, end = services.month_bounds(ref)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance-{start:%Y-%m}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        ["Employee ID", "Name", "Date", "Check-in", "Check-out", "Hours", "Status"]
    )
    for emp in User.objects.filter(is_active=True).order_by("employee_id"):
        for day in services.status_history(emp, start, end):
            record = day["record"]
            writer.writerow(
                [
                    emp.employee_id,
                    emp.get_full_name(),
                    day["date"].isoformat(),
                    timezone.localtime(record.check_in).strftime("%H:%M")
                    if record and record.check_in
                    else "",
                    timezone.localtime(record.check_out).strftime("%H:%M")
                    if record and record.check_out
                    else "",
                    day["hours"] if day["hours"] is not None else "",
                    day["status"],
                ]
            )
    return response


@hr_required
def hr_employee_report(request, user_id):
    """Download a one-month, one-employee attendance PDF for HR."""
    User = get_user_model()
    employee = get_object_or_404(User, pk=user_id)
    today = services.local_date()
    ref = today
    month_str = request.GET.get("month", "").strip()
    if month_str:
        try:
            ref = dt.date.fromisoformat(month_str + "-01")
        except ValueError:
            ref = today
    start, end = services.month_bounds(ref)
    summary = services.summarize(employee, start, end)
    pdf = monthly_employee_report(
        employee, leave_services.get_balance(employee), summary, start.strftime("%B %Y")
    )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance-{employee.employee_id}-{start:%Y-%m}.pdf"'
    )
    return response
