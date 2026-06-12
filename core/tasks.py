"""Celery task shims and synchronous execution helpers for local tests."""

from __future__ import annotations

from types import SimpleNamespace

# Import will be used when Celery is configured:
# from celery import shared_task

from django.utils import timezone

from core.models import ExecutionStatus, WorkflowStep
from core.services.domain.action_service import ActionService
from core.services.domain.execution_log_service import ExecutionLogService
from core.services.external.scan_overdue import scan_overdue_activities

__all__ = ["scan_overdue_activities", "execute_workflow_task"]


def execute_workflow_task(execution_log_id):
    """Process a workflow execution log synchronously."""
    execution_log = ExecutionLogService.get_execution_log(execution_log_id)
    ExecutionLogService.mark_running(execution_log)

    successes = 0
    failures = 0

    workflow_steps = WorkflowStep.objects.filter(workflow=execution_log.workflow).select_related(
        "action"
    )

    for workflow_step in workflow_steps:
        result = ActionService.execute_action(
            workflow_step.action,
            execution_log.event,
            execution_log,
        )
        step_entry = {
            "step_order": workflow_step.step_order,
            "action_id": str(workflow_step.action.id),
            "action_type": workflow_step.action.action_type,
            "status": result.get("status"),
            "result": result.get("result") if result.get("status") == "success" else {},
            "error": result.get("error"),
            "executed_at": timezone.now().isoformat(),
        }
        ExecutionLogService.append_step_log(execution_log, step_entry)

        if result.get("status") == "success":
            successes += 1
            continue

        failures += 1
        break

    if failures:
        status = ExecutionStatus.PARTIAL if successes else ExecutionStatus.FAILED
    else:
        status = ExecutionStatus.SUCCESS

    ExecutionLogService.finalize(execution_log, status)
    return {
        "execution_log_id": str(execution_log.id),
        "status": status,
        "step_count": len(execution_log.logs),
    }


def _execute_workflow_task_delay(*, execution_log_id):
    """Celery-like delay shim used by the service layer in local/dev tests."""
    return SimpleNamespace(result=execution_log_id)


def _execute_workflow_task_apply(*, args=None, kwargs=None):
    """Celery-like apply shim used by BDD tests."""
    args = args or ()
    kwargs = kwargs or {}
    execution_log_id = kwargs.get("execution_log_id") or (args[0] if args else None)
    result = execute_workflow_task(execution_log_id=execution_log_id)
    return SimpleNamespace(result=result, successful=lambda: True)


execute_workflow_task.delay = _execute_workflow_task_delay
execute_workflow_task.apply = _execute_workflow_task_apply

# When Celery is configured, wrap the service function with @shared_task:
# @shared_task
# def scan_overdue_activities():
#     from core.services.external.scan_overdue import scan_overdue_activities as _scan
#     return _scan()
