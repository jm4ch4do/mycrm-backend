"""Business logic service for Note model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Note

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


class NoteService:
    """Service layer for Note business logic."""

    @staticmethod
    def list_notes() -> Any:
        """Retrieve all active notes."""
        return Note.objects.filter(is_invalid=False)

    @staticmethod
    def get_note(note_id: str) -> Note:
        """Retrieve a single note by ID."""
        return get_object_or_404(Note, id=note_id)

    @staticmethod
    @transaction.atomic
    def create_note(data: dict[str, Any], user: User) -> Note:
        """Create a new note with business logic enforcement.

        Validates that ``body`` is present and creates a Note with
        ``author=user`` and ``created_by=user``.
        """
        if not data.get("body"):
            raise ValidationError({"body": "body is required."})

        note = Note.objects.create(
            author=user,
            created_by=user,
            **data,
        )
        return note

    @staticmethod
    @transaction.atomic
    def update_note(note: Note, data: dict[str, Any], user: User) -> Note:
        """Update a note with business logic enforcement.

        Raises ValidationError if the note is soft-deleted (is_invalid=True).
        Updates allowed fields: title, body, visibility, is_pinned, account,
        contact, deal.
        """
        if note.is_invalid:
            raise ValidationError("Cannot update a note that has been deleted.")

        # Remove immutable fields
        for field in ["id", "author", "created_at", "created_by"]:
            data.pop(field, None)

        # Set audit field and update
        data["updated_by"] = user
        for field, value in data.items():
            setattr(note, field, value)

        note.save()
        return note

    @staticmethod
    @transaction.atomic
    def soft_delete_note(note: Note, user: User) -> Note:
        """Soft-delete a note by setting is_invalid=True."""
        note.is_invalid = True
        note.updated_by = user
        note.save()
        return note
