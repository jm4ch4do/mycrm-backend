"""Unit tests for ActionService."""

from __future__ import annotations

import pytest

from core.models import Action, ActionType, Event, ExecutionLog, Trigger, Workflow
from core.services.domain.action_service import ActionService


@pytest.fixture
def trigger(db):
    """A minimal trigger for workflow attachment."""
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture
def workflow(trigger, test_user):
    """A workflow used to hang execution logs off action executions."""
    return Workflow.objects.create(
        name="Qualification Workflow",
        trigger=trigger,
        created_by=test_user,
        updated_by=test_user,
    )


@pytest.fixture
def event(deal):
    """A deal-targeted event used for action execution."""
    return Event.objects.create(
        event_type="deal.stage_changed",
        source_service="core",
        entity_type="deal",
        entity_id=deal.id,
        after_state={"stage": "qualified"},
    )


@pytest.fixture
def execution_log(workflow, event, test_user):
    """Execution log carrying workflow and user context."""
    return ExecutionLog.objects.create(
        workflow=workflow,
        event=event,
        triggered_by=test_user,
    )


@pytest.mark.django_db
class TestActionServiceWrite:
    """Tests for ActionService write operations."""

    def test_create_action_sets_created_by(self, test_user):
        """create_action() sets created_by and updated_by."""
        action = ActionService.create_action(
            {
                "name": "Create Qualification Task",
                "action_type": ActionType.CREATE_TASK,
                "parameters": {
                    "title": "Follow up on qualification",
                    "due_days_from_now": 2,
                },
            },
            created_by=test_user,
        )

        assert action.created_by == test_user
        assert action.updated_by == test_user

    def test_create_action_invalid_type_raises(self, test_user):
        """create_action() raises ValueError for unsupported action types."""
        with pytest.raises(ValueError, match="Unsupported action_type"):
            ActionService.create_action(
                {
                    "name": "Broken Action",
                    "action_type": "invalid_type",
                    "parameters": {"title": "x"},
                },
                created_by=test_user,
            )

    def test_update_action_sets_updated_by(self, test_user, test_user_2):
        """update_action() sets updated_by."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            parameters={"title": "Follow up on qualification"},
            created_by=test_user,
            updated_by=test_user,
        )

        updated = ActionService.update_action(
            action,
            {"name": "Updated Action"},
            updated_by=test_user_2,
        )

        assert updated.name == "Updated Action"
        assert updated.updated_by == test_user_2

    def test_delete_action_sets_is_invalid(self, test_user, test_user_2):
        """delete_action() soft-deletes the action."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            parameters={"title": "Follow up on qualification"},
            created_by=test_user,
            updated_by=test_user,
        )

        ActionService.delete_action(action, updated_by=test_user_2)

        action.refresh_from_db()
        assert action.is_invalid is True
        assert action.updated_by == test_user_2


@pytest.mark.django_db
class TestActionServiceRead:
    """Tests for ActionService read operations."""

    def test_get_action_raises_for_invalid(self, test_user):
        """get_action() raises Action.DoesNotExist for soft-deleted actions."""
        action = Action.objects.create(
            name="Deleted Action",
            action_type=ActionType.CREATE_TASK,
            parameters={"title": "Follow up on qualification"},
            created_by=test_user,
            updated_by=test_user,
            is_invalid=True,
        )

        with pytest.raises(Action.DoesNotExist):
            ActionService.get_action(action.id)

    def test_list_actions_excludes_soft_deleted(self, test_user):
        """list_actions() excludes soft-deleted actions."""
        active = Action.objects.create(
            name="Active Action",
            action_type=ActionType.CREATE_TASK,
            parameters={"title": "Follow up on qualification"},
            created_by=test_user,
            updated_by=test_user,
        )
        Action.objects.create(
            name="Deleted Action",
            action_type=ActionType.ADD_NOTE,
            parameters={"body": "Add note"},
            created_by=test_user,
            updated_by=test_user,
            is_invalid=True,
        )

        results = list(ActionService.list_actions())

        assert active in results
        assert all(not action.is_invalid for action in results)


@pytest.mark.django_db
class TestActionServiceExecution:
    """Tests for execute_action() handler dispatch."""

    def test_execute_action_create_task_returns_success(
        self,
        test_user,
        execution_log,
        event,
        deal,
    ):
        """create_task handler returns a success result dict."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            parameters={
                "title": "Follow up on qualification",
                "due_days_from_now": 2,
            },
            created_by=test_user,
            updated_by=test_user,
        )

        result = ActionService.execute_action(action, event, execution_log)

        assert result["status"] == "success"
        assert result["result"]["created"] is True

    def test_execute_action_handler_failure_returns_failed_dict(
        self,
        test_user,
        execution_log,
        event,
    ):
        """Handler failures return a failed dict instead of raising."""
        action = Action.objects.create(
            name="Broken Task Action",
            action_type=ActionType.CREATE_TASK,
            parameters={"due_days_from_now": 2},
            created_by=test_user,
            updated_by=test_user,
        )

        result = ActionService.execute_action(action, event, execution_log)

        assert result["status"] == "failed"
        assert "missing required keys" in result["error"]

    def test_execute_action_unknown_type_raises_value_error(
        self,
        test_user,
        execution_log,
        event,
    ):
        """Unknown persisted action types raise ValueError before execution."""
        action = Action.objects.create(
            name="Broken Action",
            action_type="unknown_type",
            parameters={"title": "x"},
            created_by=test_user,
            updated_by=test_user,
        )

        with pytest.raises(ValueError, match="Unsupported action_type"):
            ActionService.execute_action(action, event, execution_log)