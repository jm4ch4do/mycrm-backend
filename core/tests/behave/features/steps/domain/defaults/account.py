"""Default values handler for Account entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class AccountDefaults(BaseEntityDefaults):
    """Default values handler for Account entities."""

    DEFAULT_STATUS = "active"
    DEFAULT_TYPE = "customer"
    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_INDUSTRY = "Software"
    DEFAULT_WEBSITE = "https://example.com"

    @classmethod
    def _get_defaults(cls, row_data):
        """Return account data with defaults applied."""
        # Set default values for optional fields
        defaults = {
            "status": cls.DEFAULT_STATUS,
            "type": cls.DEFAULT_TYPE,
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
            "industry": cls.DEFAULT_INDUSTRY,
            "website": cls.DEFAULT_WEBSITE,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate name if not provided
        if "name" not in result or not result["name"]:
            counter = cls._get_next_counter("account")
            result["name"] = f"account{counter}"

        return result
