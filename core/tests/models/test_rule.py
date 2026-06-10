"""Unit tests for Rule model."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Rule, Trigger


CONDITIONS = {"operator": "AND", "conditions": [{"field": "stage", "op": "eq", "value": "qualified"}]}


@pytest.fixture
def trigger(db):
    """A minimal trigger for rule attachment."""
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.mark.django_db
class TestRuleModel:
    """Tests for Rule model fields, defaults, and behavior."""

    def test_rule_str_returns_name_and_trigger(self, trigger):
        """__str__ returns '<name> (<trigger name>)'."""
        rule = Rule.objects.create(
            name="Deal Stage Qualified Rule",
            trigger=trigger,
            conditions=CONDITIONS,
        )

        assert str(rule) == "Deal Stage Qualified Rule (Deal Stage Trigger)"

    def test_rule_requires_name(self, trigger):
        """name is required."""
        rule = Rule(
            trigger=trigger,
            conditions=CONDITIONS,
        )

        with pytest.raises(ValidationError):
            rule.full_clean()

    def test_rule_requires_trigger(self):
        """trigger FK is required."""
        rule = Rule(
            name="Orphan Rule",
            conditions=CONDITIONS,
        )

        with pytest.raises((ValidationError, ValueError)):
            rule.full_clean()

    def test_rule_requires_conditions(self, trigger):
        """conditions JSONField is required — blank raises ValidationError."""
        rule = Rule(
            name="No Conditions Rule",
            trigger=trigger,
        )

        with pytest.raises(ValidationError):
            rule.full_clean()

    def test_rule_evaluation_order_defaults_zero(self, trigger):
        """evaluation_order defaults to 0."""
        rule = Rule.objects.create(
            name="Deal Stage Qualified Rule",
            trigger=trigger,
            conditions=CONDITIONS,
        )

        assert rule.evaluation_order == 0

    def test_rule_is_active_defaults_true(self, trigger):
        """is_active defaults to True."""
        rule = Rule.objects.create(
            name="Deal Stage Qualified Rule",
            trigger=trigger,
            conditions=CONDITIONS,
        )

        assert rule.is_active is True

    def test_rule_soft_delete_sets_is_invalid(self, trigger):
        """Rule supports soft delete through is_invalid flag."""
        rule = Rule.objects.create(
            name="Deal Stage Qualified Rule",
            trigger=trigger,
            conditions=CONDITIONS,
        )

        rule.is_invalid = True
        rule.save()

        rule.refresh_from_db()
        assert rule.is_invalid is True

    def test_rule_ordering_by_evaluation_order_then_created_at(self, trigger):
        """Meta ordering returns rules by evaluation_order asc, then created_at asc."""
        rule_b = Rule.objects.create(
            name="Rule B",
            trigger=trigger,
            conditions=CONDITIONS,
            evaluation_order=2,
        )
        rule_a = Rule.objects.create(
            name="Rule A",
            trigger=trigger,
            conditions=CONDITIONS,
            evaluation_order=1,
        )
        rule_c_early = Rule.objects.create(
            name="Rule C Early",
            trigger=trigger,
            conditions=CONDITIONS,
            evaluation_order=2,
        )
        # Force rule_c_early to have an earlier created_at than rule_b
        rule_c_early.created_at = timezone.now() - timedelta(minutes=10)
        rule_c_early.save(update_fields=["created_at"])

        rules = list(Rule.objects.filter(trigger=trigger))

        assert rules[0] == rule_a
        # evaluation_order=2 tie broken by created_at — rule_c_early is older
        assert rules[1] == rule_c_early
        assert rules[2] == rule_b
