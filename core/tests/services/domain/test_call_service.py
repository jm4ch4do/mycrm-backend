"""Tests for CallService business logic."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import (
    ActivityStatus,
    ActivityType,
    CallDirection,
    CallOutcome,
)
from core.services.domain.call_service import CallService


@pytest.mark.django_db
class TestCallServiceCreate:
    """Test CallService.create_call."""

    def test_creates_activity_correctly(self, test_user, account):
        """create_call produces an Activity with type=call, owner, and created_by."""
        call = CallService.create_call(
            {"title": "Follow-up", "account": account, "direction": "outbound"},
            test_user,
        )
        assert call.activity.type == ActivityType.CALL
        assert call.activity.owner_user == test_user
        assert call.activity.created_by == test_user

    def test_fields_routed_to_correct_model(self, test_user, account):
        """Activity-level and call-level fields land on the right row."""
        call = CallService.create_call(
            {
                "title": "Cold Call",
                "description": "Prospecting",
                "account": account,
                "direction": CallDirection.INBOUND,
                "phone_number": "+1-555-0100",
                "duration_seconds": 180,
            },
            test_user,
        )
        assert call.activity.title == "Cold Call"
        assert call.activity.description == "Prospecting"
        assert call.direction == CallDirection.INBOUND
        assert call.phone_number == "+1-555-0100"
        assert call.duration_seconds == 180

    def test_direction_required(self, test_user, account):
        """create_call raises ValidationError when direction is missing."""
        with pytest.raises(ValidationError):
            CallService.create_call({"title": "No Direction", "account": account}, test_user)

    def test_unknown_fields_ignored(self, test_user, account):
        """Unknown fields in data are silently dropped."""
        call = CallService.create_call(
            {"title": "Demo", "account": account, "direction": "outbound", "bogus": "X"},
            test_user,
        )
        assert call.activity.title == "Demo"


@pytest.mark.django_db
class TestCallServiceUpdate:
    """Test CallService.update_call."""

    def _make_call(self, test_user, account):
        return CallService.create_call(
            {"title": "Original", "account": account, "direction": "outbound"},
            test_user,
        )

    def test_updates_activity_and_call_fields(self, test_user, account):
        """update_call writes to both activity and call rows."""
        call = self._make_call(test_user, account)
        updated = CallService.update_call(
            call, {"title": "Renamed", "phone_number": "+1-555-9999"}, test_user
        )
        updated.refresh_from_db()
        assert updated.activity.title == "Renamed"
        assert updated.phone_number == "+1-555-9999"

    def test_sets_updated_by_and_ignores_immutable(self, test_user, test_user_2, account):
        """update_call sets updated_by and silently strips id/created_at."""
        call = self._make_call(test_user, account)
        original_id = call.id
        CallService.update_call(call, {"id": "new-id", "title": "Changed"}, test_user_2)
        call.activity.refresh_from_db()
        assert call.activity.updated_by == test_user_2
        assert call.id == original_id

    def test_raises_if_already_completed(self, test_user, account):
        """update_call raises ValidationError when call is already completed."""
        call = self._make_call(test_user, account)
        CallService.complete_call(call, CallOutcome.CONNECTED, None, None, test_user)
        call.activity.refresh_from_db()
        with pytest.raises(ValidationError, match="completed"):
            CallService.update_call(call, {"title": "Too late"}, test_user)


@pytest.mark.django_db
class TestCallServiceComplete:
    """Test CallService.complete_call."""

    def test_sets_outcome_summary_and_duration(self, test_user, account):
        """complete_call stores outcome, summary, and duration on the call."""
        call = CallService.create_call(
            {"title": "Demo", "account": account, "direction": "outbound"}, test_user
        )
        completed = CallService.complete_call(
            call, CallOutcome.NO_ANSWER, "Went to voicemail.", 120, test_user
        )
        assert completed.outcome == CallOutcome.NO_ANSWER
        assert completed.summary == "Went to voicemail."
        assert completed.duration_seconds == 120

    def test_marks_activity_completed(self, test_user, test_user_2, account):
        """complete_call sets activity status, completed_at, and updated_by."""
        before = timezone.now()
        call = CallService.create_call(
            {"title": "Demo", "account": account, "direction": "outbound"}, test_user
        )
        completed = CallService.complete_call(
            call, CallOutcome.CONNECTED, None, None, test_user_2
        )
        assert completed.activity.status == ActivityStatus.COMPLETED
        assert completed.activity.completed_at >= before
        assert completed.activity.updated_by == test_user_2

    def test_raises_if_already_completed(self, test_user, account):
        """complete_call raises ValidationError when already completed."""
        call = CallService.create_call(
            {"title": "Demo", "account": account, "direction": "outbound"}, test_user
        )
        CallService.complete_call(call, CallOutcome.CONNECTED, None, None, test_user)
        call.activity.refresh_from_db()
        with pytest.raises(ValidationError, match="completed"):
            CallService.complete_call(call, CallOutcome.BUSY, None, None, test_user)


@pytest.mark.django_db
class TestCallServiceSoftDelete:
    """Test CallService.soft_delete_call."""

    def test_soft_delete_marks_activity(self, test_user, test_user_2, account):
        """soft_delete sets is_invalid=True and updated_by on the activity."""
        call = CallService.create_call(
            {"title": "Remove me", "account": account, "direction": "outbound"}, test_user
        )
        CallService.soft_delete_call(call, test_user_2)
        call.activity.refresh_from_db()
        assert call.activity.is_invalid is True
        assert call.activity.updated_by == test_user_2

    def test_list_excludes_soft_deleted(self, test_user, account):
        """list_calls does not return soft-deleted calls."""
        call = CallService.create_call(
            {"title": "Gone", "account": account, "direction": "outbound"}, test_user
        )
        CallService.soft_delete_call(call, test_user)
        assert not CallService.list_calls().filter(id=call.id).exists()


@pytest.mark.django_db
class TestCallServiceList:
    """Test CallService.list_calls."""

    def test_returns_active_calls(self, test_user, account):
        """list_calls returns calls whose activity is not soft-deleted."""
        call = CallService.create_call(
            {"title": "Active", "account": account, "direction": "outbound"}, test_user
        )
        assert CallService.list_calls().filter(id=call.id).exists()
