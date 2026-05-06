"""API tests for Activity endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Account, Activity, ActivityType

UserModel = get_user_model()


@pytest.mark.django_db
class TestActivityListCreate:
    """Tests for POST /activities/ and GET /activities/ endpoints."""

    def setup_method(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="activityuser", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Test Corp", owner_user=self.user
        )

    def test_create_activity_returns_201(self):
        """Test POST /activities/ returns 201 Created."""
        payload = {
            "type": ActivityType.TASK,
            "title": "Follow up",
            "account": str(self.account.id),
        }
        response = self.client.post("/activities/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Follow up"

    def test_create_activity_without_entity_reference_fails(self):
        """Test that creating an activity without any entity reference fails."""
        payload = {
            "type": ActivityType.TASK,
            "title": "Floating task",
        }
        response = self.client.post("/activities/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least one" in str(response.data).lower()

    def test_list_activities_returns_200(self):
        """Test GET /activities/ returns 200 with results."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Listed",
            owner_user=self.user,
            account=self.account,
        )
        response = self.client.get("/activities/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_list_excludes_soft_deleted(self):
        """Test that soft-deleted activities are excluded from list."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Deleted",
            owner_user=self.user,
            account=self.account,
            is_invalid=True,
        )
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Active",
            owner_user=self.user,
            account=self.account,
        )
        response = self.client.get("/activities/")
        titles = [item["title"] for item in response.data["results"]]
        assert "Active" in titles
        assert "Deleted" not in titles

    def test_create_activity_missing_title_fails(self):
        """Test that missing title returns 400."""
        payload = {
            "type": ActivityType.TASK,
            "account": str(self.account.id),
        }
        response = self.client.post("/activities/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data


@pytest.mark.django_db
class TestActivityRetrieveUpdateDelete:
    """Tests for GET/PUT/PATCH/DELETE /activities/{id}/."""

    def setup_method(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="activityuser2", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            name="Test Corp", owner_user=self.user
        )
        self.activity = Activity.objects.create(
            type=ActivityType.TASK,
            title="Test Activity",
            owner_user=self.user,
            account=self.account,
        )

    def test_retrieve_activity_returns_200(self):
        """Test GET /activities/{id}/ returns 200."""
        response = self.client.get(f"/activities/{self.activity.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(self.activity.id)

    def test_partial_update_activity_returns_200(self):
        """Test PATCH /activities/{id}/ updates allowed fields."""
        response = self.client.patch(
            f"/activities/{self.activity.id}/",
            {"title": "Updated Title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"

    def test_soft_delete_activity_returns_204(self):
        """Test DELETE /activities/{id}/ soft-deletes and returns 204."""
        response = self.client.delete(f"/activities/{self.activity.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.activity.refresh_from_db()
        assert self.activity.is_invalid is True

    def test_unauthenticated_request_returns_403(self):
        """Test that unauthenticated requests are rejected with 403."""
        unauth_client = APIClient()
        response = unauth_client.get(f"/activities/{self.activity.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
