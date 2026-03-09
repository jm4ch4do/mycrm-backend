from rest_framework import serializers

from core.models import Deal, DealContactAssoc


class DealSerializer(serializers.ModelSerializer):
    """Serializer for Deal model."""

    class Meta:
        model = Deal
        fields = [
            "id",
            "name",
            "account",
            "amount",
            "currency",
            "expected_close_date",
            "probability",
            "stage",
            "status",
            "loss_reason",
            "lead_source",
            "owner_user",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "closed_at",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class DealContactAssocSerializer(serializers.ModelSerializer):
    """Serializer for DealContactAssoc join table."""

    class Meta:
        model = DealContactAssoc
        fields = [
            "deal",
            "contact",
            "created_at",
        ]
        read_only_fields = [
            "deal",
            "created_at",
        ]
