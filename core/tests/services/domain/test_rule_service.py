"""Tests for RuleService business logic."""

from __future__ import annotations

import pytest
from django.http import Http404

from core.models import Event, Rule, Trigger
from core.services.domain.rule_service import RuleEvaluationError, RuleService

CONDITIONS = {
    "operator": "AND",
    "conditions": [{"field": "stage", "op": "eq", "value": "qualified"}],
}


@pytest.fixture
def trigger(db):
    """A minimal trigger for rule attachment."""
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture
def rule(trigger, test_user):
    """A standard active rule attached to the trigger."""
    return Rule.objects.create(
        name="Deal Stage Qualified Rule",
        trigger=trigger,
        conditions=CONDITIONS,
        created_by=test_user,
        updated_by=test_user,
    )


def _make_event(after_state: dict, db) -> Event:
    """Helper to create an Event with a given after_state."""
    return Event.objects.create(
        event_type="deal.stage_changed",
        source_service="core",
        entity_type="Deal",
        entity_id="00000000-0000-0000-0000-000000000001",
        after_state=after_state,
    )


@pytest.mark.django_db
class TestRuleServiceWrite:
    """Test RuleService write operations."""

    def test_create_rule_sets_created_by(self, trigger, test_user):
        """create_rule sets created_by and updated_by."""
        rule = RuleService.create_rule(
            {
                "name": "Qualified Stage Rule",
                "trigger": trigger,
                "conditions": CONDITIONS,
            },
            created_by=test_user,
        )

        assert rule.created_by == test_user
        assert rule.updated_by == test_user

    def test_create_rule_raises_without_conditions(self, trigger, test_user):
        """create_rule raises ValueError when conditions is missing."""
        with pytest.raises(ValueError, match="conditions"):
            RuleService.create_rule(
                {
                    "name": "No Conditions Rule",
                    "trigger": trigger,
                },
                created_by=test_user,
            )

    def test_create_rule_raises_when_conditions_not_dict(self, trigger, test_user):
        """create_rule raises ValueError when conditions is not a dict."""
        with pytest.raises(ValueError, match="conditions"):
            RuleService.create_rule(
                {
                    "name": "Bad Conditions Rule",
                    "trigger": trigger,
                    "conditions": "not-a-dict",
                },
                created_by=test_user,
            )

    def test_update_rule_sets_updated_by(self, rule, test_user_2):
        """update_rule sets updated_by."""
        updated = RuleService.update_rule(
            rule,
            {"name": "Updated Rule Name"},
            updated_by=test_user_2,
        )

        assert updated.name == "Updated Rule Name"
        assert updated.updated_by == test_user_2

    def test_delete_rule_sets_is_invalid(self, rule, test_user_2):
        """delete_rule soft-deletes by setting is_invalid=True."""
        RuleService.delete_rule(rule, updated_by=test_user_2)

        rule.refresh_from_db()
        assert rule.is_invalid is True
        assert rule.updated_by == test_user_2


@pytest.mark.django_db
class TestRuleServiceRead:
    """Test RuleService read operations."""

    def test_get_rule_returns_non_deleted_record(self, rule):
        """get_rule returns a non-deleted rule."""
        fetched = RuleService.get_rule(str(rule.id))
        assert fetched.id == rule.id

    def test_get_rule_raises_for_invalid(self, rule, test_user):
        """get_rule raises Http404 for soft-deleted rule."""
        rule.is_invalid = True
        rule.save()

        with pytest.raises(Http404):
            RuleService.get_rule(str(rule.id))

    def test_list_rules_excludes_soft_deleted(self, trigger, test_user):
        """list_rules excludes is_invalid=True records."""
        active = Rule.objects.create(
            name="Active Rule",
            trigger=trigger,
            conditions=CONDITIONS,
            is_invalid=False,
        )
        Rule.objects.create(
            name="Deleted Rule",
            trigger=trigger,
            conditions=CONDITIONS,
            is_invalid=True,
        )

        results = list(RuleService.list_rules())
        assert active in results
        assert all(not r.is_invalid for r in results)


