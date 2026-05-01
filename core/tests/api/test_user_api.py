"""API tests for user-related serializers and endpoints."""

from typing import Optional
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.api.serializers.user import CurrentUserSerializer, UserSerializer
from core.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestCurrentUserSerializer:
    """Tests for CurrentUserSerializer."""

    def test_includes_role_field(self):
        """CurrentUserSerializer output includes role field."""
        user = User.objects.create_user(username="meuser", password="pass")
        data = CurrentUserSerializer(user).data
        assert "role" in data

    def test_role_is_none_when_not_set(self):
        """role is None when the profile has no role assigned."""
        user = User.objects.create_user(username="menorole", password="pass")
        data = CurrentUserSerializer(user).data
        assert data["role"] is None

    def test_role_reflects_profile_value(self):
        """role returns the value set on the UserProfile."""
        user = User.objects.create_user(username="mewithrole", password="pass")
        user.profile.role = UserRole.MANAGER
        user.profile.save()
        data = CurrentUserSerializer(user).data
        assert data["role"] == UserRole.MANAGER


@pytest.mark.django_db
class TestUserSerializer:
    """Tests for UserSerializer."""

    def test_exposes_required_fields(self):
        """UserSerializer exposes all required fields."""
        user = User.objects.create_user(
            username="listuser",
            email="list@example.com",
            first_name="First",
            last_name="Last",
            password="pass",
        )
        data = UserSerializer(user).data
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "is_active" in data
        assert "is_staff" in data
        assert "role" in data

    def test_role_is_none_when_not_set(self):
        """role is None when the profile has no role assigned."""
        user = User.objects.create_user(username="listnorole", password="pass")
        data = UserSerializer(user).data
        assert data["role"] is None

    def test_role_reflects_profile_value(self):
        """role returns the value set on the UserProfile."""
        user = User.objects.create_user(username="listwithrole", password="pass")
        user.profile.role = UserRole.SALES
        user.profile.save()
        data = UserSerializer(user).data
        assert data["role"] == UserRole.SALES


@pytest.mark.django_db
class TestUserListEndpoint:
    """Tests for GET /users/ endpoint."""

    client: Optional[APIClient]
    staff: Optional[object]
    regular: Optional[object]

    def setup_method(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username="staffuser", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(username="regularuser", password="pass")

    def test_authenticated_user_can_list_users(self):
        """Any authenticated user can GET /users/."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_user_gets_403(self):
        """Unauthenticated GET /users/ returns 403.

        SessionAuthentication has no WWW-Authenticate header, so DRF returns 403.
        """
        response = self.client.get("/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_contains_role_field(self):
        """GET /users/ response includes role for each user."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/users/")
        assert "role" in response.data["results"][0]


@pytest.mark.django_db
class TestUserRetrieveEndpoint:
    """Tests for GET /users/{id}/ endpoint."""

    client: Optional[APIClient]
    staff: Optional[object]
    regular: Optional[object]

    def setup_method(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username="staffuser2", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="regularuser2", password="pass"
        )

    def test_authenticated_user_can_retrieve_user(self):
        """Any authenticated user can GET /users/{id}/."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(f"/users/{self.staff.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "staffuser2"

    def test_unauthenticated_user_gets_403(self):
        """Unauthenticated GET /users/{id}/ returns 403.

        SessionAuthentication has no WWW-Authenticate header, so DRF returns 403.
        """
        response = self.client.get(f"/users/{self.regular.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_nonexistent_user_gets_404(self):
        """GET /users/999999/ returns 404."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/users/999999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserUpdateEndpoint:
    """Tests for PUT /users/{id}/ endpoint."""

    client: Optional[APIClient]
    staff: Optional[object]
    regular: Optional[object]

    def setup_method(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username="staffuser3", password="pass", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="regularuser3", password="pass"
        )

    def test_staff_can_update_user_role(self):
        """Staff user can PUT /users/{id}/ to update role."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.put(
            f"/users/{self.regular.id}/",
            {"role": UserRole.MANAGER},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.regular.profile.refresh_from_db()
        assert self.regular.profile.role == UserRole.MANAGER

    def test_non_staff_update_gets_403(self):
        """Non-staff user cannot PUT /users/{id}/."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.put(
            f"/users/{self.staff.id}/",
            {"role": UserRole.SALES},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_update_gets_403(self):
        """Unauthenticated PUT /users/{id}/ returns 403.

        SessionAuthentication has no WWW-Authenticate header, so DRF returns 403.
        """
        response = self.client.put(
            f"/users/{self.regular.id}/",
            {"role": UserRole.ADMIN},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
