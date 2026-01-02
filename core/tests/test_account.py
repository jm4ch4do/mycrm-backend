"""Unit tests for Account model."""
from core.models import Account, AccountStatus, AccountType, CompanySize


class TestAccountCreation:
    """Test Account model creation."""

    def test_create_with_required_fields(self, db, test_user):  # pylint: disable=unused-argument
        """Test creating an account with only required fields."""
        account = Account.objects.create(
            name="Minimal Corp",
            owner_user=test_user,
        )
        assert account.name == "Minimal Corp"
        assert account.owner_user == test_user
        assert account.status == AccountStatus.PROSPECT
        assert account.type == AccountType.CUSTOMER
        assert account.is_invalid is False

    def test_create_with_all_fields(self, db, test_user):  # pylint: disable=unused-argument
        """Test creating an account with all fields populated."""
        account = Account.objects.create(
            name="Full Corp",
            account_number="ACC-002",
            status=AccountStatus.ACTIVE,
            type=AccountType.PARTNER,
            industry="Finance",
            company_size=CompanySize.SIZE_51_200,
            annual_revenue=1000000.00,
            website="https://fullcorp.com",
            description="A full test account",
            owner_user=test_user,
            created_by=test_user,
            updated_by=test_user,
            billing_street="123 Main St",
            billing_city="San Francisco",
            billing_state="CA",
            billing_country="USA",
            billing_postal_code="94105",
        )
        assert account.name == "Full Corp"
        assert account.industry == "Finance"
        assert account.annual_revenue == 1000000.00


class TestFiltering:
    """Test Account queryset filtering."""

    def test_filter_by_status(self, db, test_user):  # pylint: disable=unused-argument
        """Test filtering accounts by status."""
        Account.objects.create(
            name="Active",
            status=AccountStatus.ACTIVE,
            owner_user=test_user,
        )
        Account.objects.create(
            name="Prospect",
            status=AccountStatus.PROSPECT,
            owner_user=test_user,
        )
        active = Account.objects.filter(status=AccountStatus.ACTIVE)
        assert active.count() == 1

    def test_filter_by_owner(self, db, test_user, test_user_2):  # pylint: disable=unused-argument
        """Test filtering accounts by owner."""
        Account.objects.create(name="User1 Corp", owner_user=test_user)
        Account.objects.create(name="User2 Corp", owner_user=test_user_2)
        user1_accounts = Account.objects.filter(owner_user=test_user)
        assert user1_accounts.count() == 1

    def test_ordering_by_created_at(self, db, test_user):  # pylint: disable=unused-argument
        """Test default ordering (newest first)."""
        Account.objects.create(name="Corp 1", owner_user=test_user)
        account2 = Account.objects.create(name="Corp 2", owner_user=test_user)
        accounts = list(Account.objects.all())
        assert accounts[0].id == account2.id  # Newest first
