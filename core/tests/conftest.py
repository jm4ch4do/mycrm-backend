"""Shared pytest fixtures for core app tests."""
import pytest
from django.contrib.auth import get_user_model

from core.models import Account, AccountStatus, AccountType

User = get_user_model()


@pytest.fixture
def test_user(db):  # pylint: disable=unused-argument
    """Create a test user for account ownership."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user_2(db):  # pylint: disable=unused-argument
    """Create a second test user."""
    return User.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass456",
    )


@pytest.fixture
def account(db, test_user):  # pylint: disable=unused-argument,redefined-outer-name
    """Create a test Account instance."""
    return Account.objects.create(
        name="Test Corp",
        account_number="ACC-001",
        status=AccountStatus.PROSPECT,
        type=AccountType.CUSTOMER,
        owner_user=test_user,
    )
