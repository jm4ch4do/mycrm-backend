"""Trigger model for automation event gating."""

import uuid

from django.conf import settings
from django.db import models


class Trigger(models.Model):
    """Automation gate that matches incoming events before rule evaluation."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100, blank=True, null=True)

    # Conditions
    conditions = models.JSONField(null=True, blank=True)

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
        related_name="triggers_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggers_updated",
    )
    is_invalid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["entity_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.event_type})"
