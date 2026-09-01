from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "check_in", "check_out", "worked_hours")
    list_filter = ("date",)
    search_fields = ("user__employee_id", "user__first_name", "user__last_name")
    date_hierarchy = "date"
