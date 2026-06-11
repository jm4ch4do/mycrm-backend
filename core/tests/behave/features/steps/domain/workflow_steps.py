"""Workflow-specific behave step definitions."""

from behave import then, when

from core.models import Event, ExecutionLog, Workflow
from core.services.domain.workflow_service import WorkflowService
from steps.utils import resolve_model


@when('I execute workflow "{workflow_name}" for event_type "{event_type}"')
def step_execute_workflow_for_event(context, workflow_name, event_type):
    """
    Execute a named workflow for an in-memory event.

    Always attempts execution and captures any raised exception on context.
    For successful execution: context.execution_log is set, context.captured_exception is None.
    For failed execution: context.captured_exception is set, context.execution_log is None.
    """
    workflow = Workflow.objects.get(name=workflow_name)
    context.workflow = workflow
    context.event = Event.objects.create(
        event_type=event_type,
        source_service="core",
        entity_type="deal",
        entity_id="00000000-0000-0000-0000-000000000001",
        after_state={"stage": "qualified"},
    )

    try:
        context.execution_log = WorkflowService.execute_workflow(
            workflow=workflow,
            event=context.event,
            triggered_by=getattr(context, "auth_user", None),
        )
        context.captured_exception = None
    except Exception as exc:  # pylint: disable=broad-exception-caught
        context.execution_log = None
        context.captured_exception = exc


@then('an execution log exists for workflow "{workflow_name}" with status "{status_value}"')
def step_execution_log_exists_for_workflow(context, workflow_name, status_value):
    """Verify an ExecutionLog exists for a workflow name with expected status."""
    workflow_model = resolve_model("workflow")
    workflow = workflow_model.objects.get(name=workflow_name)

    assert ExecutionLog.objects.filter(workflow=workflow).exists(), (
        f"Expected an ExecutionLog for workflow '{workflow_name}'"
    )
    log = ExecutionLog.objects.filter(workflow=workflow).latest("created_at")
    assert log.status == status_value
