"""Tests for ContactService business logic."""

from __future__ import annotations

import pytest

from core.services import ContactService


@pytest.mark.django_db
class TestContactService:
    """Test ContactService business logic."""

    def test_create_contact_sets_owner_and_created_by(self, test_user, account):
        """Test that create_contact sets owner_user and created_by."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "account": account,
        }

        contact = ContactService.create_contact(data, test_user)
        assert contact.owner_user == test_user
        assert contact.created_by == test_user
        assert contact.first_name == "John"
        assert contact.account == account

    def test_update_contact_sets_updated_by(self, test_user, test_user_2, account):
        """Test that update_contact sets updated_by to the provided user."""
        contact = ContactService.create_contact(
            {"first_name": "Jane", "account": account}, test_user
        )
        data = {"first_name": "Janet"}

        updated_contact = ContactService.update_contact(contact, data, test_user_2)

        assert updated_contact.first_name == "Janet"
        assert updated_contact.updated_by == test_user_2

    def test_update_contact_prevents_modification_of_immutable_fields(
        self, test_user, account
    ):
        """Test that update_contact prevents changes to immutable fields."""
        contact = ContactService.create_contact(
            {"first_name": "Jane", "account": account}, test_user
        )
        original_id = contact.id
        original_created_at = contact.created_at
        original_created_by = contact.created_by

        data = {
            "id": "new-id",
            "created_at": "2020-01-01T00:00:00Z",
            "created_by": test_user,
            "first_name": "Updated",
        }

        updated_contact = ContactService.update_contact(contact, data, test_user)

        # Immutable fields should not change
        assert updated_contact.id == original_id
        assert updated_contact.created_at == original_created_at
        assert updated_contact.created_by == original_created_by
        # Mutable field should update
        assert updated_contact.first_name == "Updated"

    def test_soft_delete_contact_sets_is_invalid(self, test_user, account):
        """Test that soft_delete_contact sets is_invalid=True."""
        contact = ContactService.create_contact(
            {"first_name": "Jane", "account": account}, test_user
        )
        assert contact.is_invalid is False

        deleted_contact = ContactService.soft_delete_contact(contact, test_user)

        assert deleted_contact.is_invalid is True

    def test_soft_delete_contact_sets_updated_by(self, test_user, test_user_2, account):
        """Test that soft_delete_contact sets updated_by."""
        contact = ContactService.create_contact(
            {"first_name": "Jane", "account": account}, test_user
        )

        deleted_contact = ContactService.soft_delete_contact(contact, test_user_2)

        assert deleted_contact.updated_by == test_user_2
