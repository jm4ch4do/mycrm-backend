"""Default values handler for Task entities."""

from django.apps import apps
from steps.domain.defaults.base import BaseEntityDefaults


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

        # Map Activity FK field names to their attnames (account → account_id)
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

        # created_by is set explicitly; remove it if it appears in the table
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
