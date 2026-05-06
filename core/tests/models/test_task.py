"""Unit tests for Task model."""

import pytest
from django.utils import timezone
from datetime import timedelta

from core.models import (
    Activity,
    ActivityType,
    Task,
    TaskCategory,
    TaskPriority,
    TaskState,
)


def make_activity(db, account, test_user, **kwargs):
    """Create a minimal Activity(type=task) for use in Task tests."""
    defaults = dict(
        type=ActivityType.TASK,
        title="Test Task Activity",
        owner_user=test_user,
        account=account,
        created_by=test_user,
    )
    defaults.update(kwargs)
    return Activity.objects.create(**defaults)


class TestTaskCreation:
    """Test Task model creation."""

    def test_create_with_required_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Task can be created with only an activity link."""
        activity = make_activity(db, account, test_user)
        task = Task.objects.create(activity=activity)

        assert task.activity == activity
        assert task.id is not None
        assert task.state == TaskState.OPEN
        assert task.priority is None
        assert task.category is None
        assert task.estimated_duration_minutes is None

    def test_create_with_all_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Task can be created with all optional fields populated."""
        activity = make_activity(db, account, test_user)
        task = Task.objects.create(
            activity=activity,
            priority=TaskPriority.HIGH,
            category=TaskCategory.FOLLOW_UP,
            estimated_duration_minutes=30,
            state=TaskState.OPEN,
        )

        assert task.priority == TaskPriority.HIGH
        assert task.category == TaskCategory.FOLLOW_UP
        assert task.estimated_duration_minutes == 30
        assert task.state == TaskState.OPEN

    def test_status_defaults_to_open(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Task.state defaults to 'open' when not supplied."""
        activity = make_activity(db, account, test_user)
        task = Task.objects.create(activity=activity)
        assert task.state == TaskState.OPEN

    def test_str_returns_activity_title(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """__str__ delegates to the parent activity's title."""
        activity = make_activity(db, account, test_user, title="Follow up with Acme")
        task = Task.objects.create(activity=activity)
        assert str(task) == "Follow up with Acme"

    def test_one_to_one_constraint(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """A second Task cannot be created for the same Activity."""
        from django.db import IntegrityError

        activity = make_activity(db, account, test_user)
        Task.objects.create(activity=activity)
        with pytest.raises(IntegrityError):
            Task.objects.create(activity=activity)

    def test_cascade_delete_removes_task(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Deleting the parent Activity cascades to the Task row."""
        activity = make_activity(db, account, test_user)
        task = Task.objects.create(activity=activity)
        task_id = task.id
        activity.delete()
        assert not Task.objects.filter(id=task_id).exists()


class TestTaskIsOverdue:
    """Test Task.is_overdue property."""

    def test_not_overdue_when_no_due_date(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """is_overdue is False when activity.due_at is None."""
        activity = make_activity(db, account, test_user)
        task = Task.objects.create(activity=activity)
        assert task.is_overdue is False

    def test_not_overdue_when_due_in_future(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """is_overdue is False when due_at is in the future."""
        future = timezone.now() + timedelta(days=1)
        activity = make_activity(db, account, test_user, due_at=future)
        task = Task.objects.create(activity=activity)
        assert task.is_overdue is False

    def test_overdue_when_due_in_past_and_open(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """is_overdue is True when due_at is in the past and state is open."""
        past = timezone.now() - timedelta(days=1)
        activity = make_activity(db, account, test_user, due_at=past)
        task = Task.objects.create(activity=activity, state=TaskState.OPEN)
        assert task.is_overdue is True

    def test_not_overdue_when_completed_even_if_past_due(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """is_overdue is False when state is completed, regardless of due_at."""
        past = timezone.now() - timedelta(days=1)
        activity = make_activity(db, account, test_user, due_at=past)
        task = Task.objects.create(activity=activity, state=TaskState.COMPLETED)
        assert task.is_overdue is False


class TestTaskEnums:
    """Test Task enum choices."""

    def test_priority_choices(self):
        """Priority choices have the expected values."""
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"

    def test_category_choices(self):
        """Category choices have the expected values."""
        assert TaskCategory.FOLLOW_UP == "follow_up"
        assert TaskCategory.ADMIN == "admin"
        assert TaskCategory.CUSTOMER == "customer"

    def test_state_choices(self):
        """State choices have the expected values."""
        assert TaskState.OPEN == "open"
        assert TaskState.COMPLETED == "completed"


class TestTaskOrdering:
    """Test Task default ordering."""

    def test_ordered_by_activity_created_at_descending(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Meta.ordering declares descending activity.created_at."""
        assert Task._meta.ordering == ["-activity__created_at"]
