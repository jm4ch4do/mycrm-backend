"""Default values handler for Call entities."""

from django.apps import apps
from steps.domain.defaults.base import BaseEntityDefaults


class CallDefaults(BaseEntityDefaults):
    """Default values handler for Call entity creation.

    Supports both the API path (via ``_get_defaults``) and direct-DB creation
    (via ``db_create``). The ``db_create`` factory creates both the parent
    Activity and the Call row in a single call.
    """

    DEFAULT_OWNER_USERNAME = "testuser1"
    DEFAULT_DIRECTION = "outbound"

    # Call-own fields; everything else belongs to the parent Activity.
    _CALL_FIELDS = {
        "direction",
        "outcome",
        "phone_number",
        "duration_seconds",
        "summary",
    }

    @classmethod
    def _get_defaults(cls, row_data):
        """Return call data with defaults applied."""
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
            "direction": cls.DEFAULT_DIRECTION,
        }

        result = {**defaults, **row_data}

        if "title" not in result or not result["title"]:
            counter = cls._get_next_counter("call")
            result["title"] = f"Call{counter}"

        return result

    @staticmethod
    def db_create(data, user):
        """
        Create a Call and its parent Activity directly in the database.

        Fields in ``_CALL_FIELDS`` go to the Call row; all others go to the
        parent Activity.
        """
        activity_model = apps.get_model("core", "Activity")
        call_model = apps.get_model("core", "Call")

        activity_fk_attnames = {
            f.name: f.attname
            for f in activity_model._meta.get_fields()
            if hasattr(f, "attname") and f.attname != f.name
        }

        activity_data = {}
        call_data = {}
        for k, v in data.items():
            if k in CallDefaults._CALL_FIELDS:
                if v != "":
                    call_data[k] = v
            else:
                activity_data[activity_fk_attnames.get(k, k)] = v

        activity_data.pop("created_by", None)
        activity_data.pop("created_by_id", None)

        if "owner_user" not in activity_data and "owner_user_id" not in activity_data:
            activity_data["owner_user"] = user

        activity = activity_model.objects.create(
            type="call",
            created_by=user,
            **activity_data,
        )
        return call_model.objects.create(activity=activity, **call_data)
