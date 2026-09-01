# Employee Attendance Management System

A production-quality attendance and leave management application built for the
Inner Eye Consultancy Services LLP developer assignment.

## Stack choice and reasoning

**Django 5 + server-rendered Bootstrap 5 templates (Option A).** Django's
battle-tested auth (extended `AbstractUser`, PBKDF2 password hashing, session
auth with CSRF protection), ORM with declarative migrations, and admin site
cover the security-sensitive foundations out of the box, letting the effort go
into the attendance/leave business logic. Server-rendered templates mean no
build step, a single deployable, and a clean demo from a fresh clone. SQLite
is used for local development; the schema uses only portable types and
constraints and switches to PostgreSQL via environment variables.

## Features

- **Registration & login** with Employee ID, hashed passwords, unique
  email/employee-ID validation. Roles (`employee` / `hr`) drive dashboards and
  are never client-assignable: self-registration always creates employees.
- **Check-in / check-out**: one of each per day, server-side timestamps,
  guards for duplicate check-ins, check-out before check-in, and double
  check-outs (service layer + DB unique/check constraints).
- **Working hours**: daily hours from check-in/out pairs, weekly and monthly
  aggregates; missed check-outs are flagged **Incomplete**, distinct from
  zero-hour (Absent) days.
- **Leave management**: per-employee balance, request → HR approve/reject
  workflow, business-day counting, overlap prevention, balance reservation for
  pending requests, atomic deduction at approval.
- **Status tracking** via a single service layer (`attendance/services.py`):
  Present / Half-day / Working / Incomplete / On leave / Absent / Weekend /
  Not checked in — all derivable per employee per day.
- **HR dashboard**: whole-team status for any past day, search + department +
  date filters, per-employee working-hour trends over a date range, leave
  approvals. **Employee dashboard**: one-click check-in/out with immediate
  feedback, personal history, leave balance and request form.
- **Distinct role UI**: HR gets a dark navbar with an HR badge; employees a
  blue navbar. Color-coded status badges throughout.

## Screenshots

Screenshots live in `docs/screenshots/`. To (re)capture them, start the app
with seeded demo data (`python manage.py seed_demo`, see setup below) and
save the following pages:

| File | Page | How to capture |
|------|------|----------------|
| `docs/screenshots/login.png` | Login page | Open http://127.0.0.1:8000/login/ while logged out |
| `docs/screenshots/employee_dashboard.png` | Employee dashboard | Log in as `EMP001` |
| `docs/screenshots/hr_dashboard.png` | HR team dashboard | Log in as `HR001` |
| `docs/screenshots/leave_approvals.png` | Leave approvals | As `HR001`, open “Leave requests” |

![Login page](docs/screenshots/login.png)

*Login: employees sign in with their Employee ID; passwords are hashed, never stored in plaintext.*

![Employee dashboard](docs/screenshots/employee_dashboard.png)

*Employee dashboard: one-click check-in/check-out with immediate feedback, weekly/monthly hours and leave balance.*

![HR dashboard](docs/screenshots/hr_dashboard.png)

*HR dashboard (dark navbar + HR badge): whole-team status for any day with search, department and date filters.*

![Leave approvals](docs/screenshots/leave_approvals.png)

*Leave approvals: pending requests with one-click approve/reject and a review history.*

## Setup from a fresh clone

