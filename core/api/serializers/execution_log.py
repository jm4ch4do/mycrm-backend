"""Serializer for execution log records."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Event, ExecutionLog, Workflow


class _WorkflowNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ["id", "name"]


class _EventNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "event_type"]


class _UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class ExecutionLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for ExecutionLog model."""

    workflow = _WorkflowNestedSerializer(read_only=True)
    event = _EventNestedSerializer(read_only=True)
    created_by = _UserNestedSerializer(read_only=True)

    class Meta:
        model = ExecutionLog
        fields = [
            "id",
            "workflow",
            "event",
            "status",
            "started_at",
            "finished_at",
            "logs",
            "created_at",
            "created_by",
        ]
        read_only_fields = fields