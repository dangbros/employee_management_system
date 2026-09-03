from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import BootstrapPasswordChangeForm, ProfileForm, RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    """Role-based landing page."""
    if request.user.is_hr:
        return redirect("hr_dashboard")
    return redirect("employee_dashboard")


@login_required
def profile(request):
    """Show the employee-editable account details and password form."""
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": ProfileForm(instance=request.user),
            "password_form": BootstrapPasswordChangeForm(user=request.user),
        },
    )


@login_required
@require_POST
def update_profile(request):
    form = ProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Your profile details have been updated.")
        return redirect("profile")
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": form,
            "password_form": BootstrapPasswordChangeForm(user=request.user),
        },
    )


@login_required
@require_POST
def change_password(request):
    form = BootstrapPasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password has been changed.")
        return redirect("profile")
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": ProfileForm(instance=request.user),
            "password_form": form,
        },
    )
