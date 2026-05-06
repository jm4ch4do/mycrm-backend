"""Tests for TaskService business logic."""

from __future__ import annotations

import pytest
from django.utils import timezone
from datetime import timedelta

from core.models import Activity, ActivityStatus, ActivityType, TaskState
from core.services.domain.task_service import TaskService


@pytest.mark.django_db
class TestTaskServiceCreate:
    """Test TaskService.create_task."""

    def test_creates_activity_with_type_task(self, test_user, account):
        """create_task always produces an Activity with type='task'."""
        task = TaskService.create_task(
            {"title": "Follow up", "account": account}, test_user
        )
        assert task.activity.type == ActivityType.TASK

    def test_sets_owner_and_created_by_on_activity(self, test_user, account):
        """create_task sets owner_user and created_by on the Activity."""
        task = TaskService.create_task(
            {"title": "Follow up", "account": account}, test_user
        )
        assert task.activity.owner_user == test_user
        assert task.activity.created_by == test_user

    def test_activity_fields_forwarded(self, test_user, account):
        """Activity-level fields in data are stored on the activity."""
        due = timezone.now() + timedelta(days=2)
        task = TaskService.create_task(
            {
                "title": "Demo",
                "description": "Details",
                "account": account,
                "due_at": due,
            },
            test_user,
        )
        assert task.activity.title == "Demo"
        assert task.activity.description == "Details"
        assert task.activity.due_at == due

    def test_task_fields_forwarded(self, test_user, account):
        """Task-specific fields in data are stored on the Task row."""
        task = TaskService.create_task(
            {
                "title": "Call back",
                "account": account,
                "priority": "high",
                "category": "follow_up",
                "estimated_duration_minutes": 15,
            },
            test_user,
        )
        assert task.priority == "high"
        assert task.category == "follow_up"
        assert task.estimated_duration_minutes == 15

    def test_status_defaults_to_open(self, test_user, account):
        """Task.status defaults to 'open' when not supplied."""
        task = TaskService.create_task({"title": "Demo", "account": account}, test_user)
        assert task.state == TaskState.OPEN

    def test_task_status_not_written_to_activity(self, test_user, account):
        """Task state is stored on Task, not on Activity."""
        task = TaskService.create_task(
            {"title": "Demo", "account": account, "state": "completed"}, test_user
        )
        # Task has the value; activity.status remains default (planned)
        assert task.state == "completed"
        assert task.activity.status == ActivityStatus.PLANNED

    def test_unknown_fields_ignored(self, test_user, account):
        """Unknown fields in data are silently dropped."""
        task = TaskService.create_task(
            {"title": "Demo", "account": account, "bogus_field": "X"}, test_user
        )
        assert task.activity.title == "Demo"


@pytest.mark.django_db
class TestTaskServiceUpdate:
    """Test TaskService.update_task."""

    def _make_task(self, test_user, account):
        return TaskService.create_task(
            {"title": "Original", "account": account, "priority": "low"}, test_user
        )

    def test_updates_activity_title(self, test_user, account):
        """update_task writes activity-level fields to the activity."""
        task = self._make_task(test_user, account)
        updated = TaskService.update_task(task, {"title": "Renamed"}, test_user)
        assert updated.activity.title == "Renamed"

    def test_updates_task_priority(self, test_user, account):
        """update_task writes task-level fields to the task row."""
        task = self._make_task(test_user, account)
        updated = TaskService.update_task(task, {"priority": "high"}, test_user)
        updated.refresh_from_db()
        assert updated.priority == "high"

    def test_sets_updated_by_on_activity(self, test_user, test_user_2, account):
        """update_task sets activity.updated_by when activity fields change."""
        task = self._make_task(test_user, account)
        TaskService.update_task(task, {"title": "Changed"}, test_user_2)
        task.activity.refresh_from_db()
        assert task.activity.updated_by == test_user_2

    def test_immutable_fields_ignored(self, test_user, account):
        """Immutable fields (id, created_at, created_by) are stripped."""
        task = self._make_task(test_user, account)
        original_id = task.id
        TaskService.update_task(task, {"id": "new-id", "title": "X"}, test_user)
        assert task.id == original_id


