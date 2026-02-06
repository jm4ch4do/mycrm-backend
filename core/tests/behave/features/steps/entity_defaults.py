"""
Entity default handlers for BDD tests.
Each entity class provides default values for required fields.
"""

from django.contrib.auth import get_user_model

User = get_user_model()


class BaseEntityDefaults:
    """Base class for entity default handlers."""

    # Counter for generating unique entity names
    _counters = {}

    @staticmethod
    def get_defaults(row_data):
        """Returns entity data with defaults applied."""
        raise NotImplementedError("Subclasses must implement get_defaults")

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
    def get_next_counter(cls, entity_type):
        """Get next counter value for generating entity names."""
        if entity_type not in cls._counters:
            cls._counters[entity_type] = 0
        cls._counters[entity_type] += 1
        return cls._counters[entity_type]


class AccountDefaults(BaseEntityDefaults):
    """Default values handler for Account entities."""

    DEFAULT_STATUS = "active"
    DEFAULT_TYPE = "customer"
    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_INDUSTRY = "Software"
    DEFAULT_WEBSITE = "https://example.com"

    @classmethod
    def get_defaults(cls, row_data):
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
            counter = cls.get_next_counter("account")
            result["name"] = f"account{counter}"

        return result
