"""Business logic service for Activity model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Activity

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


class ActivityService:
    """Service layer for Activity business logic."""

    @staticmethod
    def list_activities() -> Any:
        """Retrieve all active activities."""
        return Activity.objects.filter(is_invalid=False)

    @staticmethod
    def get_activity(activity_id: str) -> Activity:
        """Retrieve a single activity by ID."""
        return get_object_or_404(Activity, id=activity_id)

    @staticmethod
    @transaction.atomic
    def create_activity(data: dict[str, Any], user: User) -> Activity:
        """Create a new activity with business logic enforcement."""
        activity = Activity.objects.create(
            owner_user=user,
            created_by=user,
            **data,
        )
        return activity

    @staticmethod
    @transaction.atomic
    def update_activity(
        activity: Activity, data: dict[str, Any], user: User
    ) -> Activity:
        """Update an activity with business logic enforcement."""
        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        data["updated_by"] = user
        for field, value in data.items():
            setattr(activity, field, value)

        activity.save()
        return activity

    @staticmethod
    @transaction.atomic
    def soft_delete_activity(activity: Activity, user: User) -> Activity:
        """Soft-delete an activity by setting is_invalid=True."""
        activity.is_invalid = True
        activity.updated_by = user
        activity.save()
        return activity
