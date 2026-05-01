"""Unit tests for UserProfile model."""

import pytest
from django.contrib.auth import get_user_model

from core.models import UserProfile, UserRole

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileCreation:
    """Test UserProfile model creation."""

    def test_create_profile_linked_to_user(self):
        """UserProfile can be created and linked to a User."""
        user = User.objects.create_user(username="profileuser", password="pass")
        profile = UserProfile.objects.create(user=user)
        assert profile.user == user

    def test_role_defaults_to_none(self):
        """role defaults to None when not specified."""
        user = User.objects.create_user(username="noroleuser", password="pass")
        profile = UserProfile.objects.create(user=user)
        assert profile.role is None

    @pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES])
    def test_role_accepts_all_valid_values(self, role):
        """role accepts all UserRole values."""
        user = User.objects.create_user(username=f"{role}user", password="pass")
        profile = UserProfile.objects.create(user=user, role=role)
        assert profile.role == role

    def test_str_representation(self):
        """__str__ includes username and role, or 'no role' when None."""
        user = User.objects.create_user(username="struser", password="pass")
        profile_with_role = UserProfile.objects.create(user=user, role=UserRole.SALES)
        assert "struser" in str(profile_with_role)
        assert "sales" in str(profile_with_role)

        profile_with_role.role = None
        profile_with_role.save()
        assert "no role" in str(profile_with_role)
