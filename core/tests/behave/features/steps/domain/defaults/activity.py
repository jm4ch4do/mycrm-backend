"""Default values handler for Activity entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class ActivityDefaults(BaseEntityDefaults):
    """Default values handler for Activity entities."""

    DEFAULT_TYPE = "task"
    DEFAULT_STATUS = "planned"
    DEFAULT_OWNER_USERNAME = "testuser1"

    @classmethod
    def _get_defaults(cls, row_data):
        """Return activity data with defaults applied."""
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
            "type": cls.DEFAULT_TYPE,
            "status": cls.DEFAULT_STATUS,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate title if not provided
        if "title" not in result or not result["title"]:
            counter = cls._get_next_counter("activity")
            result["title"] = f"Activity{counter}"

        return result
