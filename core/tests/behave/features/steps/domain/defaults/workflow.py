"""Default values handler for Workflow entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class WorkflowDefaults(BaseEntityDefaults):
    """Default values handler for Workflow entities."""

    NAME = "Qualify Deal Workflow"
    DEFAULT_DESCRIPTION = ""
    DEFAULT_IS_ACTIVE = True

    @classmethod
    def _get_defaults(cls, row_data):
        """Return workflow data with defaults applied."""
        defaults = {
            "name": cls.NAME,
            "description": cls.DEFAULT_DESCRIPTION,
            "is_active": cls.DEFAULT_IS_ACTIVE,
        }
        return {**defaults, **row_data}

    @classmethod
    def prepare_entity_data(cls, row_data):
        """Prepare data for API creation while preserving trigger_id."""
        result = cls._get_defaults(row_data)
        result = cls.resolve_foreign_key_references(result)

        if "trigger" in result and "trigger_id" not in result:
            result["trigger_id"] = result.pop("trigger")

        if "trigger_id" not in result:
            raise ValueError("Workflow creation requires a trigger reference.")

        return result
