"""Default values handler for Trigger entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class TriggerDefaults(BaseEntityDefaults):
    """Default values handler for Trigger entities."""

    DEFAULT_EVENT_TYPE = "deal.updated"
    DEFAULT_ENTITY_TYPE = "Deal"
    DEFAULT_IS_ACTIVE = True
    DEFAULT_CONDITIONS = {"stage": "qualified"}

    @classmethod
    def _get_defaults(cls, row_data):
        """Return trigger data with defaults applied."""
        defaults = {
            "event_type": cls.DEFAULT_EVENT_TYPE,
            "entity_type": cls.DEFAULT_ENTITY_TYPE,
            "is_active": cls.DEFAULT_IS_ACTIVE,
            "conditions": cls.DEFAULT_CONDITIONS,
        }

        result = {**defaults, **row_data}

        if "name" not in result or not result["name"]:
            counter = cls._get_next_counter("trigger")
            result["name"] = f"Trigger{counter}"

        return result
