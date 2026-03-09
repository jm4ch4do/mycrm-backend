"""Unit tests for Deal model."""

import pytest
from django.db import IntegrityError

from core.models import (
    Contact,
    Currency,
    Deal,
    DealContactAssoc,
    DealStage,
    DealStatus,
    LeadSource,
)


class TestDealCreation:
    """Test Deal model creation."""

    def test_create_with_required_fields(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test creating a deal with only required fields."""
        deal = Deal.objects.create(
            name="Test Deal",
            account=account,
        )
        assert deal.name == "Test Deal"
        assert deal.account == account
        assert deal.is_invalid is False
        assert deal.amount is None
        assert deal.stage is None
        assert deal.status is None

    def test_create_with_all_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Test creating a deal with all fields populated."""
        deal = Deal.objects.create(
            name="Full Deal",
            account=account,
            amount=50000.00,
            currency=Currency.USD,
            expected_close_date="2026-06-30",
            probability=75,
            stage=DealStage.PROPOSAL,
            status=DealStatus.OPEN,
            loss_reason=None,
            lead_source=LeadSource.INBOUND,
            owner_user=test_user,
            created_by=test_user,
            updated_by=test_user,
        )
        assert deal.name == "Full Deal"
        assert deal.amount == 50000.00
        assert deal.currency == Currency.USD
        assert deal.probability == 75
        assert deal.stage == DealStage.PROPOSAL
        assert deal.status == DealStatus.OPEN
        assert deal.lead_source == LeadSource.INBOUND
        assert deal.owner_user == test_user

    def test_create_without_account_fails(self, db):  # pylint: disable=unused-argument
        """Test that creating a deal without an account raises an error."""
        with pytest.raises(IntegrityError):
            Deal.objects.create(name="No Account Deal")

    def test_is_invalid_defaults_to_false(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test that is_invalid defaults to False."""
        deal = Deal.objects.create(name="Default Deal", account=account)
        assert deal.is_invalid is False

    def test_probability_accepts_boundary_values(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test that probability accepts 0 and 100."""
        deal_zero = Deal.objects.create(
            name="Zero Prob", account=account, probability=0
        )
        deal_hundred = Deal.objects.create(
            name="Hundred Prob", account=account, probability=100
        )
        assert deal_zero.probability == 0
        assert deal_hundred.probability == 100

    def test_str_returns_name(self, db, account):  # pylint: disable=unused-argument
        """Test __str__ returns the deal name."""
        deal = Deal.objects.create(name="My Deal", account=account)
        assert str(deal) == "My Deal"


class TestDealContactAssoc:
    """Test DealContactAssoc join table."""

    def test_create_association(self, db, account):  # pylint: disable=unused-argument
        """Test creating a deal-contact association."""
        deal = Deal.objects.create(name="Assoc Deal", account=account)
        contact = Contact.objects.create(first_name="John", account=account)
        assoc = DealContactAssoc.objects.create(deal=deal, contact=contact)
        assert assoc.deal == deal
        assert assoc.contact == contact
        assert assoc.created_at is not None

    def test_unique_constraint_prevents_duplicates(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test that duplicate deal-contact associations are rejected."""
        deal = Deal.objects.create(name="Unique Deal", account=account)
        contact = Contact.objects.create(first_name="Jane", account=account)
        DealContactAssoc.objects.create(deal=deal, contact=contact)
        with pytest.raises(IntegrityError):
            DealContactAssoc.objects.create(deal=deal, contact=contact)

    def test_multiple_contacts_per_deal(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test that a deal can have multiple contacts."""
        deal = Deal.objects.create(name="Multi Contact Deal", account=account)
        contact1 = Contact.objects.create(first_name="Alice", account=account)
        contact2 = Contact.objects.create(first_name="Bob", account=account)
        DealContactAssoc.objects.create(deal=deal, contact=contact1)
        DealContactAssoc.objects.create(deal=deal, contact=contact2)
        assert deal.contact_assocs.count() == 2

    def test_cascade_delete_deal(self, db, account):  # pylint: disable=unused-argument
        """Test that deleting a deal cascades to associations."""
        deal = Deal.objects.create(name="Cascade Deal", account=account)
        contact = Contact.objects.create(first_name="Eve", account=account)
        DealContactAssoc.objects.create(deal=deal, contact=contact)
        deal.delete()
        assert DealContactAssoc.objects.count() == 0

    def test_str_representation(self, db, account):  # pylint: disable=unused-argument
        """Test __str__ of DealContactAssoc."""
        deal = Deal.objects.create(name="Str Deal", account=account)
        contact = Contact.objects.create(first_name="Tom", account=account)
        assoc = DealContactAssoc.objects.create(deal=deal, contact=contact)
        assert str(assoc) == "Str Deal - Tom"
