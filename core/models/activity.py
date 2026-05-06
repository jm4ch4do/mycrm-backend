import uuid

from django.conf import settings
from django.db import models


class ActivityType(models.TextChoices):
    """Type discriminator for Activity specializations."""

    TASK = "task", "Task"
    MEETING = "meeting", "Meeting"
    CALL = "call", "Call"
    NOTE = "note", "Note"


class ActivityStatus(models.TextChoices):
    """Lifecycle status for an Activity."""

    PLANNED = "planned", "Planned"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "Canceled"


class Activity(models.Model):
    """
    Activity is the generic base abstraction for all CRM engagement records.

    Specific activity types (Task, Meeting, Call) extend this model via
    OneToOneField composition. At least one of account, contact, or deal
    must be set (enforced at the serializer/service layer).
    """

    # Identity
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=ActivityType.choices)
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(blank=True, null=True)

    # Ownership & Context
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_activities",
    )
    account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
    )
    contact = models.ForeignKey(
        "Contact",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
    )
    deal = models.ForeignKey(
        "Deal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
    )

    # Lifecycle
    status = models.CharField(
        max_length=20,
        choices=ActivityStatus.choices,
        default=ActivityStatus.PLANNED,
    )
    due_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities_updated",
    )
    is_invalid = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner_user"]),
            models.Index(fields=["account"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["deal"]),
            models.Index(fields=["type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_invalid"]),
        ]

    def __str__(self) -> str:
        return str(self.title)
