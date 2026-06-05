"""Unit tests for Call model."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.models import (
    Activity,
    ActivityType,
    Call,
    CallDirection,
    CallOutcome,
)


def make_activity(db, account, test_user, **kwargs):
    """Create a minimal Activity(type=call) for use in Call tests."""
    defaults = dict(
        type=ActivityType.CALL,
        title="Test Call Activity",
        owner_user=test_user,
        account=account,
        created_by=test_user,
    )
    defaults.update(kwargs)
    return Activity.objects.create(**defaults)


class TestCallCreation:
    """Test Call model creation and field constraints."""

    def test_create_with_required_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Call can be created with only direction and an activity link."""
        activity = make_activity(db, account, test_user)
        call = Call.objects.create(activity=activity, direction=CallDirection.OUTBOUND)

        assert call.activity == activity
        assert call.id is not None
        assert call.direction == CallDirection.OUTBOUND
        assert call.outcome is None
        assert call.phone_number is None
        assert call.duration_seconds is None
        assert call.summary is None

    def test_create_with_all_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Call can be created with all optional fields populated."""
        activity = make_activity(db, account, test_user)
        call = Call.objects.create(
            activity=activity,
            direction=CallDirection.INBOUND,
            outcome=CallOutcome.CONNECTED,
            phone_number="+1-555-0100",
            duration_seconds=300,
            summary="Discussed renewal options.",
        )

        assert call.direction == CallDirection.INBOUND
        assert call.outcome == CallOutcome.CONNECTED
        assert call.phone_number == "+1-555-0100"
        assert call.duration_seconds == 300
        assert call.summary == "Discussed renewal options."

    def test_direction_required(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Omitting direction raises IntegrityError (NOT NULL constraint)."""
        activity = make_activity(db, account, test_user)
        call = Call(activity=activity)
        with pytest.raises((IntegrityError, ValidationError)):
            call.full_clean()

    def test_str_returns_title_and_direction(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """__str__ returns '<title> (<direction>)'."""
        activity = make_activity(db, account, test_user, title="Follow-up Call")
        call = Call.objects.create(activity=activity, direction=CallDirection.OUTBOUND)
        assert str(call) == "Follow-up Call (outbound)"

    def test_one_to_one_constraint(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """A second Call cannot be created for the same Activity."""
        activity = make_activity(db, account, test_user)
        Call.objects.create(activity=activity, direction=CallDirection.OUTBOUND)
        with pytest.raises(IntegrityError):
            Call.objects.create(activity=activity, direction=CallDirection.INBOUND)

    def test_cascade_delete_removes_call(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Deleting the parent Activity cascades to the Call row."""
        activity = make_activity(db, account, test_user)
        call = Call.objects.create(activity=activity, direction=CallDirection.OUTBOUND)
        call_id = call.id
        activity.delete()
        assert not Call.objects.filter(id=call_id).exists()

    def test_soft_delete_via_activity_does_not_delete_call_row(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Setting activity.is_invalid=True leaves the Call row intact."""
        activity = make_activity(db, account, test_user)
        call = Call.objects.create(activity=activity, direction=CallDirection.OUTBOUND)
        activity.is_invalid = True
        activity.save()
        assert Call.objects.filter(id=call.id).exists()

    def test_outcome_choices(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """All CallOutcome values can be stored."""
        activity = make_activity(db, account, test_user)
        for outcome in CallOutcome:
            call = Call.objects.create(
                activity=activity,
                direction=CallDirection.OUTBOUND,
                outcome=outcome,
            )
            assert call.outcome == outcome
            call.delete()
            activity.refresh_from_db()
