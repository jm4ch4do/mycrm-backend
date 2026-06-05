"""Tests for NoteService business logic."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from core.services.domain.note_service import NoteService


@pytest.mark.django_db
class TestNoteServiceCreate:
    """Test NoteService.create_note."""

    def test_creates_note_with_author_and_created_by(self, test_user):
        """create_note sets author and created_by to the provided user."""
        data = {
            "body": "Customer wants to upgrade to enterprise plan.",
            "title": "Upgrade Interest",
        }

        note = NoteService.create_note(data, test_user)
        assert note.author == test_user
        assert note.created_by == test_user
        assert note.body == "Customer wants to upgrade to enterprise plan."
        assert note.title == "Upgrade Interest"

    def test_creates_note_with_all_fields(self, test_user, account, contact, deal):
        """create_note accepts all optional fields."""
        data = {
            "title": "Meeting Summary",
            "body": "Discussed Q4 goals.",
            "account": account,
            "contact": contact,
            "deal": deal,
            "visibility": "team",
            "is_pinned": True,
        }

        note = NoteService.create_note(data, test_user)
        assert note.title == "Meeting Summary"
        assert note.account == account
        assert note.contact == contact
        assert note.deal == deal
        assert note.visibility == "team"
        assert note.is_pinned is True

    def test_body_required(self, test_user):
        """create_note raises ValidationError when body is missing."""
        with pytest.raises(ValidationError, match="body"):
            NoteService.create_note({"title": "No Body"}, test_user)

    def test_empty_body_raises_error(self, test_user):
        """create_note raises ValidationError when body is empty string."""
        with pytest.raises(ValidationError, match="body"):
            NoteService.create_note({"body": ""}, test_user)


@pytest.mark.django_db
class TestNoteServiceUpdate:
    """Test NoteService.update_note."""

    def test_updates_note_fields(self, test_user, account):
        """update_note modifies allowed fields."""
        note = NoteService.create_note(
            {"body": "Original content.", "title": "Original"}, test_user
        )
        data = {
            "title": "Updated Title",
            "body": "Updated content.",
            "account": account,
            "visibility": "public",
            "is_pinned": True,
        }

        updated = NoteService.update_note(note, data, test_user)
        updated.refresh_from_db()
        assert updated.title == "Updated Title"
        assert updated.body == "Updated content."
        assert updated.account == account
        assert updated.visibility == "public"
        assert updated.is_pinned is True

    def test_sets_updated_by(self, test_user, test_user_2):
        """update_note sets updated_by to the provided user."""
        note = NoteService.create_note({"body": "Original."}, test_user)
        data = {"body": "Modified."}

        updated = NoteService.update_note(note, data, test_user_2)
        assert updated.updated_by == test_user_2

    def test_prevents_modification_of_immutable_fields(self, test_user, test_user_2):
        """update_note strips immutable fields (id, author, created_at, created_by)."""
        note = NoteService.create_note({"body": "Original."}, test_user)
        original_id = note.id
        original_author = note.author
        original_created_at = note.created_at
        original_created_by = note.created_by

        data = {
            "id": "new-id",
            "author": test_user_2,
            "created_at": "2020-01-01T00:00:00Z",
            "created_by": test_user_2,
            "body": "Updated.",
        }

        updated = NoteService.update_note(note, data, test_user_2)
        updated.refresh_from_db()

        # Immutable fields should not change
        assert updated.id == original_id
        assert updated.author == original_author
        assert updated.created_at == original_created_at
        assert updated.created_by == original_created_by
        # Mutable field should update
        assert updated.body == "Updated."

    def test_raises_if_note_is_invalid(self, test_user):
        """update_note raises ValidationError when note is soft-deleted."""
        note = NoteService.create_note({"body": "To be deleted."}, test_user)
        NoteService.soft_delete_note(note, test_user)

        with pytest.raises(ValidationError, match="deleted"):
            NoteService.update_note(note, {"body": "Cannot update."}, test_user)


@pytest.mark.django_db
class TestNoteServiceSoftDelete:
    """Test NoteService.soft_delete_note."""

    def test_soft_delete_sets_is_invalid(self, test_user):
        """soft_delete_note sets is_invalid=True."""
        note = NoteService.create_note({"body": "To be archived."}, test_user)
        assert note.is_invalid is False

        deleted = NoteService.soft_delete_note(note, test_user)
        deleted.refresh_from_db()
        assert deleted.is_invalid is True

    def test_soft_delete_sets_updated_by(self, test_user, test_user_2):
        """soft_delete_note sets updated_by to the provided user."""
        note = NoteService.create_note({"body": "To be deleted."}, test_user)

        deleted = NoteService.soft_delete_note(note, test_user_2)
        assert deleted.updated_by == test_user_2

    def test_list_excludes_soft_deleted(self, test_user):
        """list_notes excludes notes where is_invalid=True."""
        note1 = NoteService.create_note({"body": "Active note."}, test_user)
        note2 = NoteService.create_note({"body": "To delete."}, test_user)
        NoteService.soft_delete_note(note2, test_user)

        active_notes = list(NoteService.list_notes())
        note_ids = [n.id for n in active_notes]

        assert note1.id in note_ids
        assert note2.id not in note_ids


@pytest.mark.django_db
class TestNoteServiceList:
    """Test NoteService.list_notes."""

    def test_returns_active_notes(self, test_user):
        """list_notes returns only notes where is_invalid=False."""
        NoteService.create_note({"body": "Note 1"}, test_user)
        NoteService.create_note({"body": "Note 2"}, test_user)

        notes = list(NoteService.list_notes())
        assert len(notes) == 2
