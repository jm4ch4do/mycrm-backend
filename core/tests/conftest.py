"""Shared pytest fixtures for core app tests."""

import pytest
from django.contrib.auth import get_user_model

from core.models import (
    Account,
    AccountStatus,
    AccountType,
    Activity,
    ActivityType,
    Contact,
    Deal,
)

user_model = get_user_model()


@pytest.fixture
def test_user(db):  # pylint: disable=unused-argument
    """Create a test user for account ownership."""
    return user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user_2(db):  # pylint: disable=unused-argument
    """Create a second test user."""
    return user_model.objects.create_user(
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


@pytest.fixture
def contact(
    db, test_user, account
):  # pylint: disable=unused-argument,redefined-outer-name
    """Create a test Contact instance."""
    return Contact.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane@testcorp.com",
        account=account,
        owner_user=test_user,
    )


@pytest.fixture
def deal(
    db, test_user, account
):  # pylint: disable=unused-argument,redefined-outer-name
    """Create a test Deal instance."""
    return Deal.objects.create(
        name="Test Deal",
        account=account,
        owner_user=test_user,
    )


@pytest.fixture
def activity(
    db, test_user, account
):  # pylint: disable=unused-argument,redefined-outer-name
    """Create a test Activity instance."""
    return Activity.objects.create(
        type=ActivityType.TASK,
        title="Test Activity",
        owner_user=test_user,
        account=account,
        created_by=test_user,
    )
