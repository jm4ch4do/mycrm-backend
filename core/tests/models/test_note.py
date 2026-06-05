"""Unit tests for Note model."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError

from core.models import Note, NoteVisibility


class TestNoteCreation:
    """Test Note model creation and field constraints."""

    def test_create_with_required_fields(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """Note can be created with only body and author."""
        note = Note.objects.create(
            body="Customer expressed interest in upgrading their plan.",
            author=test_user,
        )

        assert note.id is not None
        assert note.body == "Customer expressed interest in upgrading their plan."
        assert note.author == test_user
        assert note.title == ""
        assert note.visibility == NoteVisibility.PRIVATE
        assert note.is_pinned is False
        assert note.is_invalid is False
        assert note.account is None
        assert note.contact is None
        assert note.deal is None

    def test_create_with_all_fields(
        self, db, test_user, account, contact, deal
    ):  # pylint: disable=unused-argument
        """Note can be created with all optional fields populated."""
        note = Note.objects.create(
            title="Account Review",
            body="Customer wants to expand to 500 seats.",
            author=test_user,
            account=account,
            contact=contact,
            deal=deal,
            visibility=NoteVisibility.TEAM,
            is_pinned=True,
        )

        assert note.title == "Account Review"
        assert note.body == "Customer wants to expand to 500 seats."
        assert note.author == test_user
        assert note.account == account
        assert note.contact == contact
        assert note.deal == deal
        assert note.visibility == NoteVisibility.TEAM
        assert note.is_pinned is True

    def test_body_required(self, db, test_user):  # pylint: disable=unused-argument
        """Omitting body raises IntegrityError (NOT NULL constraint)."""
        note = Note(author=test_user)
        with pytest.raises((IntegrityError, ValidationError)):
            note.full_clean()

    def test_author_required(self, db):  # pylint: disable=unused-argument
        """Omitting author raises IntegrityError (NOT NULL constraint)."""
        note = Note(body="Some content")
        with pytest.raises((IntegrityError, ValidationError)):
            note.full_clean()

    def test_str_returns_title_and_author(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """__str__ returns '<title> by <author>' or 'Note by <author>'."""
        note_with_title = Note.objects.create(
            title="Sales Call Notes",
            body="Discussed pricing.",
            author=test_user,
        )
        assert str(note_with_title) == f"Sales Call Notes by {test_user}"

        note_without_title = Note.objects.create(
            body="Quick observation.",
            author=test_user,
        )
        assert str(note_without_title) == f"Note by {test_user}"

    def test_soft_delete_via_is_invalid(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """Setting is_invalid=True keeps the Note row but marks it deleted."""
        note = Note.objects.create(
            body="To be archived.",
            author=test_user,
        )
        note.is_invalid = True
        note.save()
        assert Note.objects.filter(id=note.id, is_invalid=True).exists()

    def test_visibility_choices(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """All NoteVisibility values can be stored."""
        for visibility in NoteVisibility:
            note = Note.objects.create(
                body="Test visibility.",
                author=test_user,
                visibility=visibility,
            )
            assert note.visibility == visibility
            note.delete()

    def test_author_protect_constraint(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """Deleting a user with notes raises ProtectedError."""
        Note.objects.create(body="Important note.", author=test_user)

        with pytest.raises(ProtectedError):
            test_user.delete()

    def test_nullable_entity_relationships(
        self, db, test_user, account, contact, deal
    ):  # pylint: disable=unused-argument
        """Account, contact, and deal relationships are optional."""
        # Note with no entity links
        note1 = Note.objects.create(body="General note.", author=test_user)
        assert note1.account is None
        assert note1.contact is None
        assert note1.deal is None

        # Note with account only
        note2 = Note.objects.create(
            body="Account note.", author=test_user, account=account
        )
        assert note2.account == account
        assert note2.contact is None
        assert note2.deal is None

        # Note with all entity links
        note3 = Note.objects.create(
            body="Full context.",
            author=test_user,
            account=account,
            contact=contact,
            deal=deal,
        )
        assert note3.account == account
        assert note3.contact == contact
        assert note3.deal == deal
