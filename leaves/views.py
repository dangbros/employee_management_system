from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import hr_required

from . import services
from .forms import LeaveRequestForm
from .models import LeaveRequest


@login_required
def my_leaves(request):
    """Personal leave balance, request form and request history."""
    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            try:
                leave = services.create_request(
                    request.user,
                    form.cleaned_data["start_date"],
                    form.cleaned_data["end_date"],
                    form.cleaned_data["reason"],
                )
                messages.success(
                    request,
                    f"Leave request submitted for {form.cleaned_data['start_date']:%d %b} "
                    f"to {form.cleaned_data['end_date']:%d %b %Y} ({leave.days} working day(s)).",
                )
                return redirect("my_leaves")
            except services.LeaveError as exc:
                messages.error(request, str(exc))
    else:
        form = LeaveRequestForm()
    return render(
        request,
        "leaves/my_leaves.html",
        {
            "form": form,
            "balance": services.get_balance(request.user),
            "leave_requests": request.user.leave_requests.select_related("reviewed_by"),
        },
    )


@hr_required
def hr_leaves(request):
    history_qs = LeaveRequest.objects.exclude(
        status=LeaveRequest.Status.PENDING
    ).select_related("user", "reviewed_by")
    paginator = Paginator(history_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "leaves/hr_leaves.html",
        {
            "pending": LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING)
            .select_related("user")
            .order_by("start_date"),
            "history": page_obj.object_list,
            "page_obj": page_obj,
        },
    )


@hr_required
@require_POST
def approve_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    try:
        leave = services.approve(leave, request.user)
        messages.success(
            request,
            f"Approved {leave.days} working day(s) for {leave.user} "
            f"({leave.start_date:%d %b} to {leave.end_date:%d %b %Y}).",
        )
    except services.LeaveError as exc:
        messages.error(request, str(exc))
    return redirect("hr_leaves")


@hr_required
@require_POST
def reject_leave(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    try:
        leave = services.reject(leave, request.user)
        messages.success(
            request,
            f"Rejected leave for {leave.user} ({leave.start_date:%d %b} to {leave.end_date:%d %b %Y}).",
        )
    except services.LeaveError as exc:
        messages.error(request, str(exc))
    return redirect("hr_leaves")
