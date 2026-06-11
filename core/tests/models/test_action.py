"""Unit tests for Action model."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Action, ActionType


@pytest.mark.django_db
class TestActionModel:
    """Tests for Action model fields, defaults, and behavior."""

    def test_action_str_returns_name_and_type(self):
        """__str__ returns '<name> (<action_type>)'."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
        )

        assert str(action) == "Create Qualification Task (create_task)"

    def test_action_requires_name(self):
        """name is required."""
        action = Action(action_type=ActionType.CREATE_TASK)

        with pytest.raises(ValidationError):
            action.full_clean()

    def test_action_requires_action_type(self):
        """action_type is required."""
        action = Action(name="Create Qualification Task")

        with pytest.raises(ValidationError):
            action.full_clean()

    def test_action_parameters_nullable(self):
        """parameters can be null."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            parameters=None,
        )

        assert action.parameters is None

    def test_action_retry_policy_nullable(self):
        """retry_policy can be null."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            retry_policy=None,
        )

        assert action.retry_policy is None

    def test_action_timeout_seconds_nullable(self):
        """timeout_seconds can be null."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
            timeout_seconds=None,
        )

        assert action.timeout_seconds is None

    def test_action_soft_delete_sets_is_invalid(self):
        """Action supports soft delete through is_invalid flag."""
        action = Action.objects.create(
            name="Create Qualification Task",
            action_type=ActionType.CREATE_TASK,
        )

        action.is_invalid = True
        action.save()

        action.refresh_from_db()
        assert action.is_invalid is True

    def test_action_ordering_is_newest_first(self):
        """Meta ordering returns newest actions first."""
        older = Action.objects.create(
            name="Older Action",
            action_type=ActionType.CREATE_TASK,
        )
        older.created_at = timezone.now() - timedelta(minutes=5)
        older.save(update_fields=["created_at"])

        newer = Action.objects.create(
            name="Newer Action",
            action_type=ActionType.ADD_NOTE,
        )

        actions = list(Action.objects.all())

        assert actions[0] == newer
        assert actions[1] == older