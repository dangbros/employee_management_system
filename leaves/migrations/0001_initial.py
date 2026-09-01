import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LeaveBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.DecimalField(decimal_places=1, default=24, max_digits=5)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="leave_balance", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="LeaveRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("days", models.DecimalField(decimal_places=1, max_digits=4)),
                ("reason", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_leave_requests", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="leave_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["user", "status"], name="leave_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="leaverequest",
            index=models.Index(fields=["start_date", "end_date"], name="leave_dates_idx"),
        ),
        migrations.AddConstraint(
            model_name="leaverequest",
            constraint=models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="leave_end_on_or_after_start",
            ),
        ),
    ]
