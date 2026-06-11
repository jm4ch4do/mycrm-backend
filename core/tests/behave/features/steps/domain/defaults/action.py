"""Default values handler for Action entities."""

import json

from core.models import Action, ActionType
from steps.domain.defaults.base import BaseEntityDefaults


class ActionDefaults(BaseEntityDefaults):
    """Default values handler for Action entities."""

    NAME = "Create Qualification Task"
    ACTION_TYPE = ActionType.CREATE_TASK
    PARAMETERS = {"title": "Follow up on qualification", "due_days_from_now": 2}
    INVALID_PARAMETERS = {"unexpected_field": 999}

    @classmethod
    def _get_defaults(cls, row_data):
        """Return action data with defaults applied."""
        defaults = {
            "name": cls.NAME,
            "description": "",
            "action_type": cls.ACTION_TYPE,
            "parameters": cls.PARAMETERS.copy(),
            "retry_policy": None,
            "timeout_seconds": None,
        }
        return {**defaults, **row_data}

    @staticmethod
    def _decode_json_field(value, field_name):
        """Decode JSON encoded text fields used in Gherkin tables."""
        if value in (None, ""):
            return None
        if isinstance(value, (dict, list)):
            return value
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a JSON object.")
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"{field_name} must be valid JSON.") from exc
        if not isinstance(decoded, dict):
            raise ValueError(f"{field_name} must be a JSON object.")
        return decoded

    @classmethod
    def prepare_entity_data(cls, row_data):
        """Prepare action data for API creation."""
        result = cls._get_defaults(row_data)

        parameters_json = result.pop("parameters_json", None)
        retry_policy_json = result.pop("retry_policy_json", None)

        if parameters_json is not None:
            result["parameters"] = cls._decode_json_field(parameters_json, "parameters")
        if retry_policy_json is not None:
            result["retry_policy"] = cls._decode_json_field(
                retry_policy_json,
                "retry_policy",
            )

        return result

    @classmethod
    def db_create(cls, data, user):
        """Create Action directly in the database for BDD setup."""
        payload = cls.prepare_entity_data(data)
        return Action.objects.create(
            created_by=user,
            updated_by=user,
            **payload,
        )
