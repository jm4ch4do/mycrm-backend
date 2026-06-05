from rest_framework import serializers

from core.models import Note
from core.services.domain.note_service import NoteService


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for Note model."""

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "body",
            "author",
            "account",
            "contact",
            "deal",
            "visibility",
            "is_pinned",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        return NoteService.create_note(validated_data, request.user)

    def update(self, instance, validated_data):
        request = self.context["request"]
        try:
            return NoteService.update_note(instance, validated_data, request.user)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc
