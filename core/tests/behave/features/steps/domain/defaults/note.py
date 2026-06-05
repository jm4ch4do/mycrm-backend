"""Default values handler for Note entities."""

from steps.domain.defaults.base import BaseEntityDefaults


class NoteDefaults(BaseEntityDefaults):
    """Default values handler for Note entities."""

    DEFAULT_AUTHOR_USERNAME = "testuser1"
    DEFAULT_VISIBILITY = "private"
    DEFAULT_IS_PINNED = False

    @classmethod
    def _get_defaults(cls, row_data):
        """Return note data with defaults applied."""
        # Set default values for optional fields
        defaults = {
            "author_username": cls.DEFAULT_AUTHOR_USERNAME,
            "visibility": cls.DEFAULT_VISIBILITY,
            "is_pinned": cls.DEFAULT_IS_PINNED,
        }

        # Merge with provided data (provided values take precedence)
        result = {**defaults, **row_data}

        # Auto-generate body if not provided (body is required)
        if "body" not in result or not result["body"]:
            counter = cls._get_next_counter("note")
            result["body"] = f"Note body {counter}"

        return result
