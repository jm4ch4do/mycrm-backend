"""
Entity default handlers for BDD tests.
Each entity class provides default values for required fields.
"""

from django.contrib.auth import get_user_model
from steps.utils import resolve_foreign_key_pattern

User = get_user_model()


class BaseEntityDefaults:
    """Base class for entity default handlers."""

    # Counter for generating unique entity names
    _counters = {}

    @classmethod
    def prepare_entity_data(cls, row_data):
        """
        Prepare entity data by applying defaults and resolving foreign keys.
        This is the main entry point for processing row data.
        """
        result = cls._get_defaults(row_data)
        result = cls._resolve_foreign_key_references(result)
        return result

    @staticmethod
    def _get_defaults(row_data):
        """Returns entity data with defaults applied."""
        raise NotImplementedError("Subclasses must implement _get_defaults")

    @staticmethod
    def get_or_create_user(context, owner_username):
        """Get or create user for the entity."""
        if owner_username in context.users:
            return context.users[owner_username]

        # Create new test user with force_login support
        user = User.objects.create_user(
            username=owner_username,
            email=f"{owner_username}@example.com",
            password=None,  # Unusable password for force_login
            is_staff=True,
        )
        context.users[owner_username] = user
        return user

    @classmethod
    def _get_next_counter(cls, entity_type):
        """Get next counter value for generating entity names."""
        if entity_type not in cls._counters:
            cls._counters[entity_type] = 0
        cls._counters[entity_type] += 1
        return cls._counters[entity_type]

    @staticmethod
    def _resolve_foreign_key_references(result):
        """
        Resolve foreign key references using pattern resolution.

        Delegates to resolve_foreign_key_pattern() utility for pattern matching.
        Supports:
        - Pattern 1: {entity}_id_from_{field}
        - Pattern 2: {entity}_id (defaults to lookup by 'name')
        """
        keys_to_remove = []
        fields_to_add = {}

        for key, value in result.items():
            # Try to resolve the pattern
            resolution = resolve_foreign_key_pattern(key, value)

            if resolution:
                entity_name, object_id = resolution

                # Add the ID field (e.g., "account": <UUID>)
                fields_to_add[entity_name] = object_id

                # Mark the pattern field for removal
                keys_to_remove.append(key)

        # Remove pattern fields and add resolved IDs
        for key in keys_to_remove:
            del result[key]
        result.update(fields_to_add)

        return result


class AccountDefaults(BaseEntityDefaults):
    """Default values handler for Account entities."""

    DEFAULT_STATUS = "active"
    DEFAULT_TYPE = "customer"
    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_INDUSTRY = "Software"
    DEFAULT_WEBSITE = "https://example.com"

    @classmethod
    def _get_defaults(cls, row_data):
        """Returns account data with defaults applied."""
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


class ContactDefaults(BaseEntityDefaults):
    """Default values handler for Contact entities."""

    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_ROLE = "user"
    DEFAULT_SENIORITY = "junior"
    DEFAULT_JOB_TITLE = "Employee"
    DEFAULT_DEPARTMENT = "General"

    @classmethod
    def _get_defaults(cls, row_data):
        """Returns contact data with defaults applied."""
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
