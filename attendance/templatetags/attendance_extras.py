from django import template
from django.utils.html import format_html

register = template.Library()

BADGES = {
    # Attendance day statuses
    "present": ("Present", "success"),
    "half_day": ("Half-day", "info"),
    "working": ("Working", "primary"),
    "incomplete": ("Incomplete", "dark"),
    "on_leave": ("On leave", "warning text-dark"),
    "absent": ("Absent", "danger"),
    "weekend": ("Weekend", "light text-muted border"),
    "not_marked": ("Not checked in", "secondary"),
    # Leave request statuses
    "pending": ("Pending", "warning text-dark"),
    "approved": ("Approved", "success"),
    "rejected": ("Rejected", "danger"),
}


@register.filter
def status_badge(status):
    """Render a status string as a color-coded Bootstrap badge."""
    label, css = BADGES.get(status, (status, "secondary"))
    return format_html('<span class="badge bg-{}">{}</span>', css, label)
