"""Unit tests for Trigger model."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Trigger


@pytest.mark.django_db
class TestTriggerModel:
    """Tests for Trigger model fields, defaults, and behavior."""

    def test_trigger_str_returns_name_and_event_type(self):
        """__str__ returns '<name> (<event_type>)'."""
        trigger = Trigger.objects.create(
            name="Deal Stage Trigger",
            event_type="deal.stage_changed",
        )

        assert str(trigger) == "Deal Stage Trigger (deal.stage_changed)"

    def test_trigger_requires_name(self):
        """name is required."""
        trigger = Trigger(
            event_type="deal.stage_changed",
        )

        with pytest.raises(ValidationError):
            trigger.full_clean()

    def test_trigger_requires_event_type(self):
        """event_type is required."""
        trigger = Trigger(
            name="Deal Stage Trigger",
        )

        with pytest.raises(ValidationError):
            trigger.full_clean()

    def test_trigger_conditions_nullable(self):
        """conditions can be null to represent match-all behavior."""
        trigger = Trigger.objects.create(
            name="Match All Deal Updates",
            event_type="deal.updated",
            conditions=None,
        )

        assert trigger.conditions is None

    def test_trigger_entity_type_nullable(self):
        """entity_type can be null."""
        trigger = Trigger.objects.create(
            name="Deal Stage Trigger",
            event_type="deal.stage_changed",
            entity_type=None,
        )

        assert trigger.entity_type is None

    def test_trigger_is_active_defaults_true(self):
        """is_active defaults to True."""
        trigger = Trigger.objects.create(
            name="Deal Stage Trigger",
            event_type="deal.stage_changed",
        )

        assert trigger.is_active is True

    def test_trigger_soft_delete_sets_is_invalid(self):
        """Trigger supports soft delete through is_invalid flag."""
        trigger = Trigger.objects.create(
            name="Deal Stage Trigger",
            event_type="deal.stage_changed",
        )

        trigger.is_invalid = True
        trigger.save()

        trigger.refresh_from_db()
        assert trigger.is_invalid is True

    def test_trigger_ordering_is_newest_first(self):
        """Meta ordering returns newest triggers first."""
        older = Trigger.objects.create(
            name="Older Trigger",
            event_type="deal.created",
        )
        older.created_at = timezone.now() - timedelta(minutes=5)
        older.save(update_fields=["created_at"])

        newer = Trigger.objects.create(
            name="Newer Trigger",
            event_type="deal.updated",
        )

        triggers = list(Trigger.objects.all())

        assert triggers[0] == newer
        assert triggers[1] == older
