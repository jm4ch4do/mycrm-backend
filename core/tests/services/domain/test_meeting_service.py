"""Tests for MeetingService business logic."""

from __future__ import annotations

import pytest
from django.utils import timezone

from core.models import (
    ActivityStatus,
    ActivityType,
    MeetingContactAssoc,
    MeetingOutcome,
    MeetingUserAssoc,
)
from core.services.domain.meeting_service import MeetingService


@pytest.mark.django_db
class TestMeetingServiceCreate:
    """Test MeetingService.create_meeting."""

    def test_creates_activity_correctly(self, test_user, account):
        """create_meeting produces an Activity with type, owner and created_by set."""
        meeting = MeetingService.create_meeting(
            {"title": "Acme Demo", "account": account}, test_user
        )
        assert meeting.activity.type == ActivityType.MEETING
        assert meeting.activity.owner_user == test_user
        assert meeting.activity.created_by == test_user

    def test_fields_routed_to_correct_model(self, test_user, account):
        """Activity-level and meeting-level fields are stored on the right row."""
        meeting = MeetingService.create_meeting(
            {
                "title": "Renewal Review",
                "description": "Q3 discussion",
                "account": account,
                "location": "Room B",
                "meeting_url": "https://meet.example.com/xyz",
            },
            test_user,
        )
        assert meeting.activity.title == "Renewal Review"
        assert meeting.activity.description == "Q3 discussion"
        assert meeting.location == "Room B"
        assert meeting.meeting_url == "https://meet.example.com/xyz"

    def test_defaults_and_unknown_fields(self, test_user, account):
        """outcome defaults to None; unknown fields are silently dropped."""
        meeting = MeetingService.create_meeting(
            {"title": "Demo", "account": account, "bogus_field": "X"}, test_user
        )
        assert meeting.outcome is None
        assert meeting.activity.title == "Demo"


@pytest.mark.django_db
class TestMeetingServiceUpdate:
    """Test MeetingService.update_meeting."""

    def _make_meeting(self, test_user, account):
        return MeetingService.create_meeting(
            {"title": "Original", "account": account, "location": "Room A"},
            test_user,
        )

    def test_updates_activity_and_meeting_fields(self, test_user, account):
        """update_meeting writes to both the activity and the meeting row."""
        meeting = self._make_meeting(test_user, account)
        updated = MeetingService.update_meeting(
            meeting, {"title": "Renamed", "location": "Room C"}, test_user
        )
        updated.refresh_from_db()
        assert updated.activity.title == "Renamed"
        assert updated.location == "Room C"

    def test_sets_updated_by_and_ignores_immutable(
        self, test_user, test_user_2, account
    ):
        """update_meeting sets updated_by and silently strips id/created_at."""
        meeting = self._make_meeting(test_user, account)
        original_id = meeting.id
        MeetingService.update_meeting(
            meeting, {"id": "new-id", "title": "Changed"}, test_user_2
        )
        meeting.activity.refresh_from_db()
        assert meeting.activity.updated_by == test_user_2
        assert meeting.id == original_id

    def test_raises_if_outcome_already_set(self, test_user, account):
        """update_meeting raises ValueError when meeting has an outcome."""
        meeting = self._make_meeting(test_user, account)
        MeetingService.complete_meeting(
            meeting, MeetingOutcome.COMPLETED, None, test_user
        )
        meeting.refresh_from_db()
        with pytest.raises(ValueError, match="outcome"):
            MeetingService.update_meeting(meeting, {"title": "Too late"}, test_user)


@pytest.mark.django_db
class TestMeetingServiceComplete:
    """Test MeetingService.complete_meeting."""

    def test_sets_outcome_and_summary(self, test_user, account):
        """complete_meeting stores outcome and summary on the meeting."""
        meeting = MeetingService.create_meeting(
            {"title": "Demo", "account": account}, test_user
        )
        completed = MeetingService.complete_meeting(
            meeting, MeetingOutcome.NO_SHOW, "Client did not join.", test_user
        )
        assert completed.outcome == MeetingOutcome.NO_SHOW
        assert completed.summary == "Client did not join."

    def test_marks_activity_complete(self, test_user, test_user_2, account):
        """complete_meeting sets activity status, completed_at, and updated_by."""
        before = timezone.now()
        meeting = MeetingService.create_meeting(
            {"title": "Demo", "account": account}, test_user
        )
        completed = MeetingService.complete_meeting(
            meeting, MeetingOutcome.COMPLETED, None, test_user_2
        )
        assert completed.activity.status == ActivityStatus.COMPLETED
        assert completed.activity.completed_at >= before
        assert completed.activity.updated_by == test_user_2


@pytest.mark.django_db
class TestMeetingServiceSoftDelete:
    """Test MeetingService.soft_delete_meeting."""

    def test_soft_delete_marks_activity(self, test_user, test_user_2, account):
        """soft_delete sets is_invalid=True and updated_by on the activity."""
        meeting = MeetingService.create_meeting(
            {"title": "Remove me", "account": account}, test_user
        )
        MeetingService.soft_delete_meeting(meeting, test_user_2)
        meeting.activity.refresh_from_db()
        assert meeting.activity.is_invalid is True
        assert meeting.activity.updated_by == test_user_2

    def test_list_excludes_soft_deleted(self, test_user, account):
        """list_meetings does not return soft-deleted meetings."""
        meeting = MeetingService.create_meeting(
            {"title": "Gone", "account": account}, test_user
        )
        MeetingService.soft_delete_meeting(meeting, test_user)
        assert not MeetingService.list_meetings().filter(id=meeting.id).exists()


@pytest.mark.django_db
class TestMeetingServiceList:
    """Test MeetingService.list_meetings."""

    def test_returns_active_meetings(self, test_user, account):
        """list_meetings returns meetings whose activity is not soft-deleted."""
        meeting = MeetingService.create_meeting(
            {"title": "Active", "account": account}, test_user
        )
        assert MeetingService.list_meetings().filter(id=meeting.id).exists()


@pytest.mark.django_db
class TestMeetingServiceParticipants:
    """Test participant management methods."""

    def _make_meeting(self, test_user, account):
        return MeetingService.create_meeting(
            {"title": "Team Sync", "account": account}, test_user
        )

    def test_user_participant_add_and_remove(self, test_user, test_user_2, account):
        """add and remove a user participant."""
        meeting = self._make_meeting(test_user, account)
        assoc = MeetingService.add_user_participant(meeting, test_user_2)
        assert isinstance(assoc, MeetingUserAssoc)
        MeetingService.remove_user_participant(meeting, test_user_2.id)
        assert meeting.user_participants.count() == 0

    def test_contact_participant_add_and_remove(self, test_user, account, contact):
        """add and remove a contact participant."""
        meeting = self._make_meeting(test_user, account)
        assoc = MeetingService.add_contact_participant(meeting, contact)
        assert isinstance(assoc, MeetingContactAssoc)
        MeetingService.remove_contact_participant(meeting, contact.id)
        assert meeting.contact_participants.count() == 0
