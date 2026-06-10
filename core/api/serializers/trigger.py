from rest_framework import serializers

from core.models import Trigger


class TriggerSerializer(serializers.ModelSerializer):
    """Serializer for Trigger model."""

    class Meta:
        model = Trigger
        fields = [
            "id",
            "name",
            "description",
            "event_type",
            "entity_type",
            "conditions",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]
