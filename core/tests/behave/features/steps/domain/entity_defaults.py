"""
Entity default handlers for BDD tests.

Each entity class provides default values for required fields.
"""

from django.apps import apps
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


class TaskDefaults(BaseEntityDefaults):
    """Default values handler for Task entity creation.

    Supports both the API path (via ``_get_defaults``) and direct-DB creation
    (via ``db_create``). The ``db_create`` factory creates both the parent
    Activity and the Task row in a single call.
    """

    DEFAULT_OWNER_USERNAME = "testuser1"

    # Task-own fields; everything else belongs to the parent Activity.
    _TASK_FIELDS = {
        "priority",
        "category",
        "estimated_duration_minutes",
        "state",
    }

    @classmethod
    def _get_defaults(cls, row_data):
        """Return task data with defaults applied."""
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate title if not provided
        if "title" not in result or not result["title"]:
            counter = cls._get_next_counter("task")
            result["title"] = f"Task{counter}"

        return result

    @staticmethod
    def db_create(data, user):
        """
        Create a Task and its parent Activity directly in the database.

        Accepts a resolved field/value mapping (FK names with UUID string
        values). Fields in ``_TASK_FIELDS`` go to the Task row; all others
        go to the parent Activity.
        """
        activity_model = apps.get_model("core", "Activity")
        task_model = apps.get_model("core", "Task")

        # Map Activity FK field names to their attnames (account → account_id).
        activity_fk_attnames = {
            f.name: f.attname
            for f in activity_model._meta.get_fields()
            if hasattr(f, "attname") and f.attname != f.name
        }

        activity_data = {}
        task_data = {}
        for k, v in data.items():
            if k in TaskDefaults._TASK_FIELDS:
                task_data[k] = v
            else:
                activity_data[activity_fk_attnames.get(k, k)] = v

        # created_by is set explicitly; remove it if it appears in the table.
        activity_data.pop("created_by", None)
        activity_data.pop("created_by_id", None)

        if "owner_user" not in activity_data and "owner_user_id" not in activity_data:
            activity_data["owner_user"] = user

        activity = activity_model.objects.create(
            type="task",
            created_by=user,
            **activity_data,
        )
        return task_model.objects.create(activity=activity, **task_data)
