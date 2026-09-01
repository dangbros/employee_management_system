from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "role",
        "department",
        "is_active",
    )
    list_filter = ("role", "department", "is_active")
    search_fields = ("employee_id", "username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Company", {"fields": ("employee_id", "role", "department")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Company", {"fields": ("employee_id", "role", "department")}),
    )
