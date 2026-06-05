import uuid

from django.db import models

from core.models.activity import Activity


class CallDirection(models.TextChoices):
    """Direction choices for a Call."""

    INBOUND = "inbound", "Inbound"
    OUTBOUND = "outbound", "Outbound"


class CallOutcome(models.TextChoices):
    """Outcome choices for a completed Call."""

    CONNECTED = "connected", "Connected"
    NO_ANSWER = "no_answer", "No Answer"
    VOICEMAIL = "voicemail", "Voicemail"
    BUSY = "busy", "Busy"
    WRONG_NUMBER = "wrong_number", "Wrong Number"


class Call(models.Model):
    """
    Call entity represents a phone call in the CRM.

    Extends Activity via OneToOneField composition. Creating a Call requires
    a parent Activity with type='call'. Soft deletion propagates by setting
    activity.is_invalid=True rather than removing the Call row.
    Once activity.status is completed the call becomes read-only.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.OneToOneField(
        Activity,
        on_delete=models.CASCADE,
        related_name="call_detail",
    )
    direction = models.CharField(
        max_length=20,
        choices=CallDirection.choices,
    )
    outcome = models.CharField(
        max_length=20,
        choices=CallOutcome.choices,
        blank=True,
        null=True,
    )
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-activity__created_at"]
        indexes = [
            models.Index(fields=["direction"]),
            models.Index(fields=["outcome"]),
        ]

    def __str__(self) -> str:
        return f"{self.activity.title} ({self.direction})"
