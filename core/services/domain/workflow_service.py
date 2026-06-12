"""Business logic service for Workflow model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from core.models import Action, ExecutionLog, Trigger, Workflow, WorkflowStep
from core.services.domain.execution_log_service import ExecutionLogService
from core.tasks import execute_workflow_task

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

    from core.models import Event


class WorkflowInactiveError(Exception):
    """Raised when attempting to execute an inactive workflow."""


class WorkflowService:
    """Service layer for Workflow business logic."""

    @staticmethod
    def list_workflows(filters: dict[str, Any] | None = None) -> QuerySet[Workflow]:
        """List non-deleted workflows with optional filtering."""
        queryset = Workflow.objects.filter(is_invalid=False)

        if filters:
            allowed = {
                "trigger",
                "is_active",
            }
            applied_filters = {
                key: value
                for key, value in filters.items()
                if key in allowed and value not in (None, "")
            }
            if applied_filters:
                queryset = queryset.filter(**applied_filters)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_workflow(workflow_id: UUID | str) -> Workflow:
        """Retrieve a non-deleted workflow by ID.
        
        Raises:
            Workflow.DoesNotExist: If workflow not found or is soft-deleted
        """
        return Workflow.objects.get(id=workflow_id, is_invalid=False)

    @staticmethod
    @transaction.atomic
    def create_workflow(data: dict[str, Any], created_by: User) -> Workflow:
        """Create a workflow and set audit fields.

        Validates that the trigger FK exists and is not soft-deleted.

        Args:
            data: Workflow data dict
            created_by: User creating the workflow

        Returns:
            Created Workflow instance

        Raises:
            Trigger.DoesNotExist: If trigger_id is invalid or soft-deleted
        """
        payload = data.copy()

        # Validate trigger exists and is not soft-deleted
        # Handle both 'trigger' (object) and 'trigger_id' (UUID) forms
        trigger = payload.get("trigger")
        trigger_id = payload.get("trigger_id")
        
        if trigger:
            if hasattr(trigger, 'id'):
                # It's a Trigger instance
                Trigger.objects.get(id=trigger.id, is_invalid=False)
            else:
                # It's a UUID string
                Trigger.objects.get(id=trigger, is_invalid=False)
        elif trigger_id:
            Trigger.objects.get(id=trigger_id, is_invalid=False)

        return Workflow.objects.create(
            created_by=created_by,
            updated_by=created_by,
            **payload,
        )

    @staticmethod
    @transaction.atomic
    def update_workflow(workflow: Workflow, data: dict[str, Any], updated_by: User) -> Workflow:
        """Update mutable workflow fields and set updated_by.

        Args:
            workflow: Workflow instance to update
            data: Partial or full update data
            updated_by: User making the update

        Returns:
            Updated Workflow instance
        """
        payload = data.copy()

        # Protect immutable fields
        for field in ["id", "created_at", "created_by", "is_invalid"]:
            payload.pop(field, None)

        # Validate trigger if being updated
        trigger = payload.get("trigger")
        trigger_id = payload.get("trigger_id")
        
        if trigger:
            if hasattr(trigger, 'id'):
                # It's a Trigger instance
                Trigger.objects.get(id=trigger.id, is_invalid=False)
            else:
                # It's a UUID string
                Trigger.objects.get(id=trigger, is_invalid=False)
        elif trigger_id:
            Trigger.objects.get(id=trigger_id, is_invalid=False)

        payload["updated_by"] = updated_by
        for field, value in payload.items():
            setattr(workflow, field, value)

        workflow.save()
        return workflow

    @staticmethod
    @transaction.atomic
    def delete_workflow(workflow: Workflow, updated_by: User) -> None:
        """Soft-delete a workflow by marking it invalid.

        Args:
            workflow: Workflow instance to delete
            updated_by: User performing the deletion
        """
        workflow.is_invalid = True
        workflow.updated_by = updated_by
        workflow.save()

    @staticmethod
    def get_active_workflows_for_trigger(trigger: Trigger) -> QuerySet[Workflow]:
        """Return active, non-soft-deleted workflows for a trigger.

        Used by the automation engine to find workflows to execute.

        Args:
            trigger: Trigger instance

        Returns:
            QuerySet of active Workflow instances
        """
        return Workflow.objects.filter(
            trigger=trigger,
            is_active=True,
            is_invalid=False,
        ).order_by("-created_at")

    @staticmethod
    @transaction.atomic
    def add_step(
        workflow: Workflow,
        action_id: UUID | str,
        step_order: int,
        updated_by: User,
    ) -> WorkflowStep:
        """Add a step to a workflow.

        Args:
            workflow: Workflow instance
            action_id: UUID of Action to add
            step_order: Execution order (0-based)
            updated_by: User making the change

        Returns:
            Created WorkflowStep instance

        Raises:
            ValueError: If step_order already exists for this workflow
            Action.DoesNotExist: If action_id is invalid
        """
        # Check for duplicate step_order
        if WorkflowStep.objects.filter(workflow=workflow, step_order=step_order).exists():
            raise ValueError(
                f"Step order {step_order} already exists in workflow '{workflow.name}'. "
                "Each workflow step must have a unique order."
            )

        # Validate action exists
        action = Action.objects.get(id=action_id)

        # Create the step
        step = WorkflowStep.objects.create(
            workflow=workflow,
            action=action,
            step_order=step_order,
        )

        # Update workflow's updated_by for audit trail
        workflow.updated_by = updated_by
        workflow.save(update_fields=["updated_by", "updated_at"])

        return step

    @staticmethod
    @transaction.atomic
    def remove_step(
        workflow: Workflow,
        step_order: int,
        updated_by: User,
    ) -> None:
        """Remove a step from a workflow by step_order.

        Args:
            workflow: Workflow instance
            step_order: Execution order of step to remove
            updated_by: User making the change

        Raises:
            WorkflowStep.DoesNotExist: If no step at this order exists
        """
        step = WorkflowStep.objects.get(workflow=workflow, step_order=step_order)
        step.delete()

        # Update workflow's updated_by for audit trail
        workflow.updated_by = updated_by
        workflow.save(update_fields=["updated_by", "updated_at"])

    @staticmethod
    @transaction.atomic
    def execute_workflow(
        workflow: Workflow,
        event: Event,
        triggered_by: User | None = None,
    ) -> "ExecutionLog":
        """Execute a workflow asynchronously.

        Creates an ExecutionLog record immediately and dispatches a Celery task
        to process steps. Returns the log without waiting for completion.

        Args:
            workflow: Workflow instance to execute
            event: Event instance that triggered execution
            triggered_by: User who triggered the execution

        Returns:
            ExecutionLog instance with status='pending'

        Raises:
            WorkflowInactiveError: If workflow.is_active is False
        """
        if not workflow.is_active:
            raise WorkflowInactiveError(
                f"Workflow '{workflow.name}' is inactive and cannot be executed."
            )

        # Create execution log record
        execution_log = ExecutionLogService.create_execution_log(
            workflow=workflow,
            event=event,
            created_by=triggered_by,
        )

        execute_workflow_task.delay(execution_log_id=str(execution_log.id))

        return execution_log
