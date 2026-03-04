from rest_framework import serializers

from core.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model.

    Leverages model field validators for most validation.
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "mobile",
            "job_title",
            "department",
            "role",
            "seniority",
            "account",
            "owner_user",
            "primary_contact",
            "preferred_channel",
            "opt_in_email",
            "opt_in_sms",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "is_invalid",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def validate(self, attrs):
        """Validate email uniqueness per account."""
        email = attrs.get("email")
        account = attrs.get("account")

        if email and account:
            queryset = Contact.objects.filter(account=account, email=email)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "email": "A contact with this email already exists for this account."
                    }
                )

        return attrs
