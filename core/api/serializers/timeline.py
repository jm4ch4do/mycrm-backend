"""Serializer for Timeline API — flat unified shape for all item types."""

from rest_framework import serializers


class TimelineItemSerializer(serializers.Serializer):
    """Read-only flat serializer for a single timeline item.

    Fields not applicable to a given type return null.
    """

    id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    body = serializers.CharField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True, allow_null=True)
    outcome = serializers.CharField(read_only=True, allow_null=True)
    direction = serializers.CharField(read_only=True, allow_null=True)
    start_time = serializers.DateTimeField(read_only=True, allow_null=True)
    due_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    owner_user = serializers.UUIDField(read_only=True, allow_null=True)
    author = serializers.UUIDField(read_only=True, allow_null=True)
    visibility = serializers.CharField(read_only=True, allow_null=True)
    is_pinned = serializers.BooleanField(read_only=True, allow_null=True)

    def create(self, validated_data):
        raise NotImplementedError("Timeline is read-only.")

    def update(self, instance, validated_data):
        raise NotImplementedError("Timeline is read-only.")