```bash
git clone https://gitlab.com/souryaroy-group/employee_management_system.git
cd employee_management_system
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate         # creates the SQLite schema
python manage.py seed_demo       # demo users + 3 weeks of history
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in.

| Role | Login (Employee ID) | Password |
|------|--------------------|----------|
| HR | `HR001` | `DemoPass123!` |
| Employees | `EMP001` … `EMP004` | `DemoPass123!` |

Run the automated tests (working hours, status derivation, leave deduction):

```bash
python manage.py test
```

### Environment variables (all optional for local dev)

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Secret key (required in production) |
| `DJANGO_DEBUG` | `1` (default) or `0` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Set `POSTGRES_DB` to switch from SQLite to PostgreSQL |

## Leave policy (implemented)

- Every employee receives a **fixed annual allotment of 24 paid leave days**
  (`ANNUAL_LEAVE_DAYS` in `config/settings.py`), credited when the account is
  created. A fixed allotment was chosen over monthly accrual because it is the
  simplest policy that still exercises the full deduction workflow; accrual
  can be layered on later without schema changes.
- Only **business days (Mon–Fri)** in a request count against the balance.
- The balance is **deducted at approval time**, atomically with row locking.
  Pending requests **reserve** balance so an employee cannot over-book.
- Overlapping pending/approved requests are rejected.
- **Retroactive requests are allowed** so an unplanned absence can be
  regularised afterwards. Until then it shows as **Absent** (unapproved),
  clearly distinguishable from **On leave** (approved).

## Timezone policy

All datetimes are stored in **UTC** (`USE_TZ = True`) and displayed in
**Asia/Kolkata** (`TIME_ZONE`), the company's local time. A "day" for
attendance purposes is a calendar day in local time. All check-in/check-out
timestamps are captured server-side; client-supplied times are never trusted.

## Day status model

| Status | Meaning |
|--------|---------|
| Present | Checked in and out, ≥ 4 h worked |
| Half-day | Checked in and out, < 4 h worked |
| Working | Today: checked in, not yet out |
| Incomplete | Past day: checked in but never checked out (missed check-out) |
| On leave | Covered by an approved leave request |
| Absent | Past weekday: no check-in and no approved leave |
| Weekend | Sat/Sun with no activity |
| Not checked in | Today: no check-in yet |

## Database design (ER description)

```
accounts_user (custom AUTH_USER_MODEL, extends AbstractUser)
  id PK · employee_id UNIQUE · username UNIQUE (mirrors employee_id)
  email · password (hashed) · role ('employee'|'hr') · department · ...
   │
   ├─1:N─ attendance_attendance
   │        id PK · user_id FK · date · check_in (UTC) · check_out (UTC)
   │        UNIQUE(user_id, date) · CHECK(check_out > check_in)
   │        INDEX(user_id, date) · INDEX(date)
   │
   ├─1:1─ leaves_leavebalance
   │        id PK · user_id FK UNIQUE · balance DECIMAL(5,1) · updated_at
   │
   └─1:N─ leaves_leaverequest
            id PK · user_id FK · start_date · end_date · days DECIMAL(4,1)
            reason · status ('pending'|'approved'|'rejected')
            reviewed_by_id FK→user (SET_NULL) · created_at · reviewed_at
            CHECK(end_date >= start_date)
            INDEX(user_id, status) · INDEX(start_date, end_date)
```

Migration scripts live in `accounts/migrations/`, `attendance/migrations/`
and `leaves/migrations/`.

### Database scripts

The Django migrations above are the canonical schema; a readable reference
dump of the application tables is provided at [`docs/schema.sql`](docs/schema.sql).

Regenerate engine-specific DDL yourself at any time:

```bash
# Per-migration DDL (dialect follows your configured database):
python manage.py sqlmigrate accounts 0001
python manage.py sqlmigrate attendance 0001
python manage.py sqlmigrate leaves 0001

# Or dump the full live schema after `python manage.py migrate`:
sqlite3 db.sqlite3 .schema                # SQLite
pg_dump --schema-only "$POSTGRES_DB"     # PostgreSQL
```

## Architecture

- `accounts/` — custom user, registration/login, `hr_required` decorator
- `attendance/` — model, **`services.py`** (status computation, hours,
  summaries — single source of truth), views, template tags, tests
- `leaves/` — models, **`services.py`** (business-day math, overlap/balance
  validation, atomic approve/reject), views, tests
- `templates/` — Bootstrap 5 server-rendered UI

## Security

- Framework password hashing (PBKDF2); passwords are never stored or logged in plaintext
- ORM-only queries throughout — no raw or string-interpolated SQL
- CSRF protection on every form; all state-changing actions are POST-only
- Server-side role enforcement (`hr_required`) on every HR view; employees can
  only query their own data
- All client-supplied dates are parsed and validated with safe fallbacks
- **Production hardening**, active automatically when `DJANGO_DEBUG=0`
  (see `config/settings.py`):
  - `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
  - HSTS: `SECURE_HSTS_SECONDS=31536000` with subdomains and preload
  - `SECURE_CONTENT_TYPE_NOSNIFF`
  - Note: `SECURE_BROWSER_XSS_FILTER` (the legacy `X-XSS-Protection` header)
    was removed in Django 4, so the modern equivalents above are used instead

## Assumptions

- Working week is Mon–Fri; weekends are never Absent and never deducted.
- One check-in/check-out pair per day (no split shifts).
- Leave is taken in whole business days.
- Employees log in with their Employee ID.
- HR accounts are provisioned via the seed command or Django admin, never
  through self-registration.
- Missed check-outs remain visible as Incomplete for HR follow-up rather than
  being auto-closed.
- Half-day threshold is 4 hours (configurable in settings).

## What I would add with more time

- Audit logging of approvals and attendance edits
- Email/in-app notifications for leave decisions and missed check-outs
- CSV/Excel export of monthly attendance reports
- Public-holiday calendar integrated into status and leave math
- Monthly accrual and year-end carry-forward for leave balances
- A DRF JSON API alongside the templates plus OpenAPI docs
- Charts for working-hour trends and pagination for large teams
- Password reset flow and stronger session hardening for production
- Dockerfile + CI pipeline running the test suite
