"""Rule model for automation pipeline condition gating."""

import uuid

from django.conf import settings
from django.db import models

from .trigger import Trigger


class Rule(models.Model):
    """Business logic gate evaluated against an event payload before Workflow execution."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.PROTECT,
        related_name="rules",
    )

    # Evaluation
    conditions = models.JSONField()
    evaluation_order = models.PositiveIntegerField(default=0)

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
        related_name="rules_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rules_updated",
    )
    is_invalid = models.BooleanField(default=False)

    class Meta:
        ordering = ["evaluation_order", "created_at"]
        indexes = [
            models.Index(fields=["trigger"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_invalid"]),
            models.Index(fields=["evaluation_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.trigger.name})"
