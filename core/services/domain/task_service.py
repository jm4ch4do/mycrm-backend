"""Business logic service for Task model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import Activity, ActivityStatus, ActivityType, Task, TaskState

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

# Fields that belong to Activity, not Task
# NOTE: 'status' is intentionally excluded — in the Task context it refers to
# Task.status (open/completed), not Activity.status (planned/completed/…).
# Activity.status is managed implicitly by complete_task / soft_delete_task.
_ACTIVITY_FIELDS = {
    "title",
    "description",
    "due_at",
    "owner_user",
    "account",
    "contact",
    "deal",
    "completed_at",
}

# Task-own fields that may be supplied on create/update
_TASK_FIELDS = {"priority", "category", "estimated_duration_minutes", "state"}


class TaskService:
    """Service layer for Task business logic."""

    @staticmethod
    def list_tasks() -> Any:
        """Retrieve all active tasks (activity not soft-deleted)."""
        return Task.objects.filter(activity__is_invalid=False)

    @staticmethod
    def get_task(task_id: str) -> Task:
        """Retrieve a single task by ID."""
        return get_object_or_404(Task, id=task_id)

    @staticmethod
    @transaction.atomic
    def create_task(data: dict[str, Any], user: User) -> Task:
        """Create a Task by first creating the parent Activity(type='task').

        ``data`` may contain both Activity-level fields and Task-level fields.
        The ``type`` field is always forced to ActivityType.TASK.
        """
        activity_data: dict[str, Any] = {}
        task_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _TASK_FIELDS:
                task_data[key] = value
            # unknown fields are silently ignored

        activity = Activity.objects.create(
            type=ActivityType.TASK,
            owner_user=user,
            created_by=user,
            **activity_data,
        )
        task = Task.objects.create(activity=activity, **task_data)
        return task

    @staticmethod
    @transaction.atomic
    def update_task(task: Task, data: dict[str, Any], user: User) -> Task:
        """Update both the parent Activity and Task-own fields."""
        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        activity_data: dict[str, Any] = {}
        task_data: dict[str, Any] = {}

        for key, value in data.items():
            if key in _ACTIVITY_FIELDS:
                activity_data[key] = value
            elif key in _TASK_FIELDS:
                task_data[key] = value

        if activity_data:
            activity_data["updated_by"] = user
            for field, value in activity_data.items():
                setattr(task.activity, field, value)
            task.activity.save()

        if task_data:
            for field, value in task_data.items():
                setattr(task, field, value)
            task.save()

        return task

    @staticmethod
    @transaction.atomic
    def complete_task(task: Task, user: User) -> Task:
        """Mark a task and its parent activity as completed."""
        now = timezone.now()
        task.state = TaskState.COMPLETED
        task.save()

        task.activity.status = ActivityStatus.COMPLETED
        task.activity.completed_at = now
        task.activity.updated_by = user
        task.activity.save()

        return task

    @staticmethod
    @transaction.atomic
    def soft_delete_task(task: Task, user: User) -> Task:
        """Soft-delete a task by propagating is_invalid to the parent activity."""
        task.activity.is_invalid = True
        task.activity.updated_by = user
        task.activity.save()
        return task
