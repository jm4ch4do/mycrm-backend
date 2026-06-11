"""Unit tests for WorkflowService."""

import pytest
from django.contrib.auth import get_user_model

from core.models import Action, ExecutionLog, Trigger, Workflow, WorkflowStep
from core.services.domain.workflow_service import WorkflowInactiveError, WorkflowService


@pytest.fixture(name="user")
def user_fixture(db):
    """A test user."""
    return get_user_model().objects.create_user(username="testuser", password="testpass123")


@pytest.fixture(name="trigger")
def trigger_fixture(db):
    """A test trigger."""
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture(name="action")
def action_fixture(db):
    """A test action."""
    return Action.objects.create(name="Send Email")


@pytest.fixture(name="action2")
def action2_fixture(db):
    """A second test action."""
    return Action.objects.create(name="Create Task")


@pytest.mark.django_db
class TestWorkflowServiceCreate:
    """Tests for WorkflowService.create_workflow()."""

    def test_create_workflow_sets_created_by(self, user, trigger):
        """create_workflow() sets created_by and updated_by."""
        data = {
            "name": "Qualify Deal Workflow",
            "description": "Auto-qualify new deals",
            "trigger": trigger,
        }

        workflow = WorkflowService.create_workflow(data, user)

        assert workflow.created_by == user
        assert workflow.updated_by == user

    def test_create_workflow_creates_workflow(self, user, trigger):
        """create_workflow() creates a workflow with provided data."""
        data = {
            "name": "Qualify Deal Workflow",
            "description": "Auto-qualify new deals",
            "trigger": trigger,
        }

        workflow = WorkflowService.create_workflow(data, user)

        assert workflow.name == "Qualify Deal Workflow"
        assert workflow.description == "Auto-qualify new deals"
        assert workflow.trigger == trigger

    def test_create_workflow_validates_trigger_exists(self, user):
        """create_workflow() raises Trigger.DoesNotExist for invalid trigger_id."""
        data = {
            "name": "Orphan Workflow",
            "trigger_id": "00000000-0000-0000-0000-000000000000",
        }

        with pytest.raises(Trigger.DoesNotExist):
            WorkflowService.create_workflow(data, user)

    def test_create_workflow_is_atomic(self, user, trigger):
        """create_workflow() is wrapped in @transaction.atomic."""
        data = {
            "name": "Qualify Deal Workflow",
            "trigger": trigger,
        }

        workflow = WorkflowService.create_workflow(data, user)

        # Verify the workflow was persisted
        assert Workflow.objects.filter(id=workflow.id).exists()


@pytest.mark.django_db
class TestWorkflowServiceUpdate:
    """Tests for WorkflowService.update_workflow()."""

    def test_update_workflow_sets_updated_by(self, user, trigger):
        """update_workflow() sets updated_by."""
        workflow = Workflow.objects.create(
            name="Original Name",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        WorkflowService.update_workflow(
            workflow,
            {"name": "Updated Name"},
            other_user,
        )

        workflow.refresh_from_db()
        assert workflow.updated_by == other_user

    def test_update_workflow_partial_update(self, user, trigger):
        """update_workflow() handles partial updates."""
        workflow = Workflow.objects.create(
            name="Original Name",
            description="Original Description",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )

        WorkflowService.update_workflow(
            workflow,
            {"name": "Updated Name"},
            user,
        )

        workflow.refresh_from_db()
        assert workflow.name == "Updated Name"
        assert workflow.description == "Original Description"

    def test_update_workflow_protects_created_by(self, user, trigger):
        """update_workflow() cannot change created_by."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        WorkflowService.update_workflow(
            workflow,
            {"created_by": other_user},
            user,
        )

        workflow.refresh_from_db()
        assert workflow.created_by == user

    def test_update_workflow_protects_is_invalid(self, user, trigger):
        """update_workflow() cannot change is_invalid."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_invalid=False,
        )

        WorkflowService.update_workflow(
            workflow,
            {"is_invalid": True},
            user,
        )

        workflow.refresh_from_db()
        assert workflow.is_invalid is False


