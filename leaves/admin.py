from django.contrib import admin

from .models import LeaveBalance, LeaveRequest


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__employee_id", "user__first_name", "user__last_name")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "start_date", "end_date", "days", "status", "reviewed_by")
    list_filter = ("status",)
    search_fields = ("user__employee_id", "user__first_name", "user__last_name")
    date_hierarchy = "start_date"
