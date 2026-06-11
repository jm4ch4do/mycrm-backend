from rest_framework import serializers
from django.contrib.auth import get_user_model

from core.models import Action, Trigger, Workflow, WorkflowStep
from core.services.domain.workflow_service import WorkflowService


class _ActionNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ["id", "name"]


class _TriggerNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger
        fields = ["id", "name"]


class _UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class WorkflowStepSerializer(serializers.ModelSerializer):
    """Read serializer for WorkflowStep entries."""

    action = _ActionNestedSerializer(read_only=True)

    class Meta:
        model = WorkflowStep
        fields = ["id", "action", "step_order"]


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow model."""

    trigger = _TriggerNestedSerializer(read_only=True)
    trigger_id = serializers.PrimaryKeyRelatedField(
        queryset=Trigger.objects.filter(is_invalid=False),
        source="trigger",
        write_only=True,
    )
    steps = WorkflowStepSerializer(source="workflow_steps", many=True, read_only=True)
    created_by = _UserNestedSerializer(read_only=True)
    updated_by = _UserNestedSerializer(read_only=True)

    class Meta:
        model = Workflow
        fields = [
            "id",
            "name",
            "description",
            "trigger",
            "trigger_id",
            "steps",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "steps",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        return WorkflowService.create_workflow(validated_data, created_by=request.user)

    def update(self, instance, validated_data):
        request = self.context["request"]
        return WorkflowService.update_workflow(instance, validated_data, updated_by=request.user)
