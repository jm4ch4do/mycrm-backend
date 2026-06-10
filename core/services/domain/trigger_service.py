"""Business logic service for Trigger model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from core.models import Trigger

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


def _validate_event_type(event_type: str) -> str:
    """Validate and normalize event type as a non-empty dot-notation string."""
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError("event_type is required.")

    value = event_type.strip()
    if "." not in value:
        raise ValueError("event_type must use dot-notation (e.g. 'deal.updated').")

    parts = value.split(".")
    if any(not part.strip() for part in parts):
        raise ValueError("event_type must use dot-notation (e.g. 'deal.updated').")

    return value


def _resolve_payload_value(payload: dict[str, Any], dotted_path: str) -> Any:
    """Resolve nested payload values by dot path; return None when missing."""
    value: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _conditions_match(conditions: dict[str, Any] | None, payload: dict[str, Any]) -> bool:
    """Return True when all condition key-paths match exactly in payload."""
    if not conditions:
        return True

    if not isinstance(conditions, dict):
        return False

    for key, expected in conditions.items():
        if _resolve_payload_value(payload, key) != expected:
            return False

    return True


class TriggerService:
    """Service layer for Trigger business logic."""

    @staticmethod
    def list_triggers(filters: dict[str, Any] | None = None) -> QuerySet[Trigger]:
        """List non-deleted triggers with optional filtering."""
        queryset = Trigger.objects.filter(is_invalid=False)

        if filters:
            allowed = {
                "event_type",
                "entity_type",
                "is_active",
            }
            applied_filters = {
                key: value
                for key, value in filters.items()
                if key in allowed and value not in (None, "")
            }
            if applied_filters:
                queryset = queryset.filter(**applied_filters)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_trigger(trigger_id: str) -> Trigger:
        """Retrieve a non-deleted trigger by ID."""
        return get_object_or_404(Trigger, id=trigger_id, is_invalid=False)

    @staticmethod
    @transaction.atomic
    def create_trigger(data: dict[str, Any], user: User) -> Trigger:
        """Create a trigger and set audit fields."""
        payload = data.copy()
        payload["event_type"] = _validate_event_type(payload.get("event_type", ""))

        return Trigger.objects.create(
            created_by=user,
            updated_by=user,
            **payload,
        )

    @staticmethod
    @transaction.atomic
    def update_trigger(trigger: Trigger, data: dict[str, Any], user: User) -> Trigger:
        """Update mutable trigger fields and set updated_by."""
        payload = data.copy()

        for field in ["id", "created_at", "created_by", "is_invalid"]:
            payload.pop(field, None)

        if "event_type" in payload:
            payload["event_type"] = _validate_event_type(payload["event_type"])

        payload["updated_by"] = user
        for field, value in payload.items():
            setattr(trigger, field, value)

        trigger.save()
        return trigger

    @staticmethod
    @transaction.atomic
    def delete_trigger(trigger: Trigger, user: User) -> Trigger:
        """Soft-delete a trigger by marking it invalid and inactive."""
        trigger.is_invalid = True
        trigger.is_active = False
        trigger.updated_by = user
        trigger.save()
        return trigger

    @staticmethod
    def get_matching_triggers(
        event_type: str,
        entity_type: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[Trigger]:
        """Return active, non-deleted triggers that match event and payload."""
        normalized_event_type = _validate_event_type(event_type)
        queryset = Trigger.objects.filter(
            event_type=normalized_event_type,
            is_active=True,
            is_invalid=False,
        )

        if entity_type not in (None, ""):
            queryset = queryset.filter(
                Q(entity_type=entity_type) | Q(entity_type__isnull=True) | Q(entity_type="")
            )

        event_payload = payload or {}
        return [
            trigger
            for trigger in queryset.order_by("-created_at")
            if _conditions_match(trigger.conditions, event_payload)
        ]
