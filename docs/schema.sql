-- Reference schema for the Employee Attendance Management System.
--
-- The Django migrations in accounts/migrations/, attendance/migrations/ and
-- leaves/migrations/ are the CANONICAL source of the schema. This file is a
-- readable reference of the application tables (SQLite dialect); Django's
-- built-in auth/session/admin tables and the user group/permission M2M
-- tables are omitted for brevity.
--
-- Regenerate engine-specific DDL at any time with:
--   python manage.py sqlmigrate accounts 0001
--   python manage.py sqlmigrate attendance 0001
--   python manage.py sqlmigrate leaves 0001
-- or dump the live schema after `python manage.py migrate`:
--   sqlite3 db.sqlite3 .schema                       (SQLite)
--   pg_dump --schema-only "$POSTGRES_DB"             (PostgreSQL)

-- Custom user (AUTH_USER_MODEL = accounts.User, extends AbstractUser)
CREATE TABLE "accounts_user" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "password" varchar(128) NOT NULL,          -- hashed, never plaintext
    "last_login" datetime NULL,
    "is_superuser" bool NOT NULL,
    "username" varchar(150) NOT NULL UNIQUE,   -- mirrors employee_id
    "first_name" varchar(150) NOT NULL,
    "last_name" varchar(150) NOT NULL,
    "email" varchar(254) NOT NULL,
    "is_staff" bool NOT NULL,
    "is_active" bool NOT NULL,
    "date_joined" datetime NOT NULL,
    "employee_id" varchar(20) NOT NULL UNIQUE,
    "role" varchar(10) NOT NULL,               -- 'employee' | 'hr'
    "department" varchar(50) NOT NULL
);

-- One attendance row per employee per local calendar day
CREATE TABLE "attendance_attendance" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "date" date NOT NULL,
    "check_in" datetime NULL,                  -- UTC, server-side timestamp
    "check_out" datetime NULL,                 -- UTC, server-side timestamp
    "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT "unique_attendance_per_user_day" UNIQUE ("user_id", "date"),
    CONSTRAINT "check_out_after_check_in" CHECK (
        "check_out" IS NULL OR ("check_in" IS NOT NULL AND "check_out" > "check_in")
    )
);
CREATE INDEX "attendance_user_date_idx" ON "attendance_attendance" ("user_id", "date");
CREATE INDEX "attendance_date_idx" ON "attendance_attendance" ("date");

-- Remaining paid-leave days per employee (1:1 with user)
CREATE TABLE "leaves_leavebalance" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "balance" decimal NOT NULL,                -- DECIMAL(5,1)
    "updated_at" datetime NOT NULL,
    "user_id" bigint NOT NULL UNIQUE REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Leave requests with approval workflow
CREATE TABLE "leaves_leaverequest" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "start_date" date NOT NULL,
    "end_date" date NOT NULL,
    "days" decimal NOT NULL,                   -- DECIMAL(4,1), business days
    "reason" text NOT NULL,
    "status" varchar(10) NOT NULL,             -- 'pending' | 'approved' | 'rejected'
    "created_at" datetime NOT NULL,
    "reviewed_at" datetime NULL,
    "reviewed_by_id" bigint NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED, -- ON DELETE SET NULL (enforced by Django)
    "user_id" bigint NOT NULL REFERENCES "accounts_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT "leave_end_on_or_after_start" CHECK ("end_date" >= "start_date")
);
CREATE INDEX "leave_user_status_idx" ON "leaves_leaverequest" ("user_id", "status");
CREATE INDEX "leave_dates_idx" ON "leaves_leaverequest" ("start_date", "end_date");
