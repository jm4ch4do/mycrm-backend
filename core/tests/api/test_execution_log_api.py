# pyright: reportRedeclaration=false
"""API tests for ExecutionLog read-only endpoints."""

import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Event, EventSourceService, Trigger, Workflow
from core.services.domain.execution_log_service import ExecutionLogService

user_model = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def execution_user():
    return user_model.objects.create_user(
        username="execution_user",
        password="pass",
        is_staff=False,
    )


@pytest.fixture
def admin_user():
    return user_model.objects.create_user(
        username="execution_admin",
        password="pass",
        is_staff=True,
    )


def _create_workflow(name: str = "Execution Workflow"):
    trigger = Trigger.objects.create(name=f"{name} Trigger", event_type="deal.stage_changed")
    return Workflow.objects.create(name=name, trigger=trigger)


def _create_event(**overrides):
    payload = {
        "event_type": "deal.stage_changed",
        "source_service": EventSourceService.CORE,
        "entity_type": "Deal",
        "entity_id": uuid.uuid4(),
        "after_state": {"stage": "qualified"},
    }
    payload.update(overrides)
    return Event.objects.create(**payload)


def _create_execution_log(workflow=None, event=None, **overrides):
    workflow = workflow or _create_workflow()
    event = event or _create_event()
    log = ExecutionLogService.create_execution_log(workflow, event, **overrides)
    return log


@pytest.mark.django_db
class TestExecutionLogApi:
    """Tests for /executions/ and /executions/{id}/ endpoints."""

    def test_list_executions_returns_200(self, api_client, admin_user):
        """Admin user can list execution logs."""
        _create_execution_log()
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/executions/")

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1

    def test_list_executions_filter_by_workflow(self, api_client, admin_user):
        """List endpoint filters by workflow."""
        workflow_1 = _create_workflow("Workflow One")
        workflow_2 = _create_workflow("Workflow Two")
        event = _create_event()
        _create_execution_log(workflow_1, event)
        _create_execution_log(workflow_2, event)
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/executions/", {"workflow": str(workflow_1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["workflow"]["id"] == str(workflow_1.id)

    def test_list_executions_filter_by_status(self, api_client, admin_user):
        """List endpoint filters by status."""
        pending_log = _create_execution_log()
        running_log = _create_execution_log()
        ExecutionLogService.mark_running(running_log)
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/executions/", {"status": "running"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == str(running_log.id)
        assert pending_log.id != running_log.id

    def test_list_executions_orders_newest_first(self, api_client, admin_user):
        """List endpoint returns execution logs ordered by started_at descending."""
        older = _create_execution_log()
        older.started_at = timezone.now() - timedelta(minutes=5)
        older.save(update_fields=["started_at"])
        newer = _create_execution_log()
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/executions/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == str(newer.id)
        assert response.data["results"][1]["id"] == str(older.id)

    def test_retrieve_execution_admin_returns_200(self, api_client, admin_user):
        """Admin user can retrieve a single execution log."""
        execution_log = _create_execution_log()
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(f"/executions/{execution_log.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(execution_log.id)
        assert isinstance(response.data["logs"], list)

    def test_retrieve_execution_non_admin_returns_403(self, api_client, execution_user):
        """Non-admin users cannot retrieve execution logs."""
        execution_log = _create_execution_log()
        api_client.force_authenticate(user=execution_user)

        response = api_client.get(f"/executions/{execution_log.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_unknown_execution_returns_404(self, api_client, admin_user):
        """Retrieve returns 404 when execution log does not exist."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(f"/executions/{uuid.uuid4()}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_executions_returns_405(self, api_client, admin_user):
        """POST is not allowed on read-only execution endpoint."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post("/executions/", {}, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_execution_returns_405(self, api_client, admin_user):
        """DELETE is not allowed on read-only execution endpoint."""
        execution_log = _create_execution_log()
        api_client.force_authenticate(user=admin_user)

        response = api_client.delete(f"/executions/{execution_log.id}/")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_executions_unauthenticated_returns_401(self, api_client):
        """Unauthenticated access is rejected by BasicAuthentication."""
        _create_execution_log()

        response = api_client.get("/executions/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_executions_non_admin_returns_403(self, api_client, execution_user):
        """Non-admin authenticated users cannot list execution logs."""
        _create_execution_log()
        api_client.force_authenticate(user=execution_user)

        response = api_client.get("/executions/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_executions_admin_returns_200(self, api_client, admin_user):
        """Admin authenticated users can list execution logs."""
        _create_execution_log()
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/executions/")

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_execution_unauthenticated_returns_401(self, api_client):
        """Unauthenticated retrieval is rejected by BasicAuthentication."""
        execution_log = _create_execution_log()

        response = api_client.get(f"/executions/{execution_log.id}/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED