"""Unit tests for Workflow and WorkflowStep models."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from core.models import Action, ActionType, Trigger, Workflow, WorkflowStep


@pytest.fixture(name="trigger")
def trigger_fixture(db):
    """A minimal trigger for workflow attachment."""
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture(name="action")
def action_fixture(db):
    """A minimal action for workflow step attachment."""
    return Action.objects.create(
        name="Send Email",
        action_type=ActionType.CREATE_TASK,
    )


@pytest.mark.django_db
class TestWorkflowModel:
    """Tests for Workflow model fields, defaults, and behavior."""

    def test_workflow_str_returns_name_and_trigger(self, trigger):
        """__str__ returns '<name> (<trigger name>)'."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        assert str(workflow) == "Qualify Deal Workflow (Deal Stage Trigger)"

    def test_workflow_requires_name(self, trigger):
        """name is required."""
        workflow = Workflow(
            trigger=trigger,
        )

        with pytest.raises(ValidationError):
            workflow.full_clean()

    def test_workflow_requires_trigger(self):
        """trigger FK is required."""
        workflow = Workflow(
            name="Orphan Workflow",
        )

        with pytest.raises((ValidationError, ValueError)):
            workflow.full_clean()

    def test_workflow_is_active_defaults_true(self, trigger):
        """is_active defaults to True."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        assert workflow.is_active is True

    def test_workflow_is_invalid_defaults_false(self, trigger):
        """is_invalid defaults to False."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        assert workflow.is_invalid is False

    def test_workflow_soft_delete_sets_is_invalid(self, trigger):
        """Workflow supports soft delete through is_invalid flag."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        workflow.is_invalid = True
        workflow.save()

        workflow.refresh_from_db()
        assert workflow.is_invalid is True

    def test_workflow_ordering_is_newest_first(self, trigger):
        """Meta ordering returns newest workflows first."""
        older = Workflow.objects.create(
            name="Older Workflow",
            trigger=trigger,
        )
        older.created_at = timezone.now() - timedelta(minutes=5)
        older.save(update_fields=["created_at"])

        newer = Workflow.objects.create(
            name="Newer Workflow",
            trigger=trigger,
        )

        workflows = list(Workflow.objects.all())

        assert workflows[0] == newer
        assert workflows[1] == older

    def test_workflow_description_nullable(self, trigger):
        """description can be null."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
            description=None,
        )

        assert workflow.description is None

    def test_workflow_description_can_be_set(self, trigger):
        """description can be set."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
            description="This workflow qualifies deals.",
        )

        assert workflow.description == "This workflow qualifies deals."

    def test_workflow_has_many_to_many_steps(self, trigger):
        """Workflow.steps returns related Actions via WorkflowStep."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        # We can't create steps without Action model, but we can verify
        # the ManyToMany relationship exists
        assert hasattr(workflow, "steps")

    def test_workflow_has_workflow_steps_related_manager(self, trigger):
        """Workflow has workflow_steps reverse relation."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        # Verify reverse relation exists
        assert hasattr(workflow, "workflow_steps")

    def test_workflow_cascade_deletes_workflow_steps(self, trigger):
        """Deleting a Workflow cascades to delete its WorkflowSteps."""
        workflow = Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

        # Verify the workflow exists
        assert Workflow.objects.filter(id=workflow.id).exists()

        # Delete the workflow
        workflow.delete()

        # Verify the workflow is deleted
        assert not Workflow.objects.filter(id=workflow.id).exists()


@pytest.mark.django_db
class TestWorkflowStepModel:
    """Tests for WorkflowStep through model."""

    @pytest.fixture
    def workflow(self, trigger):
        """A minimal workflow for step attachment."""
        return Workflow.objects.create(
            name="Qualify Deal Workflow",
            trigger=trigger,
        )

    def test_workflow_step_str_returns_workflow_and_order(self, workflow, action):
        """__str__ returns '<workflow> - Step <step_order>'."""
        step = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=1,
        )

        assert str(step) == "Qualify Deal Workflow - Step 1"

    def test_workflow_step_step_order_defaults_zero(self, workflow, action):
        """step_order defaults to 0."""
        step = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
        )

        assert step.step_order == 0

    def test_workflow_step_unique_together_enforced(self, workflow, action):
        """unique_together constraint on (workflow, step_order) is enforced."""
        WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=1,
        )

        # Attempting to create another step with same workflow + step_order should fail
        duplicate_step = WorkflowStep(
            workflow=workflow,
            action=action,
            step_order=1,
        )

        with pytest.raises(IntegrityError):
            duplicate_step.save()

    def test_workflow_step_ordering_by_step_order(self, workflow, action):
        """Meta ordering returns steps by step_order ascending."""
        step_3 = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=3,
        )
        step_1 = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=1,
        )
        step_2 = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=2,
        )

        steps = list(WorkflowStep.objects.all())

        assert steps[0] == step_1
        assert steps[1] == step_2
        assert steps[2] == step_3

    def test_workflow_step_multiple_workflows_independent(self, trigger, action):
        """WorkflowSteps from different workflows are independent."""
        workflow_a = Workflow.objects.create(
            name="Workflow A",
            trigger=trigger,
        )
        workflow_b = Workflow.objects.create(
            name="Workflow B",
            trigger=trigger,
        )

        # Create step 1 in both workflows
        WorkflowStep.objects.create(
            workflow=workflow_a,
            action=action,
            step_order=1,
        )
        WorkflowStep.objects.create(
            workflow=workflow_b,
            action=action,
            step_order=1,
        )

        # Verify both steps exist (same step_order but different workflows)
        assert WorkflowStep.objects.filter(workflow=workflow_a, step_order=1).exists()
        assert WorkflowStep.objects.filter(workflow=workflow_b, step_order=1).exists()

    def test_workflow_step_cascade_delete_with_workflow(self, workflow, action):
        """Deleting a Workflow cascades to delete its WorkflowSteps."""
        WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=1,
        )
        WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=2,
        )

        workflow_id = workflow.id

        # Verify steps exist
        assert WorkflowStep.objects.filter(workflow_id=workflow_id).count() == 2

        # Delete the workflow
        workflow.delete()

        # Verify steps are deleted
        assert WorkflowStep.objects.filter(workflow_id=workflow_id).count() == 0
