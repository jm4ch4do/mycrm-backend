"""Action model for workflow step orchestration."""

import uuid

from django.conf import settings
from django.db import models


class ActionType(models.TextChoices):
    """Supported automation action handler types."""

    CREATE_TASK = "create_task", "Create Task"
    UPDATE_DEAL_STAGE = "update_deal_stage", "Update Deal Stage"
    ASSIGN_OWNER = "assign_owner", "Assign Owner"
    ADD_NOTE = "add_note", "Add Note"
    EMIT_EVENT = "emit_event", "Emit Event"


class Action(models.Model):
    """Atomic operation that a Workflow step executes."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    action_type = models.CharField(max_length=50, choices=ActionType.choices)

    # Execution
    parameters = models.JSONField(null=True, blank=True)
    retry_policy = models.JSONField(null=True, blank=True)
    timeout_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_updated",
    )
    is_invalid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action_type"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.action_type})"
