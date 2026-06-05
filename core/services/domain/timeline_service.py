"""Read-only aggregation service for the Timeline/Activity Feed."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404

from core.models import Activity, Note

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

# Map entity_type strings to their model app-label names and related-name
# for Activity FK lookups.
_ENTITY_MODEL_MAP = {
    "account": ("core", "Account"),
    "contact": ("core", "Contact"),
    "deal": ("core", "Deal"),
}


class TimelineService:
    """Service layer for timeline aggregation.

    Queries Activity and Note records linked to a given CRM entity, merges
    them into a single chronological feed, and enforces Note visibility rules.
    """

    @staticmethod
    def get_timeline(
        entity_type: str,
        entity_id: str,
        user: "User",
    ) -> list[dict[str, Any]]:
        """Return merged, sorted timeline items for a CRM entity.

        Args:
            entity_type: One of 'account', 'contact', 'deal'.
            entity_id: Primary key of the parent entity.
            user: The requesting user (used for Note visibility filtering).

        Returns:
            List of timeline item dicts sorted by created_at descending.

        Raises:
            Http404: If the parent entity does not exist or is soft-deleted.
        """
        if entity_type not in _ENTITY_MODEL_MAP:
            raise Http404(f"Unknown entity type: {entity_type}")

        app_label, model_name = _ENTITY_MODEL_MAP[entity_type]
        model = apps.get_model(app_label, model_name)

        # Verify parent entity exists and is not soft-deleted
        parent = get_object_or_404(model, pk=entity_id)

        if getattr(parent, "is_invalid", False):
            raise Http404(f"{model_name} has been deleted.")

        # Fetch active Activities linked to this entity
        filter_kwargs = {entity_type: parent, "is_invalid": False}
        activities = Activity.objects.filter(**filter_kwargs).select_related(
            "task_detail",
            "meeting_detail",
            "call_detail",
            "owner_user",
        )

        # Fetch active Notes linked to this entity
        note_filter_kwargs = {entity_type: parent, "is_invalid": False}
        notes = Note.objects.filter(**note_filter_kwargs).select_related(
            "author"
        )

        # Build unified timeline items
        items: list[dict[str, Any]] = []

        for activity in activities:
            items.append(TimelineService._build_activity_item(activity))

        for note in notes:
            if TimelineService._is_note_visible(note, user):
                items.append(TimelineService._build_note_item(note))

        # Sort by created_at descending
        items.sort(key=lambda x: x["created_at"], reverse=True)

        return items

    @staticmethod
    def _is_note_visible(note: Any, user: "User") -> bool:
        """Return True if the note is visible to the requesting user."""
        if note.visibility == "private":
            return note.author == user or (
                hasattr(user, "is_staff") and user.is_staff
            )
        return True

    @staticmethod
    def _build_activity_item(activity: Any) -> dict[str, Any]:
        """Build a normalised timeline item dict from an Activity."""
        outcome = None
        direction = None
        start_time = None

        # Resolve subtype-specific fields — access may raise RelatedObjectDoesNotExist
        # if the OneToOne row is absent for this activity type.
        if hasattr(activity, "call_detail"):
            try:
                call = activity.call_detail
                outcome = call.outcome
                direction = call.direction
            except ObjectDoesNotExist:
                pass

        if hasattr(activity, "meeting_detail"):
            try:
                meeting = activity.meeting_detail
                outcome = meeting.outcome
                start_time = meeting.start_time
            except ObjectDoesNotExist:
                pass

        return {
            "id": str(activity.id),
            "type": activity.type,
            "title": activity.title,
            "body": None,
            "status": activity.status,
            "outcome": outcome,
            "direction": direction,
            "start_time": start_time,
            "due_at": activity.due_at,
            "completed_at": activity.completed_at,
            "created_at": activity.created_at,
            "owner_user": activity.owner_user_id,
            "author": None,
            "visibility": None,
            "is_pinned": None,
        }

    @staticmethod
    def _build_note_item(note: Any) -> dict[str, Any]:
        """Build a normalised timeline item dict from a Note."""
        return {
            "id": str(note.id),
            "type": "note",
            "title": note.title,
            "body": note.body,
            "status": None,
            "outcome": None,
            "direction": None,
            "start_time": None,
            "due_at": None,
            "completed_at": None,
            "created_at": note.created_at,
            "owner_user": None,
            "author": note.author_id,
            "visibility": note.visibility,
            "is_pinned": note.is_pinned,
        }
