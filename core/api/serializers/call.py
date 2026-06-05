from rest_framework import serializers

from core.models import Account, Call, CallOutcome, Contact, Deal
from core.services.domain.call_service import CallService


class CallSerializer(serializers.ModelSerializer):
    """Flat serializer for Call — Activity fields are inlined."""

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

    class Meta:
        model = Call
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
            "direction",
            "outcome",
            "phone_number",
            "duration_seconds",
            "summary",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        return CallService.create_call(
            {**activity_data, **validated_data}, request.user
        )

    def update(self, instance, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        try:
            return CallService.update_call(
                instance, {**activity_data, **validated_data}, request.user
            )
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc


class CallCompleteSerializer(serializers.Serializer):
    """Serializer for the complete_call action."""

    outcome = serializers.ChoiceField(choices=CallOutcome.choices)
    summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    duration_seconds = serializers.IntegerField(required=False, allow_null=True, min_value=0)
