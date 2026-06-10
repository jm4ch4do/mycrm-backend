"""Default values handler for Rule entities."""

from core.models import Rule
from steps.domain.defaults.base import BaseEntityDefaults


class RuleDefaults(BaseEntityDefaults):
    """Default values handler for Rule entities."""

    DEFAULT_NAME = "Deal Stage Qualified Rule"
    DEFAULT_EVALUATION_ORDER = 0
    DEFAULT_IS_ACTIVE = True
    DEFAULT_CONDITIONS = {
        "operator": "AND",
        "conditions": [{"field": "stage", "op": "eq", "value": "qualified"}],
    }

    @classmethod
    def _get_defaults(cls, row_data):
        """Return rule data with defaults applied."""
        defaults = {
            "name": cls.DEFAULT_NAME,
            "evaluation_order": cls.DEFAULT_EVALUATION_ORDER,
            "is_active": cls.DEFAULT_IS_ACTIVE,
            "conditions": cls.DEFAULT_CONDITIONS,
        }

        result = {**defaults, **row_data}

        if "name" not in result or not result["name"]:
            counter = cls._get_next_counter("rule")
            result["name"] = f"Rule{counter}"

        return result

    @classmethod
    def prepare_entity_data(cls, row_data):
        """Prepare data for API creation while preserving trigger_id."""
        result = cls._get_defaults(row_data)
        result = cls.resolve_foreign_key_references(result)

        if "trigger" in result and "trigger_id" not in result:
            result["trigger_id"] = result.pop("trigger")

        if "trigger_id" not in result:
            raise ValueError("Rule creation requires a trigger reference.")

        return result

    @staticmethod
    def db_create(data, user):
        """Create Rule directly in the database for BDD setup."""
        payload = RuleDefaults._get_defaults(data)

        trigger = payload.pop("trigger", None)
        if trigger is not None:
            payload["trigger_id"] = trigger

        trigger_id = payload.pop("trigger_id", None)
        if trigger_id is None:
            raise ValueError("Rule setup requires a trigger reference.")

        return Rule.objects.create(
            trigger_id=trigger_id,
            created_by=user,
            updated_by=user,
            **payload,
        )