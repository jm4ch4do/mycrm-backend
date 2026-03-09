"""Business logic service for Deal model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.models import Deal, DealContactAssoc

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

    from core.models import Contact


class DealService:
    """Service layer for Deal business logic."""

    @staticmethod
    def list_deals() -> Any:
        """Retrieve all active deals."""
        return Deal.objects.filter(is_invalid=False)

    @staticmethod
    def get_deal(deal_id: str) -> Deal:
        """Retrieve a single deal by ID."""
        return get_object_or_404(Deal, id=deal_id)

    @staticmethod
    @transaction.atomic
    def create_deal(data: dict[str, Any], user: User) -> Deal:
        """Create a new deal with business logic enforcement."""
        deal = Deal.objects.create(
            owner_user=user,
            created_by=user,
            **data,
        )
        return deal

    @staticmethod
    @transaction.atomic
    def update_deal(deal: Deal, data: dict[str, Any], user: User) -> Deal:
        """Update a deal with business logic enforcement."""
        # Remove immutable fields
        for field in ["id", "created_at", "created_by"]:
            data.pop(field, None)

        # Set audit field and update
        data["updated_by"] = user
        for field, value in data.items():
            setattr(deal, field, value)

        deal.save()
        return deal

    @staticmethod
    @transaction.atomic
    def soft_delete_deal(deal: Deal, user: User) -> Deal:
        """Soft-delete a deal by setting is_invalid=True."""
        deal.is_invalid = True
        deal.updated_by = user
        deal.save()
        return deal

    @staticmethod
    @transaction.atomic
    def add_contact(deal: Deal, contact: Contact) -> DealContactAssoc:
        """Add a contact to a deal."""
        return DealContactAssoc.objects.create(deal=deal, contact=contact)

    @staticmethod
    @transaction.atomic
    def remove_contact(deal: Deal, contact_id: str) -> None:
        """Remove a contact from a deal."""
        assoc = get_object_or_404(DealContactAssoc, deal=deal, contact_id=contact_id)
        assoc.delete()
