"""Unit tests for Contact model."""

import pytest
from django.db import IntegrityError

from core.models import (
    Account,
    Contact,
    ContactRole,
    ContactSeniority,
    PreferredChannel,
)


class TestContactCreation:
    """Test Contact model creation."""

    def test_create_with_required_fields(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test creating a contact with only required fields."""
        contact = Contact.objects.create(
            first_name="John",
            account=account,
        )
        assert contact.first_name == "John"
        assert contact.account == account
        assert contact.last_name is None
        assert contact.full_name == "John"
        assert contact.is_invalid is False
        assert contact.opt_in_email is True
        assert contact.opt_in_sms is False

    def test_create_with_all_fields(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Test creating a contact with all fields populated."""
        contact = Contact.objects.create(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="+1-555-0100",
            mobile="+1-555-0101",
            job_title="VP of Sales",
            department="Sales",
            role=ContactRole.DECISION_MAKER,
            seniority=ContactSeniority.EXECUTIVE,
            account=account,
            owner_user=test_user,
            primary_contact=True,
            preferred_channel=PreferredChannel.EMAIL,
            opt_in_email=True,
            opt_in_sms=True,
        )
        assert contact.full_name == "Jane Doe"
        assert contact.email == "jane.doe@example.com"
        assert contact.job_title == "VP of Sales"
        assert contact.role == ContactRole.DECISION_MAKER
        assert contact.seniority == ContactSeniority.EXECUTIVE
        assert contact.primary_contact is True


class TestContactProperties:
    """Test Contact model properties."""

    def test_full_name_with_last_name(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test full_name property with both first and last name."""
        contact = Contact.objects.create(
            first_name="John",
            last_name="Smith",
            account=account,
        )
        assert contact.full_name == "John Smith"

    def test_full_name_without_last_name(
        self, db, account
    ):  # pylint: disable=unused-argument
        """Test full_name property with only first name."""
        contact = Contact.objects.create(
            first_name="Madonna",
            account=account,
        )
        assert contact.full_name == "Madonna"

    def test_str_representation(self, db, account):  # pylint: disable=unused-argument
        """Test string representation of Contact."""
        contact = Contact.objects.create(
            first_name="Alice",
            last_name="Johnson",
            account=account,
        )
        assert str(contact) == "Alice Johnson"


class TestContactConstraints:
    """Test Contact model constraints."""

    def test_unique_email_per_account(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Test that email must be unique per account."""
        Contact.objects.create(
            first_name="John",
            email="john@example.com",
            account=account,
        )

        with pytest.raises(IntegrityError):
            Contact.objects.create(
                first_name="Jane",
                email="john@example.com",  # Same email as above
                account=account,  # Same account
            )

    def test_same_email_different_accounts(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Test that same email can exist on different accounts."""
        account2 = Account.objects.create(
            name="Another Corp",
            owner_user=test_user,
        )

        contact1 = Contact.objects.create(
            first_name="John",
            email="shared@example.com",
            account=account,
        )

        contact2 = Contact.objects.create(
            first_name="Jane",
            email="shared@example.com",  # Same email
            account=account2,  # Different account - should work
        )

        assert contact1.email == contact2.email
        assert contact1.account != contact2.account


class TestContactFiltering:
    """Test Contact queryset filtering."""

    def test_filter_by_account(
        self, db, account, test_user
    ):  # pylint: disable=unused-argument
        """Test filtering contacts by account."""
        account2 = Account.objects.create(
            name="Corp 2",
            owner_user=test_user,
        )

        Contact.objects.create(first_name="John", account=account)
        Contact.objects.create(first_name="Jane", account=account)
        Contact.objects.create(first_name="Bob", account=account2)

        account_contacts = Contact.objects.filter(account=account)
        assert account_contacts.count() == 2

    def test_filter_by_role(self, db, account):  # pylint: disable=unused-argument
        """Test filtering contacts by role."""
        Contact.objects.create(
            first_name="Decision",
            role=ContactRole.DECISION_MAKER,
            account=account,
        )
        Contact.objects.create(
            first_name="Influencer",
            role=ContactRole.INFLUENCER,
            account=account,
        )

        decision_makers = Contact.objects.filter(role=ContactRole.DECISION_MAKER)
        assert decision_makers.count() == 1
        assert decision_makers.first().first_name == "Decision"
