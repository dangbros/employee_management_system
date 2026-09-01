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
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("check_in", models.DateTimeField(blank=True, null=True)),
                ("check_out", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-date"],
                "verbose_name_plural": "attendance records",
            },
        ),
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(fields=["user", "date"], name="attendance_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="attendance",
            index=models.Index(fields=["date"], name="attendance_date_idx"),
        ),
        migrations.AddConstraint(
            model_name="attendance",
            constraint=models.UniqueConstraint(fields=("user", "date"), name="unique_attendance_per_user_day"),
        ),
        migrations.AddConstraint(
            model_name="attendance",
            constraint=models.CheckConstraint(
                condition=models.Q(check_out__isnull=True)
                | (models.Q(check_in__isnull=False) & models.Q(check_out__gt=models.F("check_in"))),
                name="check_out_after_check_in",
            ),
        ),
    ]
