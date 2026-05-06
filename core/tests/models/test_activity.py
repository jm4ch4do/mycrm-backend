"""Unit tests for Activity model."""

import pytest

from core.models import Activity, ActivityStatus, ActivityType


class TestActivityCreation:
    """Test Activity model creation."""

    def test_create_with_required_fields(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test creating an activity with only required fields."""
        activity = Activity.objects.create(
            type=ActivityType.TASK,
            title="Follow up",
            owner_user=test_user,
            account=account,
        )
        assert activity.title == "Follow up"
        assert activity.type == ActivityType.TASK
        assert activity.owner_user == test_user
        assert activity.status == ActivityStatus.PLANNED
        assert activity.is_invalid is False

    def test_create_linked_to_contact(
        self, db, test_user, contact
    ):  # pylint: disable=unused-argument
        """Test creating an activity linked to a contact."""
        activity = Activity.objects.create(
            type=ActivityType.CALL,
            title="Discovery call",
            owner_user=test_user,
            contact=contact,
        )
        assert activity.contact == contact
        assert activity.account is None
        assert activity.deal is None

    def test_create_linked_to_deal(
        self, db, test_user, deal
    ):  # pylint: disable=unused-argument
        """Test creating an activity linked to a deal."""
        activity = Activity.objects.create(
            type=ActivityType.MEETING,
            title="Demo meeting",
            owner_user=test_user,
            deal=deal,
        )
        assert activity.deal == deal

    def test_create_linked_to_multiple_entities(
        self, db, test_user, account, contact, deal
    ):  # pylint: disable=unused-argument
        """Test creating an activity linked to account, contact, and deal."""
        activity = Activity.objects.create(
            type=ActivityType.CALL,
            title="Multi-context call",
            owner_user=test_user,
            account=account,
            contact=contact,
            deal=deal,
        )
        assert activity.account == account
        assert activity.contact == contact
        assert activity.deal == deal

    def test_default_status_is_planned(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test that status defaults to PLANNED."""
        activity = Activity.objects.create(
            type=ActivityType.TASK,
            title="New task",
            owner_user=test_user,
            account=account,
        )
        assert activity.status == ActivityStatus.PLANNED

    def test_is_invalid_defaults_to_false(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test that is_invalid defaults to False."""
        activity = Activity.objects.create(
            type=ActivityType.TASK,
            title="Test",
            owner_user=test_user,
            account=account,
        )
        assert activity.is_invalid is False

    def test_str_returns_title(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test __str__ returns the title."""
        activity = Activity.objects.create(
            type=ActivityType.TASK,
            title="My Task",
            owner_user=test_user,
            account=account,
        )
        assert str(activity) == "My Task"


class TestActivityEnums:
    """Test ActivityType and ActivityStatus enum values."""

    def test_activity_type_values(self):
        """Test all ActivityType choices are defined."""
        assert ActivityType.TASK == "task"
        assert ActivityType.MEETING == "meeting"
        assert ActivityType.CALL == "call"
        assert ActivityType.NOTE == "note"

    def test_activity_status_values(self):
        """Test all ActivityStatus choices are defined."""
        assert ActivityStatus.PLANNED == "planned"
        assert ActivityStatus.IN_PROGRESS == "in_progress"
        assert ActivityStatus.COMPLETED == "completed"
        assert ActivityStatus.CANCELED == "canceled"


class TestActivityFiltering:
    """Test Activity queryset filtering."""

    def test_filter_by_type(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test filtering activities by type."""
        Activity.objects.create(
            type=ActivityType.TASK, title="Task", owner_user=test_user, account=account
        )
        Activity.objects.create(
            type=ActivityType.CALL, title="Call", owner_user=test_user, account=account
        )
        tasks = Activity.objects.filter(type=ActivityType.TASK)
        assert tasks.count() == 1

    def test_filter_by_status(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test filtering activities by status."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Planned",
            status=ActivityStatus.PLANNED,
            owner_user=test_user,
            account=account,
        )
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Completed",
            status=ActivityStatus.COMPLETED,
            owner_user=test_user,
            account=account,
        )
        planned = Activity.objects.filter(status=ActivityStatus.PLANNED)
        assert planned.count() == 1

    def test_filter_out_invalid(
        self, db, test_user, account
    ):  # pylint: disable=unused-argument
        """Test that is_invalid activities can be filtered out."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Active",
            owner_user=test_user,
            account=account,
            is_invalid=False,
        )
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Deleted",
            owner_user=test_user,
            account=account,
            is_invalid=True,
        )
        active = Activity.objects.filter(is_invalid=False)
        assert active.count() == 1
