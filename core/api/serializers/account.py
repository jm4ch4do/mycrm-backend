from rest_framework import serializers

from core.models import Account


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Account model.
    
    Leverages model field validators for most validation.
    Custom validators below are examples for cross-field or complex logic.
    """

    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "account_number",
            "status",
            "type",
            "industry",
            "company_size",
            "annual_revenue",
            "website",
            "description",
            "owner_user",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "billing_street",
            "billing_city",
            "billing_state",
            "billing_country",
            "billing_postal_code",
            "shipping_street",
            "shipping_city",
            "shipping_state",
            "shipping_country",
            "shipping_postal_code",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def validate_annual_revenue(self, value):
        """Ensure revenue is non-negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Annual revenue must be a positive number."
            )
        return value

    def validate_account_number(self, value):
        """Ensure account_number is unique (excluding current instance)."""
        if value:
            queryset = Account.objects.filter(account_number=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    "An account with this account number already exists."
                )
        return value
