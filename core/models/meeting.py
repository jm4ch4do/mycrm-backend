import uuid

from django.conf import settings
from django.db import models

from core.models.activity import Activity
from core.models.contact import Contact


class MeetingOutcome(models.TextChoices):
    """Outcome choices for a completed Meeting."""

    COMPLETED = "completed", "Completed"
    NO_SHOW = "no_show", "No Show"
    RESCHEDULED = "rescheduled", "Rescheduled"
    CANCELED = "canceled", "Canceled"


class Meeting(models.Model):
    """
    Meeting entity represents a scheduled interaction in the CRM.

    Extends Activity via OneToOneField composition. Creating a Meeting
    requires a parent Activity with type='meeting'. Soft deletion propagates
    by setting activity.is_invalid=True rather than removing the Meeting row.
    Once outcome is set the meeting becomes read-only.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.OneToOneField(
        Activity,
        on_delete=models.CASCADE,
        related_name="meeting_detail",
    )

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    meeting_url = models.URLField(blank=True, null=True)
    outcome = models.CharField(
        max_length=20,
        choices=MeetingOutcome.choices,
        blank=True,
        null=True,
    )
    summary = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self) -> str:
        return str(self.activity.title)


class MeetingUserAssoc(models.Model):
    """Join table for internal participants (CRM users) on a Meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="user_participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "user"],
                name="unique_meeting_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.meeting} - {self.user}"


class MeetingContactAssoc(models.Model):
    """Join table for external participants (Contacts) on a Meeting."""

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="contact_participants",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "contact"],
                name="unique_meeting_contact",
            )
        ]

    def __str__(self) -> str:
        return f"{self.meeting} - {self.contact}"
