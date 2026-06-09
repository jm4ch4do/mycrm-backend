"""Event model for immutable automation/audit facts."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class EventSourceService(models.TextChoices):
    """Source services that emit events."""

    CORE = "core", "Core"
    ACTIVITIES = "activities", "Activities"
    AUTOMATION = "automation", "Automation"


class Event(models.Model):
    """Immutable fact record representing a domain state change."""

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)
    source_service = models.CharField(
        max_length=20,
        choices=EventSourceService.choices,
    )
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()

    # Payload
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField()
    metadata = models.JSONField(null=True, blank=True)

    # Audit
    occurred_at = models.DateTimeField(default=timezone.now)
    emitted_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events_created",
    )

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["source_service"]),
            models.Index(fields=["entity_type"]),
            models.Index(fields=["entity_id"]),
            models.Index(fields=["occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.entity_type}:{self.entity_id})"
