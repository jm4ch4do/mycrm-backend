"""Unit tests for TaskSerializer."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from core.api.serializers.task import TaskSerializer
from core.models import ActivityType, TaskState
from core.services.domain.task_service import TaskService


def _mock_request(user):
    request = MagicMock()
    request.user = user
    return request


@pytest.mark.django_db
class TestTaskSerializerOutput:
    """Test TaskSerializer serialization (read path)."""

    def test_serialized_output_includes_activity_fields(self, test_user, account):
        """Serialized task exposes Activity fields at the top level."""
        task = TaskService.create_task(
            {"title": "Check in", "account": account}, test_user
        )
        data = TaskSerializer(task).data

        assert data["title"] == "Check in"
        assert str(data["account"]) == str(account.id)
        assert data["type"] == ActivityType.TASK
        assert data["activity_id"] == str(task.activity.id)
        assert data["owner_user"] == test_user.id

    def test_serialized_output_includes_task_fields(self, test_user, account):
        """Serialized task exposes Task-own fields."""
        task = TaskService.create_task(
            {
                "title": "Call back",
                "account": account,
                "priority": "high",
                "category": "follow_up",
            },
            test_user,
        )
        data = TaskSerializer(task).data

        assert data["priority"] == "high"
        assert data["category"] == "follow_up"
        assert data["state"] == TaskState.OPEN

    def test_is_overdue_in_output(self, test_user, account):
        """Serialized task exposes is_overdue property."""
        task = TaskService.create_task(
            {"title": "Check in", "account": account}, test_user
        )
        data = TaskSerializer(task).data
        assert "is_overdue" in data
        assert data["is_overdue"] is False

    def test_activity_status_in_output(self, test_user, account):
        """Serialized task exposes activity_status separately from task status."""
        task = TaskService.create_task(
            {"title": "Check in", "account": account}, test_user
        )
        data = TaskSerializer(task).data
        assert "activity_status" in data

    def test_read_only_fields_present(self, test_user, account):
        """Read-only derived fields are present in output."""
        task = TaskService.create_task({"title": "X", "account": account}, test_user)
        data = TaskSerializer(task).data
        for field in (
            "id",
            "activity_id",
            "type",
            "owner_user",
            "created_at",
            "updated_at",
            "created_by",
            "is_overdue",
        ):
            assert field in data


@pytest.mark.django_db
class TestTaskSerializerValidation:
    """Test TaskSerializer validation (write path)."""

    def _make_request(self, test_user):
        return _mock_request(test_user)

    def test_valid_with_account(self, test_user, account):
        """Serializer is valid when account is supplied."""
        data = {"title": "Task A", "account": str(account.id)}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_contact(self, test_user, account, contact):
        """Serializer is valid when contact is supplied (no account)."""
        data = {"title": "Task B", "contact": str(contact.id)}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_deal(self, test_user, account, deal):
        """Serializer is valid when deal is supplied (no account)."""
        data = {"title": "Task C", "deal": str(deal.id)}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert serializer.is_valid(), serializer.errors

    def test_invalid_when_no_entity_reference(self, test_user):
        """Serializer rejects data with no account, contact, or deal."""
        data = {"title": "Orphan task"}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors or any(
            "account" in str(v)
            or "contact" in str(v)
            or "deal" in str(v)
            or "at least" in str(v).lower()
            for v in serializer.errors.values()
        )

    def test_title_required(self, test_user, account):
        """Serializer rejects data without a title."""
        data = {"account": str(account.id)}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert not serializer.is_valid()

    def test_invalid_priority_choice(self, test_user, account):
        """Serializer rejects invalid priority value."""
        data = {"title": "Task", "account": str(account.id), "priority": "urgent"}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert not serializer.is_valid()
        assert "priority" in serializer.errors

    def test_invalid_category_choice(self, test_user, account):
        """Serializer rejects invalid category value."""
        data = {"title": "Task", "account": str(account.id), "category": "personal"}
        serializer = TaskSerializer(
            data=data, context={"request": self._make_request(test_user)}
        )
        assert not serializer.is_valid()
        assert "category" in serializer.errors


@pytest.mark.django_db
class TestTaskSerializerCreate:
    """Test TaskSerializer.create (delegates to TaskService)."""

    def test_create_produces_task_with_correct_title(self, test_user, account):
        """Serializer create round-trip produces a persisted Task."""
        data = {"title": "Call back", "account": str(account.id), "priority": "medium"}
        serializer = TaskSerializer(
            data=data, context={"request": _mock_request(test_user)}
        )
        assert serializer.is_valid(), serializer.errors
        task = serializer.save()
        assert task.activity.title == "Call back"
        assert task.priority == "medium"

    def test_create_sets_owner_from_request_user(self, test_user, account):
        """owner_user on the created activity is taken from request.user."""
        data = {"title": "My task", "account": str(account.id)}
        serializer = TaskSerializer(
            data=data, context={"request": _mock_request(test_user)}
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        assert task.activity.owner_user == test_user


@pytest.mark.django_db
class TestTaskSerializerUpdate:
    """Test TaskSerializer.update (delegates to TaskService)."""

    def test_update_changes_title(self, test_user, account):
        """Partial update via serializer changes the activity title."""
        task = TaskService.create_task(
            {"title": "Original", "account": account}, test_user
        )
        serializer = TaskSerializer(
            task,
            data={"title": "Updated", "account": str(account.id)},
            context={"request": _mock_request(test_user)},
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.activity.title == "Updated"

    def test_partial_update_preserves_unchanged_fields(self, test_user, account):
        """PATCH (partial=True) does not wipe out fields not included in data."""
        task = TaskService.create_task(
            {"title": "Keep me", "account": account, "priority": "high"}, test_user
        )
        serializer = TaskSerializer(
            task,
            data={"priority": "low"},
            partial=True,
            context={"request": _mock_request(test_user)},
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        # Title should still be "Keep me" since it wasn't in the PATCH payload
        updated.activity.refresh_from_db()
        assert updated.activity.title == "Keep me"
        assert updated.priority == "low"