@pytest.mark.django_db
class TestTaskServiceComplete:
    """Test TaskService.complete_task."""

    def test_sets_task_status_completed(self, test_user, account):
        """complete_task sets task.state to 'completed'."""
        task = TaskService.create_task(
            {"title": "Do it", "account": account}, test_user
        )
        completed = TaskService.complete_task(task, test_user)
        assert completed.state == TaskState.COMPLETED

    def test_sets_activity_status_completed(self, test_user, account):
        """complete_task sets activity.status to 'completed'."""
        task = TaskService.create_task(
            {"title": "Do it", "account": account}, test_user
        )
        completed = TaskService.complete_task(task, test_user)
        assert completed.activity.status == ActivityStatus.COMPLETED

    def test_sets_activity_completed_at(self, test_user, account):
        """complete_task sets a non-null completed_at on the activity."""
        before = timezone.now()
        task = TaskService.create_task(
            {"title": "Do it", "account": account}, test_user
        )
        completed = TaskService.complete_task(task, test_user)
        assert completed.activity.completed_at is not None
        assert completed.activity.completed_at >= before

    def test_sets_activity_updated_by(self, test_user, test_user_2, account):
        """complete_task records who completed the task."""
        task = TaskService.create_task(
            {"title": "Do it", "account": account}, test_user
        )
        completed = TaskService.complete_task(task, test_user_2)
        assert completed.activity.updated_by == test_user_2

    def test_is_overdue_false_after_complete(self, test_user, account):
        """Once completed, is_overdue returns False even for past due_at."""
        past = timezone.now() - timedelta(days=1)
        task = TaskService.create_task(
            {"title": "Late task", "account": account, "due_at": past}, test_user
        )
        completed = TaskService.complete_task(task, test_user)
        assert completed.is_overdue is False


@pytest.mark.django_db
class TestTaskServiceSoftDelete:
    """Test TaskService.soft_delete_task."""

    def test_sets_activity_is_invalid(self, test_user, account):
        """soft_delete_task propagates is_invalid=True to the activity."""
        task = TaskService.create_task(
            {"title": "Remove me", "account": account}, test_user
        )
        TaskService.soft_delete_task(task, test_user)
        task.activity.refresh_from_db()
        assert task.activity.is_invalid is True

    def test_sets_activity_updated_by(self, test_user, test_user_2, account):
        """soft_delete_task records who deleted the task."""
        task = TaskService.create_task(
            {"title": "Remove me", "account": account}, test_user
        )
        TaskService.soft_delete_task(task, test_user_2)
        task.activity.refresh_from_db()
        assert task.activity.updated_by == test_user_2

    def test_list_tasks_excludes_soft_deleted(self, test_user, account):
        """list_tasks does not return tasks whose activity is soft-deleted."""
        task = TaskService.create_task({"title": "Gone", "account": account}, test_user)
        TaskService.soft_delete_task(task, test_user)
        assert not TaskService.list_tasks().filter(id=task.id).exists()


@pytest.mark.django_db
class TestTaskServiceList:
    """Test TaskService.list_tasks."""

    def test_returns_active_tasks(self, test_user, account):
        """list_tasks returns tasks whose activity is not soft-deleted."""
        task = TaskService.create_task(
            {"title": "Active", "account": account}, test_user
        )
        assert TaskService.list_tasks().filter(id=task.id).exists()

    def test_excludes_hard_deleted_activity(self, test_user, account):
        """list_tasks does not return tasks whose activity was hard-deleted."""
        task = TaskService.create_task(
            {"title": "Deleted", "account": account}, test_user
        )
        task_id = task.id
        Activity.objects.filter(id=task.activity.id).delete()
        assert not TaskService.list_tasks().filter(id=task_id).exists()
