from django.conf import settings
from django.db import models


class Attendance(models.Model):
    """One row per employee per local calendar day.

    Timestamps are always captured server-side. A missing ``check_out`` on a
    past day marks the day as Incomplete (distinct from a zero-hour day).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "attendance records"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"], name="unique_attendance_per_user_day"
            ),
            models.CheckConstraint(
                condition=models.Q(check_out__isnull=True)
                | (
                    models.Q(check_in__isnull=False)
                    & models.Q(check_out__gt=models.F("check_in"))
                ),
                name="check_out_after_check_in",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "date"], name="attendance_user_date_idx"),
            models.Index(fields=["date"], name="attendance_date_idx"),
        ]

    @property
    def worked_hours(self):
        """Hours between check-in and check-out, or None while incomplete."""
        if self.check_in and self.check_out:
            return round((self.check_out - self.check_in).total_seconds() / 3600, 2)
        return None

    def __str__(self):
        return f"{self.user_id} @ {self.date}"
