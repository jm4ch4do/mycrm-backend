"""Tests for AccountManager custom manager."""
import pytest

from core.models import Account, AccountStatus, CompanySize


@pytest.mark.django_db
class TestAccountManager:
    """Test AccountManager custom methods."""

    def test_active_returns_non_deleted_accounts(self, test_user):
        """Test that active() returns only accounts where is_invalid=False."""
        # Create active and inactive accounts
        active_account = Account.objects.create(
            name="Active Account",
            owner_user=test_user,
            is_invalid=False,
        )
        Account.objects.create(
            name="Deleted Account",
            owner_user=test_user,
            is_invalid=True,
        )

        # Query active accounts
        active_accounts = Account.objects.active()
        assert active_accounts.count() == 1
        assert active_account in active_accounts

    def test_by_owner_returns_accounts_for_specific_user(
        self, test_user, test_user_2
    ):
        """Test that by_owner() filters accounts by owner_user."""
        # Create accounts with different owners
        user1_account = Account.objects.create(
            name="User 1 Account",
            owner_user=test_user,
        )
        Account.objects.create(
            name="User 2 Account",
            owner_user=test_user_2,
        )

        # Query accounts by owner
        user1_accounts = Account.objects.by_owner(test_user)
        assert user1_accounts.count() == 1
        assert user1_account in user1_accounts

    def test_filter_by_params_with_single_param(self, test_user):
        """Test filter_by_params with a single parameter."""
        Account.objects.create(
            name="Tech Account",
            industry="Technology",
            owner_user=test_user,
        )
        Account.objects.create(
            name="Finance Account",
            industry="Finance",
            owner_user=test_user,
        )

        # Filter by industry
        tech_accounts = Account.objects.filter_by_params(industry="Technology")
        assert tech_accounts.count() == 1
        assert tech_accounts.first().name == "Tech Account"

    def test_filter_by_params_with_multiple_params(self, test_user):
        """Test filter_by_params with multiple parameters."""
        Account.objects.create(
            name="Active Tech Small",
            industry="Technology",
            company_size=CompanySize.SIZE_1_10,
            status=AccountStatus.ACTIVE,
            owner_user=test_user,
        )
        Account.objects.create(
            name="Active Tech Large",
            industry="Technology",
            company_size=CompanySize.SIZE_200_PLUS,
            status=AccountStatus.ACTIVE,
            owner_user=test_user,
        )

        # Filter by multiple params
        filtered = Account.objects.filter_by_params(
            industry="Technology",
            company_size=CompanySize.SIZE_1_10,
            status=AccountStatus.ACTIVE,
        )
        assert filtered.count() == 1
        assert filtered.first().name == "Active Tech Small"

    def test_filter_by_params_with_none_values_ignores_filter(self, test_user):
        """Test that filter_by_params ignores None parameters."""
        Account.objects.create(
            name="Account 1",
            industry="Technology",
            owner_user=test_user,
        )
        Account.objects.create(
            name="Account 2",
            industry="Finance",
            owner_user=test_user,
        )

        # Filter with None values - should return all accounts
        all_accounts = Account.objects.filter_by_params(
            industry=None,
            company_size=None,
            status=None,
            owner=None,
        )
        assert all_accounts.count() == 2

    def test_queryset_chaining_works_correctly(self, test_user, test_user_2):
        """Test that manager methods can be chained together."""
        # Create test data
        Account.objects.create(
            name="Active User1 Tech",
            owner_user=test_user,
            industry="Technology",
            status=AccountStatus.ACTIVE,
            is_invalid=False,
        )
        Account.objects.create(
            name="Active User2 Tech",
            owner_user=test_user_2,
            industry="Technology",
            status=AccountStatus.ACTIVE,
            is_invalid=False,
        )
        Account.objects.create(
            name="Deleted User1 Tech",
            owner_user=test_user,
            industry="Technology",
            status=AccountStatus.ACTIVE,
            is_invalid=True,
        )

        # Chain methods: active accounts owned by test_user in Technology
        chained = (
            Account.objects.active()
            .by_owner(test_user)
            .filter_by_params(industry="Technology")
        )
        assert chained.count() == 1
        assert chained.first().name == "Active User1 Tech"

    def test_filter_by_params_with_owner_parameter(self, test_user, test_user_2):
        """Test that filter_by_params works with owner parameter."""
        Account.objects.create(
            name="User 1 Account",
            owner_user=test_user,
        )
        Account.objects.create(
            name="User 2 Account",
            owner_user=test_user_2,
        )

        # Filter by owner using filter_by_params
        filtered = Account.objects.filter_by_params(owner=test_user)
        assert filtered.count() == 1
        assert filtered.first().name == "User 1 Account"
