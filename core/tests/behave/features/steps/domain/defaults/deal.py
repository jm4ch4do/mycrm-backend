"""Default values handler for Deal entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class DealDefaults(BaseEntityDefaults):
    """Default values handler for Deal entities."""

    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_STAGE = "lead"
    DEFAULT_STATUS = "open"
    DEFAULT_AMOUNT = "10000.00"
    DEFAULT_CURRENCY = "usd"

    @classmethod
    def _get_defaults(cls, row_data):
        """Return deal data with defaults applied."""
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
            "stage": cls.DEFAULT_STAGE,
            "status": cls.DEFAULT_STATUS,
            "amount": cls.DEFAULT_AMOUNT,
            "currency": cls.DEFAULT_CURRENCY,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate name if not provided
        if "name" not in result or not result["name"]:
            counter = cls._get_next_counter("deal")
            result["name"] = f"Deal{counter}"

        return result
