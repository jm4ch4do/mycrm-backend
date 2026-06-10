"""Business logic service for Rule model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from core.models import Rule, Trigger

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
    from core.models import Event


class RuleEvaluationError(Exception):
    """Raised when a rule's condition tree is malformed or cannot be evaluated."""


def _resolve_payload_value(payload: dict[str, Any], field: str) -> Any:
    """Resolve nested payload values by dot path; return None when missing."""
    value: Any = payload
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


_OPERATORS = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in b,
    "nin": lambda a, b: a not in b,
}


def _evaluate_condition(condition: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Evaluate a single leaf condition against a payload dict."""
    if not isinstance(condition, dict):
        raise RuleEvaluationError(f"Condition must be a dict, got {type(condition).__name__}.")

    field = condition.get("field")
    op = condition.get("op")
    value = condition.get("value")

    if not field or not op:
        raise RuleEvaluationError("Each condition requires 'field' and 'op' keys.")

    if op not in _OPERATORS:
        raise RuleEvaluationError(f"Unsupported operator '{op}'.")

    actual = _resolve_payload_value(payload, field)
    return _OPERATORS[op](actual, value)


def _evaluate_tree(tree: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Recursively evaluate a condition tree (AND/OR) against a payload."""
    if not isinstance(tree, dict):
        raise RuleEvaluationError("Condition tree must be a dict.")

    operator = tree.get("operator", "").upper()
    conditions = tree.get("conditions")

    if not operator or not isinstance(conditions, list) or not conditions:
        raise RuleEvaluationError(
            "Condition tree must have 'operator' (AND/OR) and a non-empty 'conditions' list."
        )

    if operator not in ("AND", "OR"):
        raise RuleEvaluationError(f"Unsupported logical operator '{operator}'. Use AND or OR.")

    results = []
    for item in conditions:
        if not isinstance(item, dict):
            raise RuleEvaluationError("Each entry in 'conditions' must be a dict.")
        # Nested group
        if "operator" in item:
            results.append(_evaluate_tree(item, payload))
        else:
            results.append(_evaluate_condition(item, payload))

    if operator == "AND":
        return all(results)
    return any(results)


class RuleService:
    """Service layer for Rule business logic."""

    @staticmethod
    def list_rules(filters: dict[str, Any] | None = None) -> QuerySet[Rule]:
        """List non-deleted rules with optional filtering."""
        queryset = Rule.objects.filter(is_invalid=False)

        if filters:
            allowed = {"trigger", "trigger_id", "is_active"}
            applied = {k: v for k, v in filters.items() if k in allowed and v not in (None, "")}
            # Normalise trigger_id → trigger
            if "trigger_id" in applied:
                applied["trigger"] = applied.pop("trigger_id")
            if applied:
                queryset = queryset.filter(**applied)

        return queryset

    @staticmethod
    def get_rule(rule_id: UUID | str) -> Rule:
        """Retrieve a non-deleted rule by ID, or raise Rule.DoesNotExist."""
        return get_object_or_404(Rule, id=rule_id, is_invalid=False)

    @staticmethod
    @transaction.atomic
    def create_rule(data: dict[str, Any], created_by: User) -> Rule:
        """Create a rule and set audit fields."""
        payload = data.copy()

        conditions = payload.get("conditions")
        if conditions is None or not isinstance(conditions, dict):
            raise ValueError("'conditions' is required and must be a dict.")

        return Rule.objects.create(
            created_by=created_by,
            updated_by=created_by,
            **payload,
        )

    @staticmethod
    @transaction.atomic
    def update_rule(rule: Rule, data: dict[str, Any], updated_by: User) -> Rule:
        """Update mutable rule fields and set updated_by."""
        payload = data.copy()

        for field in ["id", "created_at", "created_by", "is_invalid"]:
            payload.pop(field, None)

        payload["updated_by"] = updated_by
        for field, value in payload.items():
            setattr(rule, field, value)

        rule.save()
        return rule

    @staticmethod
    @transaction.atomic
    def delete_rule(rule: Rule, updated_by: User) -> None:
        """Soft-delete a rule by marking it invalid."""
        rule.is_invalid = True
        rule.updated_by = updated_by
        rule.save()

    @staticmethod
    def evaluate_rule(rule: Rule, event: Event) -> bool:
        """Evaluate a rule's condition tree against event.after_state.

        Returns True if all conditions pass, False otherwise.
        Raises RuleEvaluationError if the condition tree is malformed.
        """
        payload = event.after_state or {}
        return _evaluate_tree(rule.conditions, payload)

    @staticmethod
    def evaluate_rules_for_trigger(trigger: Trigger, event: Event) -> bool:
        """Evaluate all active, non-deleted rules for a trigger in order.

        Short-circuits on the first failing rule.
        Returns True when the trigger has no active rules.
        """
        rules = Rule.objects.filter(
            trigger=trigger,
            is_active=True,
            is_invalid=False,
        ).order_by("evaluation_order", "created_at")

        for rule in rules:
            if not RuleService.evaluate_rule(rule, event):
                return False

        return True
