"""Tests for TriggerService business logic."""

from __future__ import annotations

import pytest
from django.http import Http404

from core.models import Trigger
from core.services.domain.trigger_service import TriggerService


@pytest.mark.django_db
class TestTriggerServiceWrite:
    """Test TriggerService write operations."""

    def test_create_trigger_sets_audit_fields(self, test_user):
        """create_trigger sets created_by and updated_by."""
        trigger = TriggerService.create_trigger(
            {
                "name": "Qualified deal trigger",
                "event_type": "deal.updated",
                "entity_type": "Deal",
                "conditions": {"stage": "qualified"},
            },
            test_user,
        )

        assert trigger.created_by == test_user
        assert trigger.updated_by == test_user
        assert trigger.event_type == "deal.updated"

    def test_create_trigger_requires_dot_notation_event_type(self, test_user):
        """create_trigger raises ValueError for invalid event_type."""
        with pytest.raises(ValueError, match="dot-notation"):
            TriggerService.create_trigger(
                {
                    "name": "Invalid trigger",
                    "event_type": "deal_updated",
                },
                test_user,
            )

    def test_update_trigger_sets_updated_by_and_mutable_fields(self, test_user, test_user_2):
        """update_trigger updates mutable fields and sets updated_by."""
        trigger = Trigger.objects.create(
            name="Deal trigger",
            event_type="deal.updated",
            entity_type="Deal",
            created_by=test_user,
        )

        updated = TriggerService.update_trigger(
            trigger,
            {
                "name": "Updated trigger",
                "conditions": {"stage": "proposal"},
            },
            test_user_2,
        )

        assert updated.name == "Updated trigger"
        assert updated.conditions == {"stage": "proposal"}
        assert updated.updated_by == test_user_2

    def test_update_trigger_rejects_invalid_event_type(self, test_user):
        """update_trigger validates event_type when provided."""
        trigger = Trigger.objects.create(
            name="Deal trigger",
            event_type="deal.updated",
            created_by=test_user,
        )

        with pytest.raises(ValueError, match="dot-notation"):
            TriggerService.update_trigger(
                trigger,
                {"event_type": "deal_updated"},
                test_user,
            )

    def test_delete_trigger_soft_deletes_and_deactivates(self, test_user, test_user_2):
        """delete_trigger marks trigger invalid/inactive and sets updated_by."""
        trigger = Trigger.objects.create(
            name="Deal trigger",
            event_type="deal.updated",
            is_active=True,
            created_by=test_user,
        )

        deleted = TriggerService.delete_trigger(trigger, test_user_2)

        assert deleted.is_invalid is True
        assert deleted.is_active is False
        assert deleted.updated_by == test_user_2


@pytest.mark.django_db
class TestTriggerServiceRead:
    """Test TriggerService read operations."""

    def test_get_trigger_returns_non_deleted_record(self, test_user):
        """get_trigger returns a non-deleted trigger."""
        trigger = Trigger.objects.create(
            name="Deal trigger",
            event_type="deal.updated",
            created_by=test_user,
        )

        fetched = TriggerService.get_trigger(str(trigger.id))
        assert fetched.id == trigger.id

    def test_get_trigger_raises_for_deleted_record(self, test_user):
        """get_trigger raises Http404 for soft-deleted trigger."""
        trigger = Trigger.objects.create(
            name="Deleted trigger",
            event_type="deal.updated",
            is_invalid=True,
            created_by=test_user,
        )

        with pytest.raises(Http404):
            TriggerService.get_trigger(str(trigger.id))

    def test_list_triggers_excludes_soft_deleted(self, test_user):
        """list_triggers returns only non-deleted triggers."""
        Trigger.objects.create(
            name="Active trigger",
            event_type="deal.updated",
            is_invalid=False,
            created_by=test_user,
        )
        Trigger.objects.create(
            name="Deleted trigger",
            event_type="deal.updated",
            is_invalid=True,
            created_by=test_user,
        )

        triggers = list(TriggerService.list_triggers())

        assert len(triggers) == 1
        assert triggers[0].name == "Active trigger"

    def test_list_triggers_filters_by_allowed_fields(self, test_user):
        """list_triggers applies allowed filters only."""
        Trigger.objects.create(
            name="Deal active",
            event_type="deal.updated",
            entity_type="Deal",
            is_active=True,
            created_by=test_user,
        )
        Trigger.objects.create(
            name="Deal inactive",
            event_type="deal.updated",
            entity_type="Deal",
            is_active=False,
            created_by=test_user,
        )

        triggers = list(TriggerService.list_triggers({"is_active": True}))

        assert len(triggers) == 1
        assert triggers[0].name == "Deal active"


@pytest.mark.django_db
class TestTriggerServiceMatching:
    """Test TriggerService matching behavior."""

    def test_get_matching_triggers_matches_event_entity_and_conditions(self, test_user):
        """get_matching_triggers returns triggers that satisfy all constraints."""
        matching = Trigger.objects.create(
            name="Match trigger",
            event_type="deal.updated",
            entity_type="Deal",
            conditions={"stage": "qualified", "amount": 1000},
            is_active=True,
            is_invalid=False,
            created_by=test_user,
        )
        Trigger.objects.create(
            name="Wrong condition",
            event_type="deal.updated",
            entity_type="Deal",
            conditions={"stage": "proposal"},
            is_active=True,
            is_invalid=False,
            created_by=test_user,
        )
        Trigger.objects.create(
            name="Inactive",
            event_type="deal.updated",
            entity_type="Deal",
            conditions={"stage": "qualified", "amount": 1000},
            is_active=False,
            is_invalid=False,
            created_by=test_user,
        )

        matches = TriggerService.get_matching_triggers(
            event_type="deal.updated",
            entity_type="Deal",
            payload={"stage": "qualified", "amount": 1000},
        )

        assert [trigger.id for trigger in matches] == [matching.id]

    def test_get_matching_triggers_supports_global_entity_type(self, test_user):
        """Entity-agnostic triggers match when event type and conditions match."""
        global_trigger = Trigger.objects.create(
            name="Global trigger",
            event_type="deal.updated",
            entity_type=None,
            conditions={"stage": "qualified"},
            is_active=True,
            is_invalid=False,
            created_by=test_user,
        )

        matches = TriggerService.get_matching_triggers(
            event_type="deal.updated",
            entity_type="Deal",
            payload={"stage": "qualified"},
        )

        assert [trigger.id for trigger in matches] == [global_trigger.id]

    def test_get_matching_triggers_validates_event_type(self):
        """get_matching_triggers validates event_type format."""
        with pytest.raises(ValueError, match="dot-notation"):
            TriggerService.get_matching_triggers(event_type="deal_updated")
