"""Business logic service for Contact model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Contact

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User


class ContactService:
    """Service layer for Contact business logic."""

    @staticmethod
    def list_contacts() -> Any:
        """Retrieve all contacts."""
        return Contact.objects.all()

    @staticmethod
    def get_contact(contact_id: str) -> Contact:
        """Retrieve a single contact by ID."""
        return get_object_or_404(Contact, id=contact_id)

    @staticmethod
    @transaction.atomic
    def create_contact(data: dict[str, Any], user: User) -> Contact:
        """Create a new contact with business logic enforcement."""
        contact = Contact.objects.create(
            owner_user=user,
            created_by=user,
            **data,
        )
        return contact

    @staticmethod
    @transaction.atomic
    def update_contact(contact: Contact, data: dict[str, Any], user: User) -> Contact:
        """Update a contact with business logic enforcement."""
        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        # Set audit field and update
        data["updated_by"] = user
        for field, value in data.items():
            setattr(contact, field, value)

        contact.save()
        return contact

    @staticmethod
    @transaction.atomic
    def soft_delete_contact(contact: Contact, user: User) -> Contact:
        """Soft-delete a contact by setting is_invalid=True."""
        contact.is_invalid = True
        contact.updated_by = user
        contact.save()
        return contact
