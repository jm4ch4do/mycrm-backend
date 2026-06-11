"""ExecutionLog model stub for workflow execution auditing.

This is a placeholder for detailed implementation in KAN-22.
The real implementation will include step-level logs, error details, and durations.
"""

import uuid

from django.conf import settings
from django.db import models


class ExecutionLog(models.Model):
    """Record of a Workflow execution for auditability."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        "Workflow",
        on_delete=models.CASCADE,
        related_name="execution_logs",
    )

    # Trigger context
    event = models.ForeignKey(
        "Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_executions",
    )

    # Execution state
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Audit
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_executions",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workflow", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
