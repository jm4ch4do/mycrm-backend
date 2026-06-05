"""Base class for entity default handlers."""

from django.contrib.auth import get_user_model
from steps.utils import resolve_foreign_key_pattern

user_model = get_user_model()


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
        result = cls.resolve_foreign_key_references(result)
        return result

    @staticmethod
    def _get_defaults(row_data):
        """Return entity data with defaults applied."""
        raise NotImplementedError("Subclasses must implement _get_defaults")

    @staticmethod
    def get_or_create_user(context, owner_username):
        """Get or create user for the entity."""
        if owner_username in context.users:
            return context.users[owner_username]

        # Create new test user with force_login support
        user = user_model.objects.create_user(
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
    def resolve_foreign_key_references(result):
        """
        Resolve foreign key references using pattern resolution.

        Delegates to resolve_foreign_key_pattern() for pattern matching.
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
