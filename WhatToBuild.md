#Employee Attendance Management System

Build a complete, production-quality **Employee Attendance Management System** for a developer assignment submission (Inner Eye Consultancy Services LLP). This needs to be a fully working application, not a prototype — treat it as something that will be evaluated on architecture, code quality, UI/UX, database design, and security.

## Tech Stack (you choose, justify briefly)

Pick **one** backend and stick with it end-to-end:
- **Option A:** Django + Django REST Framework, with Django's ORM and built-in auth as a foundation (extend the User model rather than replacing it outright)
- **Option B:** FastAPI + SQLModel (or SQLAlchemy), with Pydantic schemas and JWT-based auth

Use a **relational SQL database** — SQLite for local dev/setup simplicity, but write the schema so it ports cleanly to PostgreSQL (no SQLite-only types, use proper foreign keys and constraints).

For the frontend, choose whichever pairs best with your backend choice:
- Django → server-rendered templates with Bootstrap 5 (clean, no unnecessary JS frameworks)
- FastAPI → a lightweight React (Vite) SPA consuming the REST API

State your stack choice and reasoning in one short paragraph before writing code.

## Core Features (all required)

1. **Employee Login & Registration**
   - Registration with email/employee ID, password hashing (never plaintext), basic validation
   - Login with session or JWT auth depending on stack
   - Role field: `employee` vs `hr` (or `admin`) — this drives dashboard access

2. **Attendance Check-In / Check-Out**
   - One check-in and one check-out per day per employee (prevent duplicate/overlapping entries)
   - Timestamp captured server-side, not trusted from client
   - Handle edge cases: check-out without check-in, missed check-outs

3. **Working Hours Calculation**
   - Compute daily hours worked from check-in/check-out pairs
   - Aggregate into weekly/monthly summaries
   - Flag incomplete days (missing check-out) distinctly from zero-hour days

4. **Leave Deduction Calculation**
   - A leave balance per employee (e.g. accrued monthly or fixed annual allotment — pick a reasonable policy and document it)
   - Leave requests reduce balance; unapproved absences (no check-in, no leave filed) should be distinguishable from approved leave
   - Simple approval workflow: employee requests leave → HR approves/rejects

5. **HR Dashboard**
   - View all employees, their attendance status today, working-hour trends, and leave balances
   - Approve/reject leave requests
   - Filter/search by employee, date range, department (if you add one)

6. **Employee Dashboard**
   - Personal check-in/check-out control
   - Personal attendance history and working-hours summary
   - Leave balance and leave request form/history

7. **Attendance Status Tracking**
   - Per-day status per employee: Present / Absent / On Leave / Half-day / Incomplete
   - This should be derivable/queryable, not just a raw log — build a clear status-computation layer (a service/utility function, not scattered logic in views)

## Architecture & Code Quality Requirements

- Clean separation of concerns: models / business logic (attendance & leave calculations) / views-or-routes / serializers-or-schemas
- All date/time handling must be timezone-aware and consistent (pick and document one timezone policy)
- Input validation on every endpoint/form — no trusting client-supplied dates, hours, or roles
- Passwords hashed (use the framework's built-in hasher, e.g. Django's `make_password` or `passlib`/`bcrypt` for FastAPI)
- Authorization checks: employees can only see their own data; only HR/admin role can see the HR dashboard or approve leave — enforce this server-side, not just by hiding UI elements
- No SQL injection surfaces — use the ORM/parameterized queries throughout, never raw string-interpolated SQL
- Sensible error handling and HTTP status codes (for the API option) or user-facing error messages (for the template option)
- Add basic automated tests for the working-hours calculation and leave-deduction logic specifically, since that's the trickiest business logic to get subtly wrong

## Database Design

- Design the schema first (Employee, Attendance, Leave/LeaveRequest, and any supporting tables) with proper foreign keys, indexes on frequently-queried columns (employee_id, date), and sensible constraints (unique constraint on employee+date for attendance, for example)
- Include a short ER description or diagram (text-based is fine) in the docs

## UI/UX Expectations

- Clean, uncluttered dashboards — this doesn't need to be fancy, but it needs to be usable: clear status indicators (color-coded present/absent/leave), readable tables for history, and a simple check-in/check-out button that gives immediate feedback
- Distinct visual treatment for HR vs employee views so it's obvious which role is logged in

## Deliverables

1. Full source code, organized in a clean project structure
2. Database schema/migration scripts
3. A `README.md` with:
   - Setup instructions from a fresh clone (dependencies, env vars, migration/seed commands, how to run)
   - The leave policy you implemented and why
   - Any assumptions you made about ambiguous requirements
4. Seed data / fixtures so the app is immediately demoable with a few employees, an HR user, and some attendance history
5. A short note on what you'd add with more time (shows awareness of scope, e.g. audit logging, notifications, reports export)

## Process

Work through this in order: schema design → backend models & auth → attendance/leave business logic (with tests) → HR and employee endpoints/views → frontend dashboards → seed data → README. Don't skip straight to UI before the business logic is solid — the working-hours and leave-deduction calculations are what will actually be scrutinized.