@pytest.mark.django_db
class TestRuleServiceEvaluation:
    """Test RuleService evaluate_rule and evaluate_rules_for_trigger."""

    def test_evaluate_rule_and_operator_all_pass(self, rule, db):
        """evaluate_rule returns True when all AND conditions pass."""
        event = _make_event({"stage": "qualified"}, db)
        assert RuleService.evaluate_rule(rule, event) is True

    def test_evaluate_rule_and_operator_one_fails(self, rule, db):
        """evaluate_rule returns False when one AND condition fails."""
        event = _make_event({"stage": "prospecting"}, db)
        assert RuleService.evaluate_rule(rule, event) is False

    def test_evaluate_rule_or_operator_one_passes(self, trigger, db):
        """evaluate_rule returns True when at least one OR condition passes."""
        or_rule = Rule.objects.create(
            name="OR Rule",
            trigger=trigger,
            conditions={
                "operator": "OR",
                "conditions": [
                    {"field": "stage", "op": "eq", "value": "qualified"},
                    {"field": "stage", "op": "eq", "value": "proposal"},
                ],
            },
        )
        event = _make_event({"stage": "proposal"}, db)
        assert RuleService.evaluate_rule(or_rule, event) is True

    def test_evaluate_rule_nested_conditions(self, trigger, db):
        """evaluate_rule correctly handles nested condition groups."""
        nested_rule = Rule.objects.create(
            name="Nested Rule",
            trigger=trigger,
            conditions={
                "operator": "AND",
                "conditions": [
                    {"field": "stage", "op": "eq", "value": "qualified"},
                    {
                        "operator": "OR",
                        "conditions": [
                            {"field": "value", "op": "gte", "value": 1000},
                            {"field": "priority", "op": "eq", "value": "high"},
                        ],
                    },
                ],
            },
        )
        event = _make_event({"stage": "qualified", "priority": "high"}, db)
        assert RuleService.evaluate_rule(nested_rule, event) is True

    def test_evaluate_rule_malformed_raises_error(self, trigger, db):
        """evaluate_rule raises RuleEvaluationError for malformed condition tree."""
        bad_rule = Rule.objects.create(
            name="Bad Rule",
            trigger=trigger,
            conditions={"not_operator": "AND"},
        )
        event = _make_event({"stage": "qualified"}, db)

        with pytest.raises(RuleEvaluationError):
            RuleService.evaluate_rule(bad_rule, event)

    def test_evaluate_rules_for_trigger_short_circuits(self, trigger, db):
        """evaluate_rules_for_trigger returns False on first failing rule."""
        Rule.objects.create(
            name="Failing Rule",
            trigger=trigger,
            conditions={
                "operator": "AND",
                "conditions": [{"field": "stage", "op": "eq", "value": "closed"}],
            },
            evaluation_order=1,
        )
        Rule.objects.create(
            name="Passing Rule",
            trigger=trigger,
            conditions=CONDITIONS,
            evaluation_order=2,
        )
        event = _make_event({"stage": "qualified"}, db)

        assert RuleService.evaluate_rules_for_trigger(trigger, event) is False

    def test_evaluate_rules_for_trigger_no_rules_returns_true(self, trigger, db):
        """evaluate_rules_for_trigger returns True when trigger has no active rules."""
        event = _make_event({"stage": "qualified"}, db)
        assert RuleService.evaluate_rules_for_trigger(trigger, event) is True

    def test_evaluate_rules_for_trigger_skips_inactive(self, trigger, db):
        """evaluate_rules_for_trigger skips is_active=False rules."""
        Rule.objects.create(
            name="Inactive Failing Rule",
            trigger=trigger,
            conditions={
                "operator": "AND",
                "conditions": [{"field": "stage", "op": "eq", "value": "closed"}],
            },
            is_active=False,
        )
        event = _make_event({"stage": "qualified"}, db)

        # Inactive rule is skipped → no active rules → returns True
        assert RuleService.evaluate_rules_for_trigger(trigger, event) is True

    def test_evaluate_rules_for_trigger_skips_soft_deleted(self, trigger, db):
        """evaluate_rules_for_trigger skips is_invalid=True rules."""
        Rule.objects.create(
            name="Deleted Failing Rule",
            trigger=trigger,
            conditions={
                "operator": "AND",
                "conditions": [{"field": "stage", "op": "eq", "value": "closed"}],
            },
            is_invalid=True,
        )
        event = _make_event({"stage": "qualified"}, db)

        assert RuleService.evaluate_rules_for_trigger(trigger, event) is True
