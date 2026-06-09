"""API tests for Event read-only endpoints."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Event, EventSourceService

user_model = get_user_model()


def _create_event(**overrides):
    """Create an Event with overridable default values."""
    payload = {
        "event_type": "deal.stage_changed",
        "source_service": EventSourceService.CORE,
        "entity_type": "Deal",
        "entity_id": uuid.uuid4(),
        "after_state": {"stage": "qualified"},
    }
    payload.update(overrides)
    return Event.objects.create(**payload)


@pytest.mark.django_db
class TestEventApi:
    """Tests for /events/ and /events/{id}/ endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="event_admin",
            password="pass",
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="event_user",
            password="pass",
            is_staff=False,
        )

    def test_list_events_returns_200(self):
        """Staff/admin can list events."""
        _create_event()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/events/")

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1

    def test_list_events_filter_by_event_type(self):
        """List endpoint filters by event_type."""
        _create_event(event_type="task.completed", entity_type="Task")
        _create_event(event_type="deal.stage_changed", entity_type="Deal")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/events/", {"event_type": "task.completed"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["event_type"] == "task.completed"

    def test_list_events_filter_by_entity_type_and_id(self):
        """List endpoint filters by entity_type and entity_id."""
        target_id = uuid.uuid4()
        _create_event(entity_type="Deal", entity_id=target_id)
        _create_event(entity_type="Deal", entity_id=uuid.uuid4())
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            "/events/",
            {
                "entity_type": "Deal",
                "entity_id": str(target_id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["entity_type"] == "Deal"
        assert response.data["results"][0]["entity_id"] == str(target_id)

    def test_retrieve_event_returns_200(self):
        """Authenticated user can retrieve an event."""
        event = _create_event()
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(f"/events/{event.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(event.id)

    def test_retrieve_unknown_event_returns_404(self):
        """Retrieve returns 404 when event does not exist."""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(f"/events/{uuid.uuid4()}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_events_returns_405(self):
        """POST is not allowed on read-only event endpoint."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/events/",
            {
                "event_type": "deal.stage_changed",
                "source_service": "core",
                "entity_type": "Deal",
                "entity_id": str(uuid.uuid4()),
                "after_state": {"stage": "qualified"},
            },
            format="json",
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_event_returns_405(self):
        """DELETE is not allowed on read-only event endpoint."""
        event = _create_event()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f"/events/{event.id}/")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_events_unauthenticated_returns_403(self):
        """Unauthenticated list follows existing SessionAuthentication behavior."""
        _create_event()

        response = self.client.get("/events/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_events_non_admin_returns_403(self):
        """Authenticated non-admin user cannot list full event log."""
        _create_event()
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get("/events/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_events_admin_returns_200(self):
        """Authenticated admin user can list events."""
        _create_event()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/events/")

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_event_authenticated_non_admin_returns_200(self):
        """Authenticated non-admin user can retrieve single event."""
        event = _create_event()
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(f"/events/{event.id}/")

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_event_unauthenticated_returns_403(self):
        """Unauthenticated retrieve follows existing SessionAuthentication behavior."""
        event = _create_event()

        response = self.client.get(f"/events/{event.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
