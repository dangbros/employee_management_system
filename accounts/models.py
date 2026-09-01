from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Company user. Extends Django's built-in user rather than replacing it.

    ``username`` mirrors ``employee_id`` and is what employees log in with.
    ``role`` drives dashboard access and is never client-assignable during
    registration (all self-registered users are employees; HR accounts are
    created via the seed command or Django admin).
    """

    class Role(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        HR = "hr", "HR"

    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.EMPLOYEE
    )
    department = models.CharField(max_length=50, blank=True)

    @property
    def is_hr(self):
        return self.role == self.Role.HR or self.is_superuser

    def __str__(self):
        full_name = self.get_full_name()
        return f"{self.employee_id} - {full_name}" if full_name else self.employee_id
