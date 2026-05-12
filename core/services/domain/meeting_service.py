"""Business logic service for Meeting model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import (
    Activity,
    ActivityStatus,
    ActivityType,
    Contact,
    Meeting,
    MeetingContactAssoc,
    MeetingUserAssoc,
)

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()

# Fields that belong to Activity, not Meeting
_ACTIVITY_FIELDS = {
    "title",
    "description",
    "due_at",
    "owner_user",
    "account",
    "contact",
    "deal",
    "completed_at",
}

# Meeting-own fields that may be supplied on create/update
_MEETING_FIELDS = {
    "start_time",
    "end_time",
    "location",
    "meeting_url",
    "outcome",
    "summary",
}


class MeetingService:
    """Service layer for Meeting business logic."""

    @staticmethod
    def list_meetings() -> Any:
        """Retrieve all active meetings (activity not soft-deleted)."""
        return Meeting.objects.filter(activity__is_invalid=False)

    @staticmethod
    def get_meeting(meeting_id: str) -> Meeting:
        """Retrieve a single meeting by ID."""
        return get_object_or_404(Meeting, id=meeting_id)

    @staticmethod
    @transaction.atomic
    def create_meeting(data: dict[str, Any], user: User) -> Meeting:
        """Create a Meeting by first creating the parent Activity(type='meeting').

        ``data`` may contain both Activity-level fields and Meeting-level
        fields. The ``type`` field is always forced to ActivityType.MEETING.
        """
        activity_data: dict[str, Any] = {}
        meeting_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _MEETING_FIELDS:
                meeting_data[key] = value
            # unknown fields are silently ignored

        activity = Activity.objects.create(
            type=ActivityType.MEETING,
            owner_user=user,
            created_by=user,
            **activity_data,
        )
        meeting = Meeting.objects.create(activity=activity, **meeting_data)
        return meeting

    @staticmethod
    @transaction.atomic
    def update_meeting(meeting: Meeting, data: dict[str, Any], user: User) -> Meeting:
        """Update both the parent Activity and Meeting-own fields.

        Raises ValueError if the meeting already has an outcome set
        (completed meetings are read-only).
        """
        if meeting.outcome is not None:
            raise ValueError("Cannot update a meeting that already has an outcome set.")

        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        activity_data: dict[str, Any] = {}
        meeting_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _MEETING_FIELDS:
                meeting_data[key] = value

        if activity_data:
            activity_data["updated_by"] = user
            for field, value in activity_data.items():
                setattr(meeting.activity, field, value)
            meeting.activity.save()

        if meeting_data:
            for field, value in meeting_data.items():
                setattr(meeting, field, value)
            meeting.save()

        return meeting

    @staticmethod
    @transaction.atomic
    def complete_meeting(
        meeting: Meeting, outcome: str, summary: str | None, user: User
    ) -> Meeting:
        """Set the meeting outcome and mark its parent activity as completed."""
        now = timezone.now()
        meeting.outcome = outcome
        meeting.summary = summary
        meeting.save()

        meeting.activity.status = ActivityStatus.COMPLETED
        meeting.activity.completed_at = now
        meeting.activity.updated_by = user
        meeting.activity.save()

        return meeting

    @staticmethod
    @transaction.atomic
    def soft_delete_meeting(meeting: Meeting, user: User) -> Meeting:
        """Soft-delete by propagating is_invalid=True to the parent activity."""
        meeting.activity.is_invalid = True
        meeting.activity.updated_by = user
        meeting.activity.save()
        return meeting

    @staticmethod
    @transaction.atomic
    def add_user_participant(meeting: Meeting, user: User) -> MeetingUserAssoc:
        """Add a CRM user as an internal participant of the meeting."""
        assoc, _ = MeetingUserAssoc.objects.get_or_create(meeting=meeting, user=user)
        return assoc

    @staticmethod
    @transaction.atomic
    def remove_user_participant(meeting: Meeting, user_id: Any) -> None:
        """Remove a CRM user from the meeting's internal participants."""
        MeetingUserAssoc.objects.filter(meeting=meeting, user_id=user_id).delete()

    @staticmethod
    @transaction.atomic
    def add_contact_participant(
        meeting: Meeting, contact: Contact
    ) -> MeetingContactAssoc:
        """Add a Contact as an external participant of the meeting."""
        assoc, _ = MeetingContactAssoc.objects.get_or_create(
            meeting=meeting, contact=contact
        )
        return assoc

    @staticmethod
    @transaction.atomic
    def remove_contact_participant(meeting: Meeting, contact_id: Any) -> None:
        """Remove a Contact from the meeting's external participants."""
        MeetingContactAssoc.objects.filter(
            meeting=meeting, contact_id=contact_id
        ).delete()
