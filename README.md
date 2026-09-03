# Employee Attendance Management System

A Django-based web application for tracking employee attendance, working hours, and leave — built as a developer assignment for **Inner Eye Consultancy Services LLP**.

## Overview

The system supports two roles — **Employee** and **HR** — with server-side enforced access control between them.

- Employees check in/out, view their own attendance history and working-hours summary, and submit leave requests.
- HR views all employees' attendance and leave status, approves or rejects leave requests, and monitors working-hour trends.

Attendance status (Present / Absent / On Leave / Half-day / Incomplete) is computed from check-in/check-out records and approved leave — not stored as a raw flag — so it stays consistent even as records change.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 |
| Database | SQLite (dev) — schema is FK/constraint-clean and portable to PostgreSQL |
| Frontend | Django templates + Bootstrap 5 |
| Auth | Django's built-in auth system, extended with a role field |

**Why this stack:** Django's ORM, migrations, and auth system cover most of the assignment's requirements (user management, password hashing, session security) out of the box, which keeps the codebase focused on the actual business logic — attendance and leave calculation — rather than re-implementing infrastructure. Server-rendered templates were chosen over a separate frontend because the app's screens are form- and table-driven rather than highly interactive, so a SPA would add complexity without a corresponding UX benefit.

## Project Structure

```
employee-attendance-management/
├── accounts/       # User model, roles, registration & login
├── attendance/     # Check-in/check-out, working-hours calculation, status tracking
├── leaves/         # Leave balance, leave requests, HR approval workflow
├── config/         # Django project settings, root URLconf
├── templates/      # HTML templates shared across apps
├── static/css/     # Stylesheets
├── docs/           # Supporting documentation
├── manage.py
├── requirements.txt
└── README.md
```

## Features

- **Authentication & Roles** — registration and login via Django's auth system; each user has an `employee` or `hr` role that determines which views and dashboard they can access.
- **Check-In / Check-Out** — one check-in and one check-out per employee per day, timestamped server-side; duplicate or overlapping entries are rejected.
- **Working Hours Calculation** — daily hours derived from check-in/check-out pairs, aggregated into weekly/monthly summaries; days with a missing check-out are flagged as *Incomplete* rather than silently counted as zero hours.
- **Leave Requests & Deduction** — employees submit leave requests against their balance; HR approves or rejects them; approved leave deducts from the balance and is reflected in attendance status.
- **Attendance Status Tracking** — a dedicated status-computation layer derives Present / Absent / On Leave / Half-day / Incomplete per employee per day from attendance and leave records.
- **HR Dashboard** — organization-wide view of today's attendance, leave requests awaiting action, and per-employee working-hour trends.
- **Employee Dashboard** — personal check-in/check-out control, attendance history, and leave balance/request history.

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/dangbros/employee-attendance-management.git
cd employee-attendance-management

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create an HR/admin account
python manage.py createsuperuser

# (Optional) Load seed data — a few demo employees, an HR user, and sample attendance/leave history
python manage.py loaddata seed_data.json

# Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

<!-- If demo login credentials are seeded, list them here, e.g.:
### Demo Credentials
| Role | Username | Password |
|---|---|---|
| HR | hr_demo | demo-pass-123 |
| Employee | emp_demo | demo-pass-123 |
-->

## Database Schema

Core models:

- **User** (`accounts`) — extends Django's user model with a `role` field (`employee` / `hr`).
- **Attendance** (`attendance`) — one row per employee per day; `check_in`, `check_out` timestamps; unique constraint on `(employee, date)`.
- **LeaveRequest** (`leaves`) — `employee`, `start_date`, `end_date`, `status` (pending/approved/rejected), `reviewed_by`, `reviewed_at`.
- **LeaveBalance** (`leaves`) — running balance per employee.

Foreign keys tie `Attendance` and `LeaveRequest` to `User`, with indexes on `employee` and `date` fields to keep dashboard queries fast.

To generate a schema dump for review:

```bash
python manage.py sqlmigrate attendance 0001
python manage.py sqlmigrate leaves 0001
python manage.py sqlmigrate accounts 0001
```

## Leave Policy

<!-- Fill in the actual policy implemented, e.g.: -->
Each employee accrues **N days of paid leave per month**, credited automatically and deducted upon HR approval of a leave request. Unapproved absences (no check-in and no filed leave) are tracked separately from approved leave and do not draw down the balance.

## Timezone Policy

All timestamps are stored in UTC and rendered in the configured local timezone (`TIME_ZONE` in `config/settings.py`), using Django's timezone-aware datetime handling throughout.

## Security Notes

- Passwords are hashed via Django's default password hasher (PBKDF2).
- Role checks are enforced server-side in views/decorators, not just hidden in the UI — an employee cannot reach HR views by guessing a URL.
- Django's CSRF protection is enabled on all forms.
- All database access goes through the Django ORM — no raw string-interpolated SQL.
- For production deployment, set `DEBUG=False` and enable `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` in settings.

## Testing

```bash
python manage.py test
```

Tests focus on the working-hours calculation and leave-deduction logic, since these are the parts most likely to have subtle edge-case bugs (missing check-outs, overlapping leave requests, balance underflow).

## Assumptions

<!-- List any ambiguous-requirement decisions made during implementation, e.g.: -->
- A day with a check-in but no check-out is marked *Incomplete* rather than counted toward working hours.
- Leave requests spanning weekends/holidays are counted at face value (no holiday calendar in this version).
- Only one active session per user is assumed; no explicit device/session management was implemented.

## Future Work

Given more time, the next priorities would be:

- CI pipeline running the test suite on every push
- CSV export of attendance/leave reports from the HR dashboard
- A dedicated leave-approval audit log (beyond `reviewed_by`/`reviewed_at`)
- A holiday calendar feeding into status calculation
- Working-hours trend charts on the HR and employee dashboards
- Docker-based one-command setup


<!-- Add license if required by the assignment, e.g. MIT, or omit if not applicable -->