from rest_framework import serializers

from core.models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model."""

    class Meta:
        model = Activity
        fields = [
            "id",
            "type",
            "title",
            "description",
            "owner_user",
            "account",
            "contact",
            "deal",
            "status",
            "due_at",
            "completed_at",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "owner_user",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def validate(self, attrs):
        """At least one of account, contact, or deal must be set."""
        # On partial update, merge with existing instance values
        instance = self.instance
        account = attrs.get("account", getattr(instance, "account", None))
        contact = attrs.get("contact", getattr(instance, "contact", None))
        deal = attrs.get("deal", getattr(instance, "deal", None))

        if not any([account, contact, deal]):
            raise serializers.ValidationError(
                "At least one of account, contact, or deal must be set."
            )
        return attrs
