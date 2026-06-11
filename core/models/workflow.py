"""Workflow model for multi-step automation orchestration."""

import uuid

from django.conf import settings
from django.db import models

from .trigger import Trigger


class Workflow(models.Model):
    """Orchestrates an ordered sequence of Actions executed when a Trigger fires and Rules pass."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.PROTECT,
        related_name="workflows",
    )

    # Steps
    steps = models.ManyToManyField(
        "Action",
        through="WorkflowStep",
        related_name="workflows",
    )

    # Lifecycle
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflows_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflows_updated",
    )
    is_invalid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trigger"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.trigger.name})"


class WorkflowStep(models.Model):
    """Represents a single step in a Workflow execution sequence."""

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="workflow_steps",
    )
    action = models.ForeignKey(
        "Action",
        on_delete=models.PROTECT,
        related_name="workflow_steps",
    )
    step_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["step_order"]
        unique_together = [["workflow", "step_order"]]

    def __str__(self) -> str:
        return f"{self.workflow.name} - Step {self.step_order}"
