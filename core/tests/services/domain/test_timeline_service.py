"""Tests for TimelineService business logic."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.http import Http404

from core.models import Activity, ActivityType, Note
from core.services.domain.timeline_service import TimelineService

user_model = get_user_model()


@pytest.mark.django_db
class TestTimelineServiceGetTimeline:
    """Test TimelineService.get_timeline."""

    def test_returns_activities_and_notes_merged(self, test_user, account):
        """get_timeline returns both Activity and Note items merged."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Follow-up Task",
            owner_user=test_user,
            account=account,
        )
        Note.objects.create(
            body="Initial contact made.",
            author=test_user,
            account=account,
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        types = {item["type"] for item in items}
        assert "task" in types
        assert "note" in types

    def test_sorted_by_created_at_descending(self, test_user, account):
        """get_timeline returns items sorted by created_at descending."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Task A",
            owner_user=test_user,
            account=account,
        )
        Activity.objects.create(
            type=ActivityType.CALL,
            title="Call B",
            owner_user=test_user,
            account=account,
        )
        Note.objects.create(
            body="Note C",
            author=test_user,
            account=account,
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        timestamps = [item["created_at"] for item in items]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_excludes_soft_deleted_activities(self, test_user, account):
        """get_timeline excludes Activities where is_invalid=True."""
        Activity.objects.create(
            type=ActivityType.TASK,
            title="Deleted Task",
            owner_user=test_user,
            account=account,
            is_invalid=True,
        )
        Activity.objects.create(
            type=ActivityType.CALL,
            title="Active Call",
            owner_user=test_user,
            account=account,
            is_invalid=False,
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        titles = [item["title"] for item in items]
        assert "Deleted Task" not in titles
        assert "Active Call" in titles

    def test_excludes_soft_deleted_notes(self, test_user, account):
        """get_timeline excludes Notes where is_invalid=True."""
        Note.objects.create(
            body="Deleted note",
            author=test_user,
            account=account,
            is_invalid=True,
        )
        Note.objects.create(
            body="Active note",
            author=test_user,
            account=account,
            is_invalid=False,
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        bodies = [item["body"] for item in items if item["type"] == "note"]
        assert "Deleted note" not in bodies
        assert "Active note" in bodies

    def test_excludes_private_notes_from_other_user(self, test_user, account):
        """Private notes from another author are hidden from the requesting user."""
        other_user = user_model.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="pass",
        )
        Note.objects.create(
            body="Secret note",
            author=other_user,
            account=account,
            visibility="private",
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        bodies = [item["body"] for item in items if item["type"] == "note"]
        assert "Secret note" not in bodies

    def test_includes_private_notes_for_author(self, test_user, account):
        """Private notes authored by the requesting user are included."""
        Note.objects.create(
            body="My private note",
            author=test_user,
            account=account,
            visibility="private",
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        bodies = [item["body"] for item in items if item["type"] == "note"]
        assert "My private note" in bodies

    def test_includes_private_notes_for_staff(self, account):
        """Staff users can see all private notes regardless of author."""
        regular_user = user_model.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="pass",
        )
        staff_user = user_model.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="pass",
            is_staff=True,
        )
        Note.objects.create(
            body="Private note by regular",
            author=regular_user,
            account=account,
            visibility="private",
        )

        items = TimelineService.get_timeline("account", str(account.pk), staff_user)

        bodies = [item["body"] for item in items if item["type"] == "note"]
        assert "Private note by regular" in bodies

    def test_raises_404_when_entity_does_not_exist(self, test_user):
        """get_timeline raises Http404 when the parent entity is not found."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(Http404):
            TimelineService.get_timeline("account", fake_id, test_user)

    def test_raises_404_when_entity_is_soft_deleted(self, test_user, account):
        """get_timeline raises Http404 when the parent entity is soft-deleted."""
        account.is_invalid = True
        account.save()

        with pytest.raises(Http404):
            TimelineService.get_timeline("account", str(account.pk), test_user)

    def test_each_item_has_type_discriminator(self, test_user, account):
        """Every timeline item contains a type discriminator field."""
        Activity.objects.create(
            type=ActivityType.MEETING,
            title="Kickoff",
            owner_user=test_user,
            account=account,
        )
        Note.objects.create(
            body="Some note",
            author=test_user,
            account=account,
        )

        items = TimelineService.get_timeline("account", str(account.pk), test_user)

        for item in items:
            assert "type" in item
            assert item["type"] is not None

    def test_contact_timeline(self, test_user, contact):
        """get_timeline works for contact entity type."""
        Activity.objects.create(
            type=ActivityType.CALL,
            title="Contact Call",
            owner_user=test_user,
            contact=contact,
        )

        items = TimelineService.get_timeline(
            "contact", str(contact.pk), test_user
        )

        assert len(items) == 1
        assert items[0]["title"] == "Contact Call"

    def test_deal_timeline(self, test_user, deal):
        """get_timeline works for deal entity type."""
        Note.objects.create(
            body="Deal note",
            author=test_user,
            deal=deal,
        )

        items = TimelineService.get_timeline("deal", str(deal.pk), test_user)

        assert len(items) == 1
        assert items[0]["body"] == "Deal note"
