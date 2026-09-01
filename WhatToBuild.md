# Polish Pass on Employee Attendance Management System

## Context

The core Employee Attendance Management System is already implemented and working (Django + DRF/templates, SQL backend) — see MR !3 (`employee_management_system` on GitLab): login/registration, check-in/check-out, working-hours calculation, leave deduction, HR dashboard, employee dashboard, and attendance status tracking are all done.

This is a **follow-up pass** on the same branch/repo to strengthen the submission against the assessment's stated criteria: architecture, code quality, UI/UX, database design, security, and overall implementation. Work through the items below **one at a time, in the order given**, and after each one: run the existing test suite to confirm nothing broke, then commit with a clear, scoped message before moving to the next item. Don't batch multiple items into one commit.

Do not touch or refactor unrelated parts of the existing feature set unless a task below explicitly requires it.

---

## Group 1 — High impact, low effort (do these first)

### 1. CI pipeline
Add a `.gitlab-ci.yml` that runs `python manage.py test` on every push (and merge request). Use an appropriate Python Docker image, cache pip dependencies, and install from `requirements.txt`. Keep it to a single `test` stage for now — don't over-engineer with deploy stages that don't exist yet.

### 2. Screenshots in the README
Take (or describe exactly how to take, if you can't capture images directly) 3–4 screenshots: login page, employee dashboard, HR dashboard, and the leave approval view. Add an "Screenshots" section to the README embedding these images with brief captions.

### 3. Database scripts deliverable
The assignment explicitly asks for "database scripts." Migrations satisfy this technically, but make it explicit: add a README section showing either (a) `python manage.py sqlmigrate <app> <migration>` output for the key migrations, or (b) a generated `schema.sql` dump of the full schema. Include the exact command used so evaluators can reproduce it.

### 4. Production hardening notes + settings
In `settings.py`, add a `DEBUG`-gated security block: `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, and `SECURE_BROWSER_XSS_FILTER`, all active only when `DEBUG=0`. Document this in the README under a "Security" section so it's visible without reading the code.

---

## Group 2 — Medium effort, strengthens "overall implementation"

### 5. CSV export
Add a "Export CSV" action on the HR dashboard for monthly attendance — employee name, date, check-in, check-out, hours worked, status. Use Django's `HttpResponse` with `content_type="text/csv"` and the `csv` module; don't add a new dependency for this.

### 6. Password reset flow
Wire up Django's built-in password-reset views (`PasswordResetView`, `PasswordResetConfirmView`, etc.) with the console email backend for local/dev use. Add the necessary URL patterns and minimal templates matching the existing UI style. Note in the README that a real email backend (SMTP/SendGrid/etc.) would replace the console backend in production.

### 7. Pagination
Add pagination to the HR dashboard's employee/attendance table and to the leave-history view — use Django's built-in `Paginator`, default page size 20, with prev/next controls matching the existing template style.

### 8. Audit trail for leave decisions
Add a dedicated `LeaveAuditLog` model (or similarly named) recording: leave request reference, action (approved/rejected), performed_by, timestamp, and optional notes. Populate it at the same point `reviewed_by`/`reviewed_at` are currently set, without removing those fields. Surface a simple read-only log view for HR.

---

## Group 3 — Nice to have (implement if time allows; otherwise write a "Future Work" README section describing each briefly)

### 9. Working-hours trend charts
Add a `<canvas>`-based chart (Chart.js via CDN, no new backend dependency) on the trends page showing weekly or monthly hours-worked trend per employee (employee view) and aggregate trend (HR view).

### 10. Holiday calendar
Add a `Holiday` model (date, name) and feed it into the attendance-status computation so holidays aren't miscounted as absences. Seed a small set of holidays as an example.

### 11. Dockerfile
Add a `Dockerfile` (and `docker-compose.yml` if a separate DB service is used) for one-command setup: build, migrate, seed, run. Document the exact commands in the README.

### 12. Leave accrual + carry-forward policy
Upgrade the leave-balance model from a fixed allotment to monthly accrual with a capped carry-forward into the next year. Document the exact policy (accrual rate, cap, carry-forward rules) in the README's leave-policy section, replacing the previous fixed-allotment description.

---

## Reporting back

After each completed item, give a one-line summary of what changed and confirm tests pass. At the end of each group, give a short overall status update before moving to the next group. If any item conflicts with existing architecture in a way that needs a judgment call, flag it and state the decision you made rather than silently picking one.