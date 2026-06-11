"""
Celery tasks for background processing.

NOTE: Celery infrastructure (worker + beat scheduler) not yet configured.
      For now, these tasks can be invoked directly with .apply() for testing.
      Full Celery setup deferred to production deployment.
"""

# Import will be used when Celery is configured:
# from celery import shared_task

from core.services.external.scan_overdue import scan_overdue_activities

__all__ = ["scan_overdue_activities", "execute_workflow_task"]


def execute_workflow_task(execution_log_id):
    """Placeholder workflow task callable until Celery is fully configured."""
    return execution_log_id


def _execute_workflow_task_delay(*, execution_log_id):
    """Celery-like delay shim used by the service layer in local/dev tests."""
    return execute_workflow_task(execution_log_id=execution_log_id)


execute_workflow_task.delay = _execute_workflow_task_delay

# When Celery is configured, wrap the service function with @shared_task:
# @shared_task
# def scan_overdue_activities():
#     from core.services.external.scan_overdue import scan_overdue_activities as _scan
#     return _scan()
