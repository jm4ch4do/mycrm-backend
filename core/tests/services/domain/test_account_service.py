"""Tests for AccountService business logic."""
from __future__ import annotations

import pytest

from core.models import AccountStatus
from core.services import AccountService


@pytest.mark.django_db
class TestAccountService:
    """Test AccountService business logic."""

    def test_create_account_sets_owner_and_created_by(self, test_user):
        """Test that create_account sets owner_user and created_by."""
        data = {
            "name": "New Account",
            "status": AccountStatus.PROSPECT,
        }

        account = AccountService.create_account(data, test_user)
        assert account.owner_user == test_user
        assert account.created_by == test_user
        assert account.name == "New Account"

    def test_create_account_raises_error_on_owner_override(self, test_user, test_user_2):
        """Test that create_account raises error when owner_user is provided."""
        data = {
            "name": "Account",
            "owner_user": test_user_2,  # Try to set different owner
        }

        with pytest.raises(
            TypeError,
            match="got multiple values for keyword argument 'owner_user'",
        ):
            AccountService.create_account(data, test_user)

    def test_create_account_raises_error_on_created_by_override(self, test_user, test_user_2):
        """Test that create_account raises error when created_by is provided."""
        data = {
            "name": "Account",
            "created_by": test_user_2,  # Try to set different creator
        }

        with pytest.raises(
            TypeError,
            match="got multiple values for keyword argument 'created_by'",
        ):
            AccountService.create_account(data, test_user)

    def test_update_account_sets_updated_by(self, test_user_2, account):
        """Test that update_account sets updated_by to the provided user."""
        data = {"name": "Updated Account"}

        updated_account = AccountService.update_account(account, data, test_user_2)

        assert updated_account.name == "Updated Account"
        assert updated_account.updated_by == test_user_2

    def test_update_account_prevents_modification_of_immutable_fields(
        self, test_user, account
    ):
        """Test that update_account prevents changes to immutable fields."""
        original_id = account.id
        original_created_at = account.created_at
        original_created_by = account.created_by

        data = {
            "id": "new-id",
            "created_at": "2020-01-01T00:00:00Z",
            "created_by": test_user,
            "name": "Updated",
        }

        updated_account = AccountService.update_account(account, data, test_user)

        # Immutable fields should not change
        assert updated_account.id == original_id
        assert updated_account.created_at == original_created_at
        assert updated_account.created_by == original_created_by
        # Mutable field should update
        assert updated_account.name == "Updated"

    def test_soft_delete_account_sets_is_invalid(self, test_user, account):
        """Test that soft_delete_account sets is_invalid=True."""
        assert account.is_invalid is False

        deleted_account = AccountService.soft_delete_account(account, test_user)

        assert deleted_account.is_invalid is True

    def test_soft_delete_account_sets_updated_by(self, test_user_2, account):
        """Test that soft_delete_account sets updated_by."""
        deleted_account = AccountService.soft_delete_account(account, test_user_2)

        assert deleted_account.updated_by == test_user_2
