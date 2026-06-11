from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Action
from core.services.domain.action_service import ActionService


class ActionUserNestedSerializer(serializers.ModelSerializer):
    """Read-only subset for action audit user details."""

    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class ActionSerializer(serializers.ModelSerializer):
    """Serializer for Action model."""

    created_by = ActionUserNestedSerializer(read_only=True)
    updated_by = ActionUserNestedSerializer(read_only=True)

    class Meta:
        model = Action
        fields = [
            "id",
            "name",
            "description",
            "action_type",
            "parameters",
            "retry_policy",
            "timeout_seconds",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        return ActionService.create_action(validated_data, created_by=request.user)

    def update(self, instance, validated_data):
        request = self.context["request"]
        return ActionService.update_action(instance, validated_data, updated_by=request.user)