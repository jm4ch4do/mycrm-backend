from rest_framework import serializers

from core.models import (
    Account,
    Contact,
    Deal,
    Meeting,
    MeetingContactAssoc,
    MeetingOutcome,
    MeetingUserAssoc,
)
from core.services.domain.meeting_service import MeetingService


class MeetingSerializer(serializers.ModelSerializer):
    """Flat serializer for Meeting — Activity fields are inlined."""

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
        model = Meeting
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
            "start_time",
            "end_time",
            "location",
            "meeting_url",
            "outcome",
            "summary",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        return MeetingService.create_meeting(
            {**activity_data, **validated_data}, request.user
        )

    def update(self, instance, validated_data):
        activity_data = validated_data.pop("activity", {})
        request = self.context["request"]
        try:
            return MeetingService.update_meeting(
                instance, {**activity_data, **validated_data}, request.user
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class MeetingCompleteSerializer(serializers.Serializer):
    """Serializer for the complete meeting action."""

    outcome = serializers.ChoiceField(choices=MeetingOutcome.choices)
    summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class MeetingUserAssocSerializer(serializers.ModelSerializer):
    """Serializer for adding/removing user participants."""

    class Meta:
        model = MeetingUserAssoc
        fields = ["meeting", "user", "created_at"]
        read_only_fields = ["meeting", "created_at"]


class MeetingContactAssocSerializer(serializers.ModelSerializer):
    """Serializer for adding/removing contact participants."""

    class Meta:
        model = MeetingContactAssoc
        fields = ["meeting", "contact", "created_at"]
        read_only_fields = ["meeting", "created_at"]
