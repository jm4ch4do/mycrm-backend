"""Unit tests for Celery tasks."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Activity, ActivityStatus, Account
from core.services.external.scan_overdue import scan_overdue_activities

User = get_user_model()


@pytest.mark.django_db
class TestScanOverdueActivities:
    """Test suite for the scan_overdue_activities task."""

    def setup_method(self):
        """Create test user and account for each test."""
        self.user = User.objects.create_user(
            username="taskuser", email="task@example.com", password="testpass"
        )
        self.account = Account.objects.create(
            name="Test Account",
            owner_user=self.user,
        )

    def test_flags_overdue_planned_activity(self):
        """Test that planned activities with past due_at are flagged."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Overdue Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=past_time,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is True
        assert result["flagged"] == 1
        assert result["cleared"] == 0

    def test_flags_overdue_in_progress_activity(self):
        """Test that in-progress activities with past due_at are flagged."""
        past_time = timezone.now() - timedelta(days=2)
        activity = Activity.objects.create(
            type="meeting",
            title="Overdue Meeting",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.IN_PROGRESS,
            due_at=past_time,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is True
        assert result["flagged"] == 1

    def test_does_not_flag_future_activity(self):
        """Test that activities with future due_at are not flagged."""
        future_time = timezone.now() + timedelta(hours=1)
        activity = Activity.objects.create(
            type="call",
            title="Future Call",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=future_time,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["flagged"] == 0

    def test_does_not_flag_completed_activity(self):
        """Test that completed activities are not flagged as overdue."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Completed Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.COMPLETED,
            due_at=past_time,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["flagged"] == 0

    def test_does_not_flag_canceled_activity(self):
        """Test that canceled activities are not flagged as overdue."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Canceled Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.CANCELED,
            due_at=past_time,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["flagged"] == 0

    def test_does_not_flag_soft_deleted_activity(self):
        """Test that soft-deleted activities are not flagged."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Deleted Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=past_time,
            is_invalid=True,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["flagged"] == 0

    def test_does_not_flag_activity_without_due_date(self):
        """Test that activities without due_at are not flagged."""
        activity = Activity.objects.create(
            type="task",
            title="No Due Date",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=None,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["flagged"] == 0

    def test_skips_already_flagged_activities(self):
        """Test that activities already flagged are not counted again."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Already Overdue",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=past_time,
            is_overdue=True,  # Already flagged
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is True
        assert result["flagged"] == 0  # Should not count this one

    def test_clears_flag_when_completed(self):
        """Test that is_overdue is cleared when activity is completed."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Completed Late",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.COMPLETED,
            due_at=past_time,
            is_overdue=True,  # Was overdue, now completed
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["cleared"] == 1
        assert result["flagged"] == 0

    def test_clears_flag_when_due_date_extended(self):
        """Test that is_overdue is cleared when due_at is moved to future."""
        future_time = timezone.now() + timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Rescheduled Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=future_time,
            is_overdue=True,  # Was overdue, now rescheduled
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["cleared"] == 1

    def test_clears_flag_when_due_date_removed(self):
        """Test that is_overdue is cleared when due_at is set to None."""
        activity = Activity.objects.create(
            type="task",
            title="Due Date Removed",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=None,
            is_overdue=True,  # Was overdue, now no due date
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["cleared"] == 1

    def test_clears_flag_when_soft_deleted(self):
        """Test that is_overdue is cleared when activity is soft-deleted."""
        past_time = timezone.now() - timedelta(hours=1)
        activity = Activity.objects.create(
            type="task",
            title="Deleted Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=past_time,
            is_invalid=True,
            is_overdue=True,  # Was overdue, now deleted
        )

        result = scan_overdue_activities()

        activity.refresh_from_db()
        assert activity.is_overdue is False
        assert result["cleared"] == 1

    def test_mixed_scenario(self):
        """Test flagging and clearing in the same run."""
        now = timezone.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # Should be flagged (not yet flagged, overdue, planned)
        activity1 = Activity.objects.create(
            type="task",
            title="New Overdue",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=past,
            is_overdue=False,
        )

        # Should be cleared (was flagged, now completed)
        activity2 = Activity.objects.create(
            type="task",
            title="Completed",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.COMPLETED,
            due_at=past,
            is_overdue=True,
        )

        # Should be cleared (was flagged, now has future due date)
        activity3 = Activity.objects.create(
            type="task",
            title="Rescheduled",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=future,
            is_overdue=True,
        )

        # Should remain unchanged (not overdue, not flagged)
        activity4 = Activity.objects.create(
            type="task",
            title="Future Task",
            owner_user=self.user,
            account=self.account,
            status=ActivityStatus.PLANNED,
            due_at=future,
            is_overdue=False,
        )

        result = scan_overdue_activities()

        activity1.refresh_from_db()
        activity2.refresh_from_db()
        activity3.refresh_from_db()
        activity4.refresh_from_db()

        assert activity1.is_overdue is True  # Newly flagged
        assert activity2.is_overdue is False  # Cleared
        assert activity3.is_overdue is False  # Cleared
        assert activity4.is_overdue is False  # Unchanged

        assert result["flagged"] == 1
        assert result["cleared"] == 2

    def test_returns_summary_dict(self):
        """Test that the task returns a properly structured summary."""
        result = scan_overdue_activities()

        assert "flagged" in result
        assert "cleared" in result
        assert "timestamp" in result
        assert isinstance(result["flagged"], int)
        assert isinstance(result["cleared"], int)
        assert isinstance(result["timestamp"], str)
