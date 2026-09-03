"""PDF rendering for HR attendance reports."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from django.utils import timezone


STATUS_LABELS = {
    "present": "Present",
    "half_day": "Half-day",
    "working": "Working",
    "incomplete": "Incomplete",
    "on_leave": "On leave",
    "absent": "Absent",
    "weekend": "Weekend",
    "not_marked": "Not checked in",
}


def monthly_employee_report(employee, balance, summary, month_label):
    """Return a polished, in-memory PDF for one employee's month."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.textColor = colors.HexColor("#13253F")
    heading = styles["Heading2"]
    heading.textColor = colors.HexColor("#0F766E")
    body = styles["BodyText"]
    body.textColor = colors.HexColor("#405067")

    name = employee.get_full_name() or employee.username
    story = [
        Paragraph("Inner Eye Attendance", title),
        Paragraph(f"Monthly attendance report - {month_label}", body),
        Spacer(1, 7 * mm),
        Paragraph("Employee details", heading),
        Table(
            [
                ["Employee", name, "Employee ID", employee.employee_id],
                ["Department", employee.department or "Not assigned", "Leave balance", f"{balance.balance} days"],
            ],
            colWidths=[28 * mm, 58 * mm, 30 * mm, 54 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF8F6")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#ECF8F6")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#17263C")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E2E9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 7 * mm),
        Paragraph("Monthly summary", heading),
        Table(
            [["Hours", "Present", "Half-days", "On leave", "Absent", "Incomplete"], [
                str(summary["total_hours"]), str(summary["present"]), str(summary["half_days"]),
                str(summary["on_leave"]), str(summary["absent"]), str(summary["incomplete"]),
            ]],
            colWidths=[28 * mm] * 6,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#13253F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F5F7FA")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E2E9")),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 7 * mm),
        Paragraph("Daily attendance", heading),
    ]

    daily_rows = [["Date", "Status", "Check-in", "Check-out", "Hours"]]
    for day in summary["days"]:
        record = day["record"]
        daily_rows.append([
            day["date"].strftime("%d %b %Y"),
            STATUS_LABELS.get(day["status"], day["status"]),
            timezone.localtime(record.check_in).strftime("%H:%M") if record and record.check_in else "-",
            timezone.localtime(record.check_out).strftime("%H:%M") if record and record.check_out else "-",
            str(day["hours"]) if day["hours"] is not None else "-",
        ])
    story.append(
        Table(
            daily_rows,
            repeatRows=1,
            colWidths=[37 * mm, 40 * mm, 30 * mm, 30 * mm, 24 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#13253F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D8E2E9")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )
    document.build(story)
    return buffer.getvalue()
