"""Unit tests for ExecutionLogService."""

from uuid import UUID

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    Event,
    EventSourceService,
    ExecutionLog,
    ExecutionStatus,
    Trigger,
    Workflow,
)
from core.services.domain.execution_log_service import ExecutionLogService


@pytest.fixture(name="user")
def user_fixture(db):  # pylint: disable=unused-argument
    """Create a test user."""
    user_model = get_user_model()
    return user_model.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture(name="trigger")
def trigger_fixture(db):  # pylint: disable=unused-argument
    """Create a test trigger."""
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
    """Create an event for execution logs."""
    return Event.objects.create(
        event_type="deal.stage_changed",
        source_service=EventSourceService.CORE,
        entity_type="deal",
        entity_id=UUID("00000000-0000-0000-0000-000000000001"),
        after_state={"stage": "qualified"},
        created_by=user,
    )


@pytest.mark.django_db
class TestExecutionLogServiceCreate:
    """Tests for ExecutionLogService.create_execution_log()."""

    def test_create_execution_log_sets_pending_status(self, workflow, event):
        """create_execution_log() sets status to pending."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        assert execution_log.status == ExecutionStatus.PENDING

    def test_create_execution_log_sets_created_by(self, workflow, event, user):
        """create_execution_log() stores the triggering user when provided."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event, user)

        assert execution_log.created_by == user

    def test_create_execution_log_does_not_open_its_own_transaction(self, workflow, event):
        """create_execution_log() persists directly and returns a saved object."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        assert ExecutionLog.objects.filter(id=execution_log.id).exists()


@pytest.mark.django_db
class TestExecutionLogServiceUpdate:
    """Tests for write-path ExecutionLogService methods."""

    def test_mark_running_updates_status(self, workflow, event):
        """mark_running() updates the execution status."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        updated = ExecutionLogService.mark_running(execution_log)

        assert updated.status == ExecutionStatus.RUNNING

    def test_append_step_log_adds_to_list(self, workflow, event):
        """append_step_log() adds a new step entry."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        updated = ExecutionLogService.append_step_log(
            execution_log,
            {
                "step_order": 1,
                "action_id": "11111111-1111-1111-1111-111111111111",
                "action_type": "create_task",
                "status": "success",
                "result": {},
                "error": None,
                "executed_at": timezone.now().isoformat(),
            },
        )

        assert len(updated.logs) == 1

    def test_append_step_log_does_not_overwrite(self, workflow, event):
        """append_step_log() preserves existing step entries."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)
        ExecutionLogService.append_step_log(
            execution_log,
            {
                "step_order": 1,
                "action_id": "11111111-1111-1111-1111-111111111111",
                "action_type": "create_task",
                "status": "success",
                "result": {},
                "error": None,
                "executed_at": timezone.now().isoformat(),
            },
        )

        updated = ExecutionLogService.append_step_log(
            execution_log,
            {
                "step_order": 2,
                "action_id": "22222222-2222-2222-2222-222222222222",
                "action_type": "add_note",
                "status": "failed",
                "result": {},
                "error": "boom",
                "executed_at": timezone.now().isoformat(),
            },
        )

        assert len(updated.logs) == 2
        assert updated.logs[0]["step_order"] == 1


@pytest.mark.django_db
class TestExecutionLogServiceFinalize:
    """Tests for ExecutionLogService.finalize()."""

    def test_finalize_success_sets_status_and_finished_at(self, workflow, event):
        """finalize() sets a success status and finished_at."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        finalized = ExecutionLogService.finalize(execution_log, ExecutionStatus.SUCCESS)

        assert finalized.status == ExecutionStatus.SUCCESS
        assert finalized.finished_at is not None

    def test_finalize_failed_sets_status_and_finished_at(self, workflow, event):
        """finalize() sets a failed status and finished_at."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        finalized = ExecutionLogService.finalize(execution_log, ExecutionStatus.FAILED)

        assert finalized.status == ExecutionStatus.FAILED
        assert finalized.finished_at is not None

    def test_finalize_partial_sets_status_and_finished_at(self, workflow, event):
        """finalize() accepts partial status and sets finished_at."""
        execution_log = ExecutionLogService.create_execution_log(workflow, event)

        finalized = ExecutionLogService.finalize(execution_log, ExecutionStatus.PARTIAL)

        assert finalized.status == ExecutionStatus.PARTIAL
        assert finalized.finished_at is not None


@pytest.mark.django_db
class TestExecutionLogServiceRead:
    """Tests for read-path ExecutionLogService methods."""

    def test_get_execution_log_raises_for_unknown_id(self):
        """get_execution_log() raises for unknown IDs."""
        with pytest.raises(ExecutionLog.DoesNotExist):
            ExecutionLogService.get_execution_log("00000000-0000-0000-0000-000000000000")

    def test_list_execution_logs_filters_by_workflow(self, workflow, event):
        """list_execution_logs() filters by workflow."""
        other_trigger = Trigger.objects.create(name="Other Trigger", event_type="deal.created")
        other_workflow = Workflow.objects.create(
            name="Other Workflow",
            trigger=other_trigger,
        )

        matched = ExecutionLogService.create_execution_log(workflow, event)
        ExecutionLogService.create_execution_log(other_workflow, event)

        queryset = ExecutionLogService.list_execution_logs({"workflow": workflow})

        assert list(queryset) == [matched]

    def test_list_execution_logs_filters_by_status(self, workflow, event):
        """list_execution_logs() filters by status."""
        pending_log = ExecutionLogService.create_execution_log(workflow, event)
        running_log = ExecutionLogService.create_execution_log(workflow, event)
        ExecutionLogService.mark_running(running_log)

        queryset = ExecutionLogService.list_execution_logs({"status": ExecutionStatus.RUNNING})

        assert list(queryset) == [running_log]
        assert pending_log not in queryset
