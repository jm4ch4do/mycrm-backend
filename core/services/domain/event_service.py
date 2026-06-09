"""Business logic service for immutable Event records."""

from __future__ import annotations

import uuid
from typing import Any

from django.db.models import QuerySet

from core.models import Event


def _validate_event_type(event_type: str) -> None:
    """Validate event type as a non-empty dot-notation string."""
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError("event_type is required.")

    value = event_type.strip()
    if "." not in value:
        raise ValueError("event_type must use dot-notation (e.g. 'deal.updated').")

    parts = value.split(".")
    if any(not part.strip() for part in parts):
        raise ValueError("event_type must use dot-notation (e.g. 'deal.updated').")


def emit_event(
    event_type: str,
    source_service: str,
    entity_type: str,
    entity_id: uuid.UUID | str,
    after_state: dict[str, Any],
    before_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    emitted_by_user_id: uuid.UUID | str | None = None,
    created_by=None,
) -> Event:
    """Create and return an immutable Event record.

    This helper is intentionally transaction-agnostic and should be called from
    the caller's existing @transaction.atomic block.
    """
    _validate_event_type(event_type)

    if after_state is None:
        raise ValueError("after_state is required.")

    return Event.objects.create(
        event_type=event_type.strip(),
        source_service=source_service,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        metadata=metadata,
        emitted_by_user_id=emitted_by_user_id,
        created_by=created_by,
    )


class EventService:
    """Service layer for Event read operations and shared emission utility."""

    @staticmethod
    def get_event(event_id: uuid.UUID | str) -> Event:
        """Retrieve a single event by ID or raise Event.DoesNotExist."""
        return Event.objects.get(id=event_id)

    @staticmethod
    def list_events(filters: dict[str, Any] | None = None) -> QuerySet[Event]:
        """List events with optional filtering and newest-first ordering."""
        queryset = Event.objects.all()

        if filters:
            allowed = {
                "event_type",
                "source_service",
                "entity_type",
                "entity_id",
            }
            applied_filters = {
                key: value
                for key, value in filters.items()
                if key in allowed and value not in (None, "")
            }
            if applied_filters:
                queryset = queryset.filter(**applied_filters)

        return queryset.order_by("-occurred_at")
