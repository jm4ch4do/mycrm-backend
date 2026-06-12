"""Unit tests for the ExecutionLog model."""

from datetime import timedelta
from uuid import UUID

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    Event,
    EventSourceService,
    ExecutionLog,
    Trigger,
    Workflow,
)


@pytest.fixture(name="user")
def user_fixture(db):  # pylint: disable=unused-argument
    """Create a user for audit fields."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="workflow-audit-user",
        email="workflow-audit-user@example.com",
        password="testpass123",
    )


@pytest.fixture(name="trigger")
def trigger_fixture(db):  # pylint: disable=unused-argument
    """Create a trigger for workflow attachment."""
    return Trigger.objects.create(
        name="Deal Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture(name="workflow")
def workflow_fixture(db, trigger, user):  # pylint: disable=unused-argument,redefined-outer-name
    """Create a workflow for execution logs."""
    return Workflow.objects.create(
        name="Qualify Deal Workflow",
        trigger=trigger,
        created_by=user,
        updated_by=user,
    )


@pytest.fixture(name="event")
def event_fixture(db, user):  # pylint: disable=unused-argument,redefined-outer-name
    """Create an event that triggered execution."""
    return Event.objects.create(
        event_type="deal.stage_changed",
        source_service=EventSourceService.CORE,
        entity_type="deal",
        entity_id=UUID("00000000-0000-0000-0000-000000000001"),
        after_state={"stage": "qualified"},
        created_by=user,
    )


@pytest.mark.django_db
class TestExecutionLogModel:
    """Tests for ExecutionLog model fields, defaults, and behavior."""

    def test_execution_log_str_returns_workflow_and_status(self, workflow, event):
        """__str__ returns the workflow name and status."""
        execution_log = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )

        assert str(execution_log) == "Qualify Deal Workflow (pending)"

    def test_execution_log_requires_workflow(self, event):
        """workflow is required."""
        execution_log = ExecutionLog(event=event)

        with pytest.raises((ValidationError, ValueError)):
            execution_log.full_clean()

    def test_execution_log_requires_event(self, workflow):
        """event is required."""
        execution_log = ExecutionLog(workflow=workflow)

        with pytest.raises((ValidationError, ValueError)):
            execution_log.full_clean()

    def test_execution_log_status_defaults_pending(self, workflow, event):
        """status defaults to pending."""
        execution_log = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )

        assert execution_log.status == "pending"

    def test_execution_log_logs_defaults_empty_list(self, workflow, event):
        """logs defaults to an empty list."""
        execution_log = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )

        assert execution_log.logs == []

    def test_execution_log_finished_at_nullable(self, workflow, event):
        """finished_at can remain null until execution completes."""
        execution_log = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )

        assert execution_log.finished_at is None

    def test_execution_log_ordering_is_newest_first(self, workflow, event):
        """Meta ordering returns newest execution logs first."""
        older = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )
        older.started_at = timezone.now() - timedelta(minutes=5)
        older.save(update_fields=["started_at"])

        newer = ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
        )

        logs = list(ExecutionLog.objects.all())

        assert logs[0] == newer
        assert logs[1] == older