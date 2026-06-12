"""Business logic service for ExecutionLog model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db.models import QuerySet
from django.utils import timezone

from core.models import ExecutionLog, ExecutionStatus

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

    from core.models import Event, Workflow


class ExecutionLogService:
    """Service layer for ExecutionLog read and write operations."""

    @staticmethod
    def create_execution_log(
        workflow: Workflow,
        event: Event,
        created_by: User | None = None,
    ) -> ExecutionLog:
        """Create a pending execution log without opening a transaction."""
        return ExecutionLog.objects.create(
            workflow=workflow,
            event=event,
            status=ExecutionStatus.PENDING,
            started_at=timezone.now(),
            created_by=created_by,
        )

    @staticmethod
    def mark_running(execution_log: ExecutionLog) -> ExecutionLog:
        """Mark an execution log as running."""
        execution_log.status = ExecutionStatus.RUNNING
        execution_log.save(update_fields=["status"])
        return execution_log

    @staticmethod
    def append_step_log(execution_log: ExecutionLog, step_entry: dict[str, Any]) -> ExecutionLog:
        """Append a step entry to the execution log without overwriting existing entries."""
        logs = list(execution_log.logs or [])
        logs.append(step_entry)
        execution_log.logs = logs
        execution_log.save(update_fields=["logs"])
        return execution_log

    @staticmethod
    def finalize(execution_log: ExecutionLog, status: str) -> ExecutionLog:
        """Finalize an execution log with a terminal status and completion time."""
        execution_log.status = status
        execution_log.finished_at = timezone.now()
        execution_log.save(update_fields=["status", "finished_at"])
        return execution_log

    @staticmethod
    def get_execution_log(log_id: UUID | str) -> ExecutionLog:
        """Retrieve a single execution log by ID."""
        return ExecutionLog.objects.get(id=log_id)

    @staticmethod
    def list_execution_logs(filters: dict[str, Any] | None = None) -> QuerySet[ExecutionLog]:
        """List execution logs with optional filtering."""
        queryset = ExecutionLog.objects.all()

        if filters:
            allowed = {"workflow", "event", "status"}
            applied_filters = {
                key: value
                for key, value in filters.items()
                if key in allowed and value not in (None, "")
            }
            if applied_filters:
                queryset = queryset.filter(**applied_filters)

        return queryset.order_by("-started_at")