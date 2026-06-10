from rest_framework import serializers

from core.models import Rule, Trigger
from core.services.domain.rule_service import RuleService


class _TriggerNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger
        fields = ["id", "name"]


class _UserNestedSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for Rule model."""

    # Read: nested objects
    trigger = _TriggerNestedSerializer(read_only=True)
    created_by = _UserNestedSerializer(read_only=True)
    updated_by = _UserNestedSerializer(read_only=True)

    # Write: accept UUID
    trigger_id = serializers.PrimaryKeyRelatedField(
        queryset=Trigger.objects.all(),
        source="trigger",
        write_only=True,
    )

    class Meta:
        model = Rule
        fields = [
            "id",
            "name",
            "description",
            "trigger",
            "trigger_id",
            "conditions",
            "evaluation_order",
            "is_active",
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
        return RuleService.create_rule(validated_data, created_by=request.user)

    def update(self, instance, validated_data):
        request = self.context["request"]
        return RuleService.update_rule(instance, validated_data, updated_by=request.user)
