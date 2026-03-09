"""Tests for DealService business logic."""

from __future__ import annotations

import pytest
from django.http import Http404

from core.models import Contact, DealContactAssoc, DealStage
from core.services import DealService


@pytest.mark.django_db
class TestDealService:
    """Test DealService business logic."""

    def test_create_deal_sets_owner_and_created_by(self, test_user, account):
        """Test that create_deal sets owner_user and created_by."""
        data = {
            "name": "New Deal",
            "account": account,
            "stage": DealStage.LEAD,
        }

        deal = DealService.create_deal(data, test_user)
        assert deal.owner_user == test_user
        assert deal.created_by == test_user
        assert deal.name == "New Deal"
        assert deal.account == account

    def test_update_deal_sets_updated_by(self, test_user, test_user_2, account):
        """Test that update_deal sets updated_by to the provided user."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)

        updated = DealService.update_deal(
            deal, {"name": "Updated Deal", "stage": DealStage.PROPOSAL}, test_user_2
        )

        assert updated.name == "Updated Deal"
        assert updated.stage == DealStage.PROPOSAL
        assert updated.updated_by == test_user_2

    def test_update_deal_prevents_modification_of_immutable_fields(
        self, test_user, account
    ):
        """Test that update_deal prevents changes to immutable fields."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)
        original_id = deal.id
        original_created_at = deal.created_at
        original_created_by = deal.created_by

        data = {
            "id": "new-id",
            "created_at": "2020-01-01T00:00:00Z",
            "created_by": test_user,
            "name": "Updated",
        }

        updated = DealService.update_deal(deal, data, test_user)

        assert updated.id == original_id
        assert updated.created_at == original_created_at
        assert updated.created_by == original_created_by
        assert updated.name == "Updated"

    def test_soft_delete_deal_sets_is_invalid(self, test_user, account):
        """Test that soft_delete_deal sets is_invalid=True."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)
        assert deal.is_invalid is False

        deleted = DealService.soft_delete_deal(deal, test_user)
        assert deleted.is_invalid is True

    def test_soft_delete_deal_sets_updated_by(self, test_user, test_user_2, account):
        """Test that soft_delete_deal sets updated_by."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)

        deleted = DealService.soft_delete_deal(deal, test_user_2)
        assert deleted.updated_by == test_user_2


@pytest.mark.django_db
class TestDealContactAssocService:
    """Test DealService contact association methods."""

    def test_add_contact_creates_assoc(self, test_user, account):
        """Test that add_contact creates a DealContactAssoc."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)
        contact = Contact.objects.create(first_name="John", account=account)

        assoc = DealService.add_contact(deal, contact)

        assert assoc.deal == deal
        assert assoc.contact == contact
        assert DealContactAssoc.objects.count() == 1

    def test_remove_contact_deletes_assoc(self, test_user, account):
        """Test that remove_contact deletes a DealContactAssoc."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)
        contact = Contact.objects.create(first_name="Jane", account=account)
        DealService.add_contact(deal, contact)
        assert DealContactAssoc.objects.count() == 1

        DealService.remove_contact(deal, str(contact.id))
        assert DealContactAssoc.objects.count() == 0

    def test_remove_contact_raises_404_for_missing_assoc(self, test_user, account):
        """Test that remove_contact raises 404 if association doesn't exist."""
        deal = DealService.create_deal({"name": "Deal", "account": account}, test_user)
        contact = Contact.objects.create(first_name="Ghost", account=account)

        with pytest.raises(Http404):
            DealService.remove_contact(deal, str(contact.id))
