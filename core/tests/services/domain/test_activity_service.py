"""Tests for ActivityService business logic."""

from __future__ import annotations

import pytest

from core.models import ActivityType
from core.services.domain.activity_service import ActivityService


@pytest.mark.django_db
class TestActivityService:
    """Test ActivityService business logic."""

    def test_create_activity_sets_owner_and_created_by(self, test_user, account):
        """Test that create_activity sets owner_user and created_by."""
        data = {
            "type": ActivityType.TASK,
            "title": "New Task",
            "account": account,
        }
        activity = ActivityService.create_activity(data, test_user)
        assert activity.owner_user == test_user
        assert activity.created_by == test_user
        assert activity.title == "New Task"

    def test_create_activity_raises_error_on_owner_override(
        self, test_user, test_user_2, account
    ):
        """Test that create_activity raises error when owner_user is in data."""
        data = {
            "type": ActivityType.TASK,
            "title": "Task",
            "account": account,
            "owner_user": test_user_2,
        }
        with pytest.raises(
            TypeError,
            match="got multiple values for keyword argument 'owner_user'",
        ):
            ActivityService.create_activity(data, test_user)

    def test_update_activity_sets_updated_by(self, test_user_2, activity):
        """Test that update_activity sets updated_by to the provided user."""
        data = {"title": "Updated Title"}
        updated = ActivityService.update_activity(activity, data, test_user_2)
        assert updated.title == "Updated Title"
        assert updated.updated_by == test_user_2

    def test_update_activity_prevents_modification_of_immutable_fields(
        self, test_user, activity
    ):
        """Test that update_activity protects id, created_at, created_by."""
        original_id = activity.id
        original_created_at = activity.created_at
        original_created_by = activity.created_by

        data = {
            "id": "new-id",
            "created_at": "2020-01-01T00:00:00Z",
            "created_by": test_user,
            "title": "Updated",
        }
        updated = ActivityService.update_activity(activity, data, test_user)

        assert updated.id == original_id
        assert updated.created_at == original_created_at
        assert updated.created_by == original_created_by
        assert updated.title == "Updated"

    def test_soft_delete_sets_is_invalid(self, test_user, activity):
        """Test that soft_delete_activity sets is_invalid=True."""
        assert activity.is_invalid is False
        deleted = ActivityService.soft_delete_activity(activity, test_user)
        assert deleted.is_invalid is True

    def test_soft_delete_sets_updated_by(self, test_user_2, activity):
        """Test that soft_delete_activity sets updated_by."""
        deleted = ActivityService.soft_delete_activity(activity, test_user_2)
        assert deleted.updated_by == test_user_2

    def test_list_activities_excludes_invalid(self, test_user, account):
        """Test that list_activities filters out is_invalid=True records."""
        ActivityService.create_activity(
            {"type": ActivityType.TASK, "title": "Active", "account": account},
            test_user,
        )
        invalid = ActivityService.create_activity(
            {"type": ActivityType.TASK, "title": "Deleted", "account": account},
            test_user,
        )
        ActivityService.soft_delete_activity(invalid, test_user)

        results = ActivityService.list_activities()
        assert results.filter(title="Active").exists()
        assert not results.filter(title="Deleted").exists()

    def test_get_activity_returns_correct_instance(self, activity):
        """Test that get_activity returns the correct activity."""
        fetched = ActivityService.get_activity(activity.id)
        assert fetched.id == activity.id
