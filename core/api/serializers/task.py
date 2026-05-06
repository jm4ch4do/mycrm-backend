from rest_framework import serializers

from core.models import Account, Contact, Deal, Task
from core.services.domain.task_service import TaskService


class TaskSerializer(serializers.ModelSerializer):
    """Flat serializer for Task — Activity fields are inlined."""

    # ── Activity fields ──────────────────────────────────────────────────
    activity_id = serializers.UUIDField(source="activity.id", read_only=True)
    type = serializers.CharField(source="activity.type", read_only=True)
    title = serializers.CharField(source="activity.title", max_length=255)
    description = serializers.CharField(
        source="activity.description",
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    owner_user = serializers.PrimaryKeyRelatedField(
        source="activity.owner_user", read_only=True
    )
    account = serializers.PrimaryKeyRelatedField(
        source="activity.account",
        queryset=Account.objects.all(),
        required=False,
        allow_null=True,
    )
    contact = serializers.PrimaryKeyRelatedField(
        source="activity.contact",
        queryset=Contact.objects.all(),
        required=False,
        allow_null=True,
    )
    deal = serializers.PrimaryKeyRelatedField(
        source="activity.deal",
        queryset=Deal.objects.all(),
        required=False,
        allow_null=True,
    )
    due_at = serializers.DateTimeField(
        source="activity.due_at", required=False, allow_null=True
    )
    completed_at = serializers.DateTimeField(
        source="activity.completed_at", read_only=True
    )
    activity_status = serializers.CharField(source="activity.status", read_only=True)
    is_invalid = serializers.BooleanField(source="activity.is_invalid", read_only=True)
    created_at = serializers.DateTimeField(source="activity.created_at", read_only=True)
    updated_at = serializers.DateTimeField(source="activity.updated_at", read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(
        source="activity.created_by", read_only=True
    )
    updated_by = serializers.PrimaryKeyRelatedField(
        source="activity.updated_by", read_only=True
    )

    # ── Task-own computed property ───────────────────────────────────────
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "activity_id",
            "type",
            "title",
            "description",
            "owner_user",
            "account",
            "contact",
            "deal",
            "due_at",
            "completed_at",
            "activity_status",
            "is_invalid",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "priority",
            "category",
            "estimated_duration_minutes",
            "state",
            "is_overdue",
        ]
        read_only_fields = ["id", "is_overdue"]

    def validate(self, attrs):
        """At least one of account, contact, or deal must be set."""
        activity_attrs = attrs.get("activity", {})
        instance = self.instance
        existing_activity = getattr(instance, "activity", None)

        def resolve(field):
            return activity_attrs.get(field, getattr(existing_activity, field, None))

        if not any([resolve("account"), resolve("contact"), resolve("deal")]):
            raise serializers.ValidationError(
                "At least one of account, contact, or deal must be set."
            )
        return attrs

    def create(self, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        return TaskService.create_task(
            {**activity_data, **validated_data}, request.user
        )

    def update(self, instance, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        return TaskService.update_task(
            instance, {**activity_data, **validated_data}, request.user
        )
