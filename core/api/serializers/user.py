from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    is_authenticated = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
            "is_authenticated",
            "role",
        ]

    def get_is_authenticated(self, obj):
        return obj.is_authenticated

    def get_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.role if profile else None


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "role",
        ]

    def get_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.role if profile else None
