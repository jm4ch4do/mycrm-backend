"""Unit tests for UserProfile model."""

import pytest
from django.contrib.auth import get_user_model

from core.models import UserProfile, UserRole
from core.signals import create_user_profile

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileCreation:
    """Test UserProfile model creation."""

    def test_create_profile_linked_to_user(self):
        """UserProfile is linked to its User after auto-creation."""
        user = User.objects.create_user(username="profileuser", password="pass")
        assert user.profile.user == user

    def test_role_defaults_to_none(self):
        """role defaults to None when not specified."""
        user = User.objects.create_user(username="noroleuser", password="pass")
        assert user.profile.role is None

    @pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES])
    def test_role_accepts_all_valid_values(self, role):
        """role accepts all UserRole values."""
        user = User.objects.create_user(username=f"{role}user", password="pass")
        user.profile.role = role
        user.profile.save()
        user.profile.refresh_from_db()
        assert user.profile.role == role

    def test_str_representation(self):
        """__str__ includes username and role, or 'no role' when None."""
        user = User.objects.create_user(username="struser", password="pass")
        user.profile.role = UserRole.SALES
        user.profile.save()
        assert "struser" in str(user.profile)
        assert "sales" in str(user.profile)

        user.profile.role = None
        user.profile.save()
        assert "no role" in str(user.profile)


@pytest.mark.django_db
class TestUserProfileSignal:
    """Test UserProfile auto-creation via post_save signal."""

    def test_profile_auto_created_on_user_save(self):
        """UserProfile is auto-created when a new User is saved."""
        user = User.objects.create_user(username="signaluser", password="pass")
        assert UserProfile.objects.filter(user=user).exists()

    def test_signal_does_not_fire_on_user_update(self):
        """Updating a User does not create a duplicate profile."""
        user = User.objects.create_user(username="updateuser", password="pass")
        user.first_name = "Updated"
        user.save()
        assert UserProfile.objects.filter(user=user).count() == 1

    def test_get_or_create_prevents_duplicate_profiles(self):
        """get_or_create ensures no duplicate profile even if signal fires twice."""
        user = User.objects.create_user(username="idempotentuser", password="pass")
        create_user_profile(sender=User, instance=user, created=True)
        assert UserProfile.objects.filter(user=user).count() == 1
