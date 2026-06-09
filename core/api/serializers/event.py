"""Serializer for immutable Event records."""

from rest_framework import serializers

from core.models import Event


class EventCreatedBySerializer(serializers.Serializer):
    """Read-only subset for event.created_by user details."""

    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)


class EventSerializer(serializers.ModelSerializer):
    """Read-only serializer for Event model."""

    created_by = EventCreatedBySerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "event_type",
            "source_service",
            "entity_type",
            "entity_id",
            "before_state",
            "after_state",
            "metadata",
            "occurred_at",
            "emitted_by_user_id",
            "created_at",
            "created_by",
        ]
        read_only_fields = fields
