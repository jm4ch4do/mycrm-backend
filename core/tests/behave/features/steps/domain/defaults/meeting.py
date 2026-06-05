"""Default values handler for Meeting entities."""

from django.apps import apps
from steps.domain.defaults.base import BaseEntityDefaults


class MeetingDefaults(BaseEntityDefaults):
    """Default values handler for Meeting entity creation.

    Supports both the API path (via ``_get_defaults``) and direct-DB creation
    (via ``db_create``). The ``db_create`` factory creates both the parent
    Activity and the Meeting row in a single call.
    """

    DEFAULT_OWNER_USERNAME = "testuser1"

    # Meeting-own fields; everything else belongs to the parent Activity.
    _MEETING_FIELDS = {
        "start_time",
        "end_time",
        "location",
        "meeting_url",
        "outcome",
        "summary",
    }

    @classmethod
    def _get_defaults(cls, row_data):
        """Return meeting data with defaults applied."""
        defaults = {
            "owner_username": cls.DEFAULT_OWNER_USERNAME,
        }

        result = {**defaults, **row_data}

        if "title" not in result or not result["title"]:
            counter = cls._get_next_counter("meeting")
            result["title"] = f"Meeting{counter}"

        return result

    @staticmethod
    def db_create(data, user):
        """
        Create a Meeting and its parent Activity directly in the database.

        Fields in ``_MEETING_FIELDS`` go to the Meeting row; all others
        go to the parent Activity.
        """
        activity_model = apps.get_model("core", "Activity")
        meeting_model = apps.get_model("core", "Meeting")

        activity_fk_attnames = {
            f.name: f.attname
            for f in activity_model._meta.get_fields()
            if hasattr(f, "attname") and f.attname != f.name
        }

        activity_data = {}
        meeting_data = {}
        for k, v in data.items():
            if k in MeetingDefaults._MEETING_FIELDS:
                if v != "":
                    meeting_data[k] = v
            else:
                activity_data[activity_fk_attnames.get(k, k)] = v

        activity_data.pop("created_by", None)
        activity_data.pop("created_by_id", None)

        if "owner_user" not in activity_data and "owner_user_id" not in activity_data:
            activity_data["owner_user"] = user

        activity = activity_model.objects.create(
            type="meeting",
            created_by=user,
            **activity_data,
        )
        return meeting_model.objects.create(activity=activity, **meeting_data)
