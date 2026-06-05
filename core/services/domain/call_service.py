"""Business logic service for Call model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import (
    Activity,
    ActivityStatus,
    ActivityType,
    Call,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

# Fields that belong to Activity, not Call
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

# Call-own fields that may be supplied on create/update
_CALL_FIELDS = {
    "direction",
    "outcome",
    "phone_number",
    "duration_seconds",
    "summary",
}


class CallService:
    """Service layer for Call business logic."""

    @staticmethod
    def list_calls() -> Any:
        """Retrieve all active calls (activity not soft-deleted)."""
        return Call.objects.filter(activity__is_invalid=False)

    @staticmethod
    def get_call(call_id: str) -> Call:
        """Retrieve a single call by ID."""
        return get_object_or_404(Call, id=call_id)

    @staticmethod
    @transaction.atomic
    def create_call(data: dict[str, Any], user: User) -> Call:
        """Create a Call by first creating the parent Activity(type='call').

        ``data`` must include ``direction``. Both Activity-level and
        Call-level fields may be supplied together; they are automatically
        routed to the correct model. Unknown keys are silently ignored.
        """
        if not data.get("direction"):
            raise ValidationError({"direction": "direction is required."})

        activity_data: dict[str, Any] = {}
        call_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _CALL_FIELDS:
                call_data[key] = value

        activity = Activity.objects.create(
            type=ActivityType.CALL,
            owner_user=user,
            created_by=user,
            **activity_data,
        )
        return Call.objects.create(activity=activity, **call_data)

    @staticmethod
    @transaction.atomic
    def update_call(call: Call, data: dict[str, Any], user: User) -> Call:
        """Update both the parent Activity and Call-own fields.

        Raises ValidationError if the call's activity is already completed.
        """
        if call.activity.status == ActivityStatus.COMPLETED:
            raise ValidationError(
                "Cannot update a call that is already completed."
            )

        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        activity_data: dict[str, Any] = {}
        call_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _CALL_FIELDS:
                call_data[key] = value

        if activity_data:
            activity_data["updated_by"] = user
            for field, value in activity_data.items():
                setattr(call.activity, field, value)
            call.activity.save()

        if call_data:
            for field, value in call_data.items():
                setattr(call, field, value)
            call.save()

        return call

    @staticmethod
    @transaction.atomic
    def complete_call(
        call: Call,
        outcome: str,
        summary: str | None,
        duration_seconds: int | None,
        user: User,
    ) -> Call:
        """Set the call outcome and mark its parent activity as completed.

        Raises ValidationError if the call is already completed.
        """
        if call.activity.status == ActivityStatus.COMPLETED:
            raise ValidationError("Cannot complete a call that is already completed.")

        now = timezone.now()
        call.outcome = outcome
        call.summary = summary
        call.duration_seconds = duration_seconds
        call.save()

        call.activity.status = ActivityStatus.COMPLETED
        call.activity.completed_at = now
        call.activity.updated_by = user
        call.activity.save()

        return call

    @staticmethod
    @transaction.atomic
    def soft_delete_call(call: Call, user: User) -> Call:
        """Soft-delete by propagating is_invalid=True to the parent activity."""
        call.activity.is_invalid = True
        call.activity.updated_by = user
        call.activity.save()
        return call
