"""API tests for Action endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Action, ActionType

user_model = get_user_model()

VALID_PARAMETERS = {
    "title": "Follow up on qualification",
    "due_days_from_now": 2,
}


@pytest.fixture
def action(db, test_user):
    return Action.objects.create(
        name="Create Qualification Task",
        action_type=ActionType.CREATE_TASK,
        parameters=VALID_PARAMETERS,
        created_by=test_user,
        updated_by=test_user,
    )


@pytest.mark.django_db
class TestActionApiCrud:
    """CRUD tests for /actions/ endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="action_admin",
            password="pass",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_action_returns_201(self):
        response = self.client.post(
            "/actions/",
            {
                "name": "New Action",
                "action_type": ActionType.CREATE_TASK,
                "parameters": VALID_PARAMETERS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Action"

    def test_create_action_invalid_type_returns_400(self):
        response = self.client.post(
            "/actions/",
            {
                "name": "Invalid Action",
                "action_type": "invalid_type",
                "parameters": VALID_PARAMETERS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_actions_returns_200(self, action):
        response = self.client.get("/actions/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

    def test_retrieve_action_returns_200(self, action):
        response = self.client.get(f"/actions/{action.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(action.id)

    def test_update_action_returns_200(self, action):
        response = self.client.patch(
            f"/actions/{action.id}/",
            {"name": "Updated Action"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Action"

    def test_delete_action_returns_204(self, action):
        response = self.client.delete(f"/actions/{action.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_deleted_action_returns_404(self, action):
        self.client.delete(f"/actions/{action.id}/")

        response = self.client.get(f"/actions/{action.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_dry_run_valid_parameters_returns_200(self, action):
        response = self.client.post(
            f"/actions/{action.id}/dry_run/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

    def test_dry_run_invalid_parameters_returns_400(self, test_user):
        invalid_action = Action.objects.create(
            name="Broken Action",
            action_type=ActionType.CREATE_TASK,
            parameters={"unexpected_field": 999},
            created_by=test_user,
            updated_by=test_user,
        )

        response = self.client.post(
            f"/actions/{invalid_action.id}/dry_run/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestActionApiPermissions:
    """Permission tests for /actions/ endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="action_perm_admin",
            password="pass",
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="action_perm_user",
            password="pass",
            is_staff=False,
        )

    def test_list_actions_unauthenticated_returns_401(self):
        response = self.client.get("/actions/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_actions_non_admin_returns_403(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get("/actions/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_action_admin_returns_201(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/actions/",
            {
                "name": "Allowed Action",
                "action_type": ActionType.CREATE_TASK,
                "parameters": VALID_PARAMETERS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_dry_run_non_admin_returns_403(self, action):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(
            f"/actions/{action.id}/dry_run/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN