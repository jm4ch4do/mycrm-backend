"""ExecutionLog-specific behave step definitions."""

from behave import then, when

from core.tasks import execute_workflow_task


@when("the Celery task processes the workflow execution")
def when_celery_task_processes_workflow_execution(context):
    """Run the workflow execution task synchronously via the apply shim."""
    assert (
        context.execution_log is not None
    ), "Expected execution_log to exist before task processing."
    task_result = execute_workflow_task.apply(
        kwargs={"execution_log_id": str(context.execution_log.id)}
    )
    context.execution_result = task_result.result
    context.execution_log.refresh_from_db()


@then('the execution log status is "{status_value}"')
def then_execution_log_status_is(context, status_value):
    """Assert the execution log reached the expected status."""
    context.execution_log.refresh_from_db()
    assert context.execution_log.status == status_value


@then("the logs array contains one step entry")
def then_logs_array_contains_one_step_entry(context):
    """Assert a successful execution wrote exactly one step log entry."""
    context.execution_log.refresh_from_db()
    assert len(context.execution_log.logs) == 1


@then("the step log entry contains an error message")
def then_step_log_entry_contains_error_message(context):
    """Assert the step log contains an error message."""
    context.execution_log.refresh_from_db()
    assert context.execution_log.logs
    assert context.execution_log.logs[0]["error"]
