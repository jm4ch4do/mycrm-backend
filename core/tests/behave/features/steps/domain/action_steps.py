"""Action-specific behave step definitions."""

import uuid

from behave import when

from core.models import Action, Event, ExecutionLog, Trigger, Workflow
from core.services.domain.action_service import ActionService


@when('the automation engine executes action "{action_name}" against an event')
def step_execute_action_against_event(context, action_name):
    """Execute a named action via ActionService against a synthetic event."""
    action = Action.objects.get(name=action_name)
    context.action = action

    trigger = Trigger.objects.create(
        name=f"Action Trigger {uuid.uuid4()}",
        event_type="deal.stage_changed",
    )
    workflow = Workflow.objects.create(
        name=f"Action Workflow {uuid.uuid4()}",
        trigger=trigger,
        created_by=getattr(context, "auth_user", context.test_user),
        updated_by=getattr(context, "auth_user", context.test_user),
    )
    event = Event.objects.create(
        event_type="deal.stage_changed",
        source_service="core",
        entity_type="deal",
        entity_id=str(context.deal.id),
        after_state={"stage": "qualified"},
    )
    execution_log = ExecutionLog.objects.create(
        workflow=workflow,
        event=event,
        triggered_by=getattr(context, "auth_user", context.test_user),
    )

    try:
        context.execution_result = ActionService.execute_action(action, event, execution_log)
        context.captured_exception = None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        context.execution_result = None
        context.captured_exception = exc


