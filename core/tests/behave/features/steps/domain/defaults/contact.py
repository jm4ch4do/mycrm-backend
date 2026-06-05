"""Default values handler for Contact entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class ContactDefaults(BaseEntityDefaults):
    """Default values handler for Contact entities."""

    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_ROLE = "user"
    DEFAULT_SENIORITY = "junior"
    DEFAULT_JOB_TITLE = "Employee"
    DEFAULT_DEPARTMENT = "General"

    @classmethod
    def _get_defaults(cls, row_data):
        """Return contact data with defaults applied."""
        # Set default values for optional fields
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
            "role": cls.DEFAULT_ROLE,
            "seniority": cls.DEFAULT_SENIORITY,
            "job_title": cls.DEFAULT_JOB_TITLE,
            "department": cls.DEFAULT_DEPARTMENT,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate first_name if not provided
        if "first_name" not in result or not result["first_name"]:
            counter = cls._get_next_counter("contact")
            result["first_name"] = f"Contact{counter}"

        # Auto-generate last_name if not provided
        if "last_name" not in result or not result["last_name"]:
            result["last_name"] = "Doe"

        # Auto-generate email if not provided
        if "email" not in result or not result["email"]:
            counter = cls._get_next_counter("contact_email")
            result["email"] = f"contact{counter}@example.com"

        return result
