"""ExecutionLog model for workflow execution auditing."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ExecutionStatus(models.TextChoices):
    """Terminal and in-progress workflow execution states."""

    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    PARTIAL = "partial", "Partial"


class ExecutionLog(models.Model):
    """Record of a Workflow execution for auditability."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        "Workflow",
        on_delete=models.PROTECT,
        related_name="execution_logs",
    )
    event = models.ForeignKey(
        "Event",
        on_delete=models.PROTECT,
        related_name="execution_logs",
    )

    # Lifecycle
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
    )
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Detail
    logs = models.JSONField(default=list)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="execution_logs_created",
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["workflow"]),
            models.Index(fields=["event"]),
            models.Index(fields=["status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name} ({self.status})"