@pytest.mark.django_db
class TestWorkflowServiceDelete:
    """Tests for WorkflowService.delete_workflow()."""

    def test_delete_workflow_sets_is_invalid(self, user, trigger):
        """delete_workflow() sets is_invalid=True."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )

        WorkflowService.delete_workflow(workflow, user)

        workflow.refresh_from_db()
        assert workflow.is_invalid is True

    def test_delete_workflow_sets_updated_by(self, user, trigger):
        """delete_workflow() sets updated_by."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        WorkflowService.delete_workflow(workflow, other_user)

        workflow.refresh_from_db()
        assert workflow.updated_by == other_user


@pytest.mark.django_db
class TestWorkflowServiceGet:
    """Tests for WorkflowService.get_workflow()."""

    def test_get_workflow_returns_workflow(self, user, trigger):
        """get_workflow() returns a valid workflow."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )

        retrieved = WorkflowService.get_workflow(workflow.id)

        assert retrieved == workflow

    def test_get_workflow_raises_for_invalid(self, user, trigger):
        """get_workflow() raises Workflow.DoesNotExist for soft-deleted workflows."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_invalid=True,
        )

        with pytest.raises(Workflow.DoesNotExist):
            WorkflowService.get_workflow(workflow.id)

    def test_get_workflow_raises_for_nonexistent(self):
        """get_workflow() raises Workflow.DoesNotExist for non-existent workflows."""
        with pytest.raises(Workflow.DoesNotExist):
            WorkflowService.get_workflow("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
class TestWorkflowServiceList:
    """Tests for WorkflowService.list_workflows()."""

    def test_list_workflows_excludes_soft_deleted(self, user, trigger):
        """list_workflows() excludes soft-deleted workflows."""
        valid_workflow = Workflow.objects.create(
            name="Valid Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        invalid_workflow = Workflow.objects.create(
            name="Invalid Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_invalid=True,
        )

        workflows = list(WorkflowService.list_workflows())

        assert valid_workflow in workflows
        assert invalid_workflow not in workflows

    def test_list_workflows_filters_by_trigger(self, user, trigger):
        """list_workflows() filters by trigger_id."""
        trigger2 = Trigger.objects.create(name="Other Trigger", event_type="deal.created")

        workflow1 = Workflow.objects.create(
            name="Workflow 1",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        workflow2 = Workflow.objects.create(
            name="Workflow 2",
            trigger=trigger2,
            created_by=user,
            updated_by=user,
        )

        workflows = list(WorkflowService.list_workflows({"trigger": trigger}))

        assert workflow1 in workflows
        assert workflow2 not in workflows

    def test_list_workflows_filters_by_is_active(self, user, trigger):
        """list_workflows() filters by is_active."""
        active_workflow = Workflow.objects.create(
            name="Active Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        inactive_workflow = Workflow.objects.create(
            name="Inactive Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=False,
        )

        workflows = list(WorkflowService.list_workflows({"is_active": True}))

        assert active_workflow in workflows
        assert inactive_workflow not in workflows


@pytest.mark.django_db
class TestWorkflowServiceSteps:
    """Tests for WorkflowService step management."""

    def test_add_step_creates_workflow_step(self, user, trigger, action):
        """add_step() creates a WorkflowStep."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )

        step = WorkflowService.add_step(workflow, action.id, 1, user)

        assert step.workflow == workflow
        assert step.action == action
        assert step.step_order == 1

    def test_add_step_raises_on_duplicate_order(self, user, trigger, action):
        """add_step() raises ValueError for duplicate step_order."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        WorkflowStep.objects.create(workflow=workflow, action=action, step_order=1)

        with pytest.raises(ValueError, match="Step order 1 already exists"):
            WorkflowService.add_step(workflow, action.id, 1, user)

    def test_add_step_updates_workflow_updated_by(self, user, trigger, action):
        """add_step() updates workflow.updated_by."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        WorkflowService.add_step(workflow, action.id, 1, other_user)

        workflow.refresh_from_db()
        assert workflow.updated_by == other_user

    def test_remove_step_deletes_workflow_step(self, user, trigger, action):
        """remove_step() deletes a WorkflowStep."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        step = WorkflowStep.objects.create(workflow=workflow, action=action, step_order=1)

        WorkflowService.remove_step(workflow, 1, user)

        assert not WorkflowStep.objects.filter(id=step.id).exists()

    def test_remove_step_updates_workflow_updated_by(self, user, trigger, action):
        """remove_step() updates workflow.updated_by."""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
        )
        WorkflowStep.objects.create(workflow=workflow, action=action, step_order=1)
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        WorkflowService.remove_step(workflow, 1, other_user)

        workflow.refresh_from_db()
        assert workflow.updated_by == other_user


@pytest.mark.django_db
class TestWorkflowServiceExecution:
    """Tests for WorkflowService.execute_workflow()."""

    def test_execute_workflow_creates_execution_log(self, user, trigger):
        """execute_workflow() creates an ExecutionLog."""
        from core.models import Event

        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        event = Event.objects.create(
            event_type="deal.stage_changed",
            source_service="core",
            entity_type="deal",
            entity_id="00000000-0000-0000-0000-000000000001",
            after_state={"stage": "qualified"},
        )

        execution_log = WorkflowService.execute_workflow(workflow, event, user)

        assert execution_log.workflow == workflow
        assert execution_log.event == event
        assert execution_log.triggered_by == user
        assert execution_log.status == "pending"

    def test_execute_workflow_raises_for_inactive(self, user, trigger):
        """execute_workflow() raises WorkflowInactiveError for inactive workflows."""
        from core.models import Event

        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=False,
        )
        event = Event.objects.create(
            event_type="deal.stage_changed",
            source_service="core",
            entity_type="deal",
            entity_id="00000000-0000-0000-0000-000000000001",
            after_state={"stage": "qualified"},
        )

        with pytest.raises(WorkflowInactiveError, match="inactive"):
            WorkflowService.execute_workflow(workflow, event, user)

    def test_execute_workflow_returns_pending_log(self, user, trigger):
        """execute_workflow() returns ExecutionLog with status='pending'."""
        from core.models import Event

        workflow = Workflow.objects.create(
            name="Test Workflow",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        event = Event.objects.create(
            event_type="deal.stage_changed",
            source_service="core",
            entity_type="deal",
            entity_id="00000000-0000-0000-0000-000000000001",
            after_state={"stage": "qualified"},
        )

        execution_log = WorkflowService.execute_workflow(workflow, event, user)

        assert execution_log.status == "pending"
        # Verify it's persisted
        assert ExecutionLog.objects.filter(id=execution_log.id).exists()


@pytest.mark.django_db
class TestWorkflowServiceTriggerWorkflows:
    """Tests for WorkflowService.get_active_workflows_for_trigger()."""

    def test_get_active_workflows_for_trigger_excludes_inactive(self, user, trigger):
        """get_active_workflows_for_trigger() excludes inactive workflows."""
        active = Workflow.objects.create(
            name="Active",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        inactive = Workflow.objects.create(
            name="Inactive",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=False,
        )

        workflows = list(WorkflowService.get_active_workflows_for_trigger(trigger))

        assert active in workflows
        assert inactive not in workflows

    def test_get_active_workflows_for_trigger_excludes_soft_deleted(self, user, trigger):
        """get_active_workflows_for_trigger() excludes soft-deleted workflows."""
        valid = Workflow.objects.create(
            name="Valid",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        deleted = Workflow.objects.create(
            name="Deleted",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
            is_invalid=True,
        )

        workflows = list(WorkflowService.get_active_workflows_for_trigger(trigger))

        assert valid in workflows
        assert deleted not in workflows

    def test_get_active_workflows_for_trigger_returns_correct_trigger_only(self, user, trigger):
        """get_active_workflows_for_trigger() returns workflows for specific trigger only."""
        trigger2 = Trigger.objects.create(name="Other Trigger", event_type="deal.created")

        workflow1 = Workflow.objects.create(
            name="Workflow 1",
            trigger=trigger,
            created_by=user,
            updated_by=user,
            is_active=True,
        )
        workflow2 = Workflow.objects.create(
            name="Workflow 2",
            trigger=trigger2,
            created_by=user,
            updated_by=user,
            is_active=True,
        )

        workflows = list(WorkflowService.get_active_workflows_for_trigger(trigger))

        assert workflow1 in workflows
        assert workflow2 not in workflows
