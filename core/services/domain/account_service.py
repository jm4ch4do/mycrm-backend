"""Business logic service for Account model."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Account

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


class AccountService:
    """Service layer for Account business logic."""

    @staticmethod
    def list_accounts() -> Any:
        """Retrieve all accounts."""
        return Account.objects.all()

    @staticmethod
    def get_account(account_id: str) -> Account:
        """Retrieve a single account by ID."""
        return get_object_or_404(Account, id=account_id)

    @staticmethod
    @transaction.atomic
    def create_account(data: dict[str, Any], user: User) -> Account:
        """Create a new account with business logic enforcement."""
        account = Account.objects.create(
            owner_user=user,
            created_by=user,
            **data,
        )
        return account

    @staticmethod
    @transaction.atomic
    def update_account(account: Account, data: dict[str, Any], user: User) -> Account:
        """Update an account with business logic enforcement."""
        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        # Set audit field and update
        data["updated_by"] = user
        for field, value in data.items():
            setattr(account, field, value)

        account.save()
        return account

    @staticmethod
    @transaction.atomic
    def soft_delete_account(account: Account, user: User) -> Account:
        """Soft-delete an account by setting is_invalid=True."""
        account.is_invalid = True
        account.updated_by = user
        account.save()
        return account
