"""Unit tests for Meeting model."""

import pytest
from django.db import IntegrityError

from core.models import (
    Activity,
    ActivityType,
    Contact,
    Meeting,
    MeetingContactAssoc,
    MeetingOutcome,
    MeetingUserAssoc,
)


def make_activity(db, account, test_user, **kwargs):
    """Create a minimal Activity(type=meeting) for use in Meeting tests."""
    defaults = dict(
        type=ActivityType.MEETING,
        title="Test Meeting Activity",
        owner_user=test_user,
        account=account,
        created_by=test_user,
    )
    defaults.update(kwargs)
    return Activity.objects.create(**defaults)


class TestMeetingCreation:
    """Test Meeting model creation."""

    def test_create_with_required_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Meeting can be created with only an activity link."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)

        assert meeting.activity == activity
        assert meeting.id is not None
        assert meeting.start_time is None
        assert meeting.end_time is None
        assert meeting.location is None
        assert meeting.meeting_url is None
        assert meeting.outcome is None
        assert meeting.summary is None

    def test_create_with_all_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Meeting can be created with all optional fields populated."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(
            activity=activity,
            start_time="2026-06-01T10:00:00Z",
            end_time="2026-06-01T11:00:00Z",
            location="Conference Room A",
            meeting_url="https://meet.example.com/abc",
            outcome=MeetingOutcome.COMPLETED,
            summary="Discussed renewal terms.",
        )

        assert meeting.location == "Conference Room A"
        assert meeting.meeting_url == "https://meet.example.com/abc"
        assert meeting.outcome == MeetingOutcome.COMPLETED
        assert meeting.summary == "Discussed renewal terms."

    def test_str_returns_activity_title(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """__str__ delegates to the parent activity's title."""
        activity = make_activity(db, account, test_user, title="Acme Demo")
        meeting = Meeting.objects.create(activity=activity)
        assert str(meeting) == "Acme Demo"

    def test_one_to_one_constraint(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """A second Meeting cannot be created for the same Activity."""
        activity = make_activity(db, account, test_user)
        Meeting.objects.create(activity=activity)
        with pytest.raises(IntegrityError):
            Meeting.objects.create(activity=activity)

    def test_cascade_delete_removes_meeting(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Deleting the parent Activity cascades to the Meeting row."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        meeting_id = meeting.id
        activity.delete()
        assert not Meeting.objects.filter(id=meeting_id).exists()

    def test_outcome_choices(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """All MeetingOutcome values can be stored."""
        activity = make_activity(db, account, test_user)
        for outcome in MeetingOutcome:
            meeting = Meeting.objects.create(activity=activity, outcome=outcome)
            assert meeting.outcome == outcome
            meeting.delete()
            activity.refresh_from_db()


class TestMeetingUserAssoc:
    """Test MeetingUserAssoc join table."""

    def test_create_association(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """User can be added as a participant to a Meeting."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        assoc = MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)

        assert assoc.meeting == meeting
        assert assoc.user == test_user
        assert assoc.created_at is not None

    def test_unique_constraint_prevents_duplicates(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """The same user cannot be added to the same Meeting twice."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)
        with pytest.raises(IntegrityError):
            MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)

    def test_multiple_users_per_meeting(
        self, db, account, test_user, test_user_2
    ):  # pylint: disable=unused-argument
        """A Meeting can have multiple user participants."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)
        MeetingUserAssoc.objects.create(meeting=meeting, user=test_user_2)
        assert meeting.user_participants.count() == 2

    def test_cascade_delete_meeting(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Deleting a Meeting cascades to its user participant rows."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)
        meeting.delete()
        assert MeetingUserAssoc.objects.count() == 0

    def test_str_representation(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """__str__ of MeetingUserAssoc includes meeting and user."""
        activity = make_activity(db, account, test_user, title="Acme Demo")
        meeting = Meeting.objects.create(activity=activity)
        assoc = MeetingUserAssoc.objects.create(meeting=meeting, user=test_user)
        assert str(assoc) == f"Acme Demo - {test_user}"


class TestMeetingContactAssoc:
    """Test MeetingContactAssoc join table."""

    def test_create_association(
        self, db, account, test_user, contact
    ):  # pylint: disable=unused-argument
        """Contact can be added as a participant to a Meeting."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        assoc = MeetingContactAssoc.objects.create(meeting=meeting, contact=contact)

        assert assoc.meeting == meeting
        assert assoc.contact == contact
        assert assoc.created_at is not None

    def test_unique_constraint_prevents_duplicates(
        self, db, account, test_user, contact
    ):  # pylint: disable=unused-argument
        """The same contact cannot be added to the same Meeting twice."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        MeetingContactAssoc.objects.create(meeting=meeting, contact=contact)
        with pytest.raises(IntegrityError):
            MeetingContactAssoc.objects.create(meeting=meeting, contact=contact)

    def test_multiple_contacts_per_meeting(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """A Meeting can have multiple contact participants."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        contact1 = Contact.objects.create(first_name="Alice", account=account)
        contact2 = Contact.objects.create(first_name="Bob", account=account)
        MeetingContactAssoc.objects.create(meeting=meeting, contact=contact1)
        MeetingContactAssoc.objects.create(meeting=meeting, contact=contact2)
        assert meeting.contact_participants.count() == 2

    def test_cascade_delete_meeting(
        self, db, account, test_user, contact
    ):  # pylint: disable=unused-argument
        """Deleting a Meeting cascades to its contact participant rows."""
        activity = make_activity(db, account, test_user)
        meeting = Meeting.objects.create(activity=activity)
        MeetingContactAssoc.objects.create(meeting=meeting, contact=contact)
        meeting.delete()
        assert MeetingContactAssoc.objects.count() == 0

    def test_str_representation(
        self, db, account, test_user, contact
    ):  # pylint: disable=unused-argument
        """__str__ of MeetingContactAssoc includes meeting and contact."""
        activity = make_activity(db, account, test_user, title="Acme Demo")
        meeting = Meeting.objects.create(activity=activity)
        assoc = MeetingContactAssoc.objects.create(meeting=meeting, contact=contact)
        assert str(assoc) == f"Acme Demo - {contact}"
