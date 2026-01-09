from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
            "is_authenticated",
        ]

    is_authenticated = serializers.SerializerMethodField()

    def get_is_authenticated(self, obj):
        return obj.is_authenticated
