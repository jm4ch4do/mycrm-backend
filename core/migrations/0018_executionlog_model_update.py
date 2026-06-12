from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_alter_action_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="executionlog",
            options={"ordering": ["-started_at"]},
        ),
        migrations.RemoveIndex(
            model_name="executionlog",
            name="core_execut_workflo_51fdf3_idx",
        ),
        migrations.RemoveIndex(
            model_name="executionlog",
            name="core_execut_status_37def8_idx",
        ),
        migrations.RenameField(
            model_name="executionlog",
            old_name="completed_at",
            new_name="finished_at",
        ),
        migrations.RenameField(
            model_name="executionlog",
            old_name="triggered_by",
            new_name="created_by",
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="execution_logs",
                to="core.event",
            ),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="workflow",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="execution_logs",
                to="core.workflow",
            ),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("running", "Running"),
                    ("success", "Success"),
                    ("failed", "Failed"),
                    ("partial", "Partial"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="started_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="finished_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="executionlog",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="execution_logs_created",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="executionlog",
            name="logs",
            field=models.JSONField(default=list),
        ),
        migrations.AddIndex(
            model_name="executionlog",
            index=models.Index(fields=["workflow"], name="core_execut_workflow_idx"),
        ),
        migrations.AddIndex(
            model_name="executionlog",
            index=models.Index(fields=["event"], name="core_execut_event_idx"),
        ),
        migrations.AddIndex(
            model_name="executionlog",
            index=models.Index(fields=["status"], name="core_execut_status_idx"),
        ),
        migrations.AddIndex(
            model_name="executionlog",
            index=models.Index(fields=["started_at"], name="core_execut_started_idx"),
        ),
    ]