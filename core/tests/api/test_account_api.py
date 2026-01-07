"""API tests for Account endpoints."""
from decimal import Decimal
from typing import Optional

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Account, AccountStatus, AccountType

UserModel = get_user_model()


@pytest.mark.django_db
class TestAccountListCreate:
    """Tests for POST /accounts and GET /accounts endpoints."""

    client: Optional[APIClient]
    user: Optional[object]

    def setup_method(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_account_returns_201(self):
        """Test POST /accounts returns 201 Created."""
        payload = {
            'name': 'Acme Corp',
            'status': AccountStatus.PROSPECT,
            'type': AccountType.CUSTOMER,
            'website': 'https://acme.com',
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme Corp'

    def test_create_account_with_negative_revenue_fails(self):
        """Test annual_revenue validator rejects negative values."""
        payload = {
            'name': 'Test Account',
            'annual_revenue': Decimal('-1000.00'),
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'annual_revenue' in response.data
        assert 'positive' in str(response.data['annual_revenue']).lower()

    def test_create_account_with_zero_revenue_succeeds(self):
        """Test annual_revenue validator allows zero."""
        payload = {
            'name': 'Test Account',
            'annual_revenue': Decimal('0.00'),
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['annual_revenue'] == '0.00'

    def test_create_account_with_positive_revenue_succeeds(self):
        """Test annual_revenue validator allows positive values."""
        payload = {
            'name': 'Test Account',
            'annual_revenue': Decimal('50000.00'),
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['annual_revenue'] == '50000.00'

    def test_create_account_with_duplicate_account_number_fails(self):
        """Test account_number validator rejects duplicates."""
        Account.objects.create(
            name='Existing Account',
            account_number='ACC-001',
            owner_user=self.user,
            created_by=self.user,
        )
        payload = {
            'name': 'New Account',
            'account_number': 'ACC-001',
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'account_number' in response.data
        assert 'already exists' in str(response.data['account_number']).lower()

    def test_create_account_with_unique_account_number_succeeds(self):
        """Test account_number validator allows unique values."""
        payload = {
            'name': 'Test Account',
            'account_number': 'ACC-001',
        }
        response = self.client.post('/accounts/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['account_number'] == 'ACC-001'

    def test_list_accounts_returns_200(self):
        """Test GET /accounts returns 200 OK with list."""
        Account.objects.create(
            name='Test Account',
            owner_user=self.user,
            created_by=self.user,
        )
        response = self.client.get('/accounts/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Account'

    def test_list_accounts_with_status_filter(self):
        """Test GET /accounts with status filter."""
        Account.objects.create(
            name='Active Account',
            status=AccountStatus.ACTIVE,
            owner_user=self.user,
            created_by=self.user,
        )
        Account.objects.create(
            name='Prospect Account',
            status=AccountStatus.PROSPECT,
            owner_user=self.user,
            created_by=self.user,
        )
        response = self.client.get(
            '/accounts/',
            {'status': AccountStatus.ACTIVE},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Active Account'

    def test_list_accounts_with_search(self):
        """Test GET /accounts with search query."""
        Account.objects.create(
            name='Acme Corporation',
            industry='Technology',
            owner_user=self.user,
            created_by=self.user,
        )
        Account.objects.create(
            name='Beta Company',
            industry='Finance',
            owner_user=self.user,
            created_by=self.user,
        )
        response = self.client.get(
            '/accounts/',
            {'search': 'Acme'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Acme Corporation'


@pytest.mark.django_db
class TestAccountRetrieve:
    """Tests for GET /accounts/{id} endpoint."""

    client: Optional[APIClient]
    user: Optional[object]

    def setup_method(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username='testuser_retrieve',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_account_returns_200(self):
        """Test GET /accounts/{id} returns 200 OK."""
        account = Account.objects.create(
            name='Test Account',
            owner_user=self.user,
            created_by=self.user,
        )
        response = self.client.get(f'/accounts/{account.id}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Account'
        assert response.data['id'] == str(account.id)

    def test_retrieve_nonexistent_account_returns_404(self):
        """Test GET /accounts/{id} with invalid id returns 404."""
        import uuid
        fake_uuid = str(uuid.uuid4())
        response = self.client.get(f'/accounts/{fake_uuid}/', format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_can_retrieve_own_account(self):
        """Test user can retrieve their own account."""
        regular_user = UserModel.objects.create_user(
            username='regular3',
            password='testpass123',
            is_staff=False
        )
        account = Account.objects.create(
            name='My Account',
            owner_user=regular_user,
            created_by=regular_user,
        )

        client = APIClient()
        client.force_authenticate(user=regular_user)

        response = client.get(f'/accounts/{account.id}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'My Account'

    def test_user_can_retrieve_other_users_account(self):
        """Test user can retrieve other user's account (safe methods allowed)."""
        owner = UserModel.objects.create_user(
            username='owner',
            password='testpass123',
            is_staff=False
        )
        other_user = UserModel.objects.create_user(
            username='other',
            password='testpass123',
            is_staff=False
        )
        account = Account.objects.create(
            name='Owner Account',
            owner_user=owner,
            created_by=owner,
        )

        # Authenticate as different user
        client = APIClient()
        client.force_authenticate(user=other_user)

        response = client.get(f'/accounts/{account.id}/', format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAccountUpdate:
    """Tests for PUT/PATCH /accounts/{id} endpoints."""

    client: Optional[APIClient]
    user: Optional[object]

    def setup_method(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username='testuser_update',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_update_account_returns_200(self):
        """Test PUT /accounts/{id} returns 200 OK."""
        account = Account.objects.create(
            name='Test Account',
            status=AccountStatus.PROSPECT,
            owner_user=self.user,
            created_by=self.user,
        )
        payload = {
            'name': 'Updated Account',
            'status': AccountStatus.ACTIVE,
        }
        response = self.client.put(
            f'/accounts/{account.id}/',
            payload,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Account'
        assert response.data['status'] == AccountStatus.ACTIVE
        assert response.data['updated_by'] == self.user.id

    def test_update_account_with_duplicate_account_number_fails(self):
        """Test account_number validator rejects duplicates on update."""
        account1 = Account.objects.create(
            name='Account 1',
            account_number='ACC-001',
            owner_user=self.user,
            created_by=self.user,
        )
        Account.objects.create(
            name='Account 2',
            account_number='ACC-002',
            owner_user=self.user,
            created_by=self.user,
        )
        payload = {
            'name': 'Account 1 Updated',
            'account_number': 'ACC-002',  # Trying to use existing number
        }
        response = self.client.put(
            f'/accounts/{account1.id}/',
            payload,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'account_number' in response.data

    def test_update_account_with_same_account_number_succeeds(self):
        """Test account_number validator allows same number on update."""
        account = Account.objects.create(
            name='Test Account',
            account_number='ACC-001',
            owner_user=self.user,
            created_by=self.user,
        )
        payload = {
            'name': 'Test Account Updated',
            'account_number': 'ACC-001',  # Same number
        }
        response = self.client.put(
            f'/accounts/{account.id}/',
            payload,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['account_number'] == 'ACC-001'

    def test_non_admin_cannot_update_account(self):
        """Test non-admin user cannot update account (returns 403)."""
        # Create a non-admin user
        regular_user = UserModel.objects.create_user(
            username='regular',
            password='testpass123',
            is_staff=False
        )
        account = Account.objects.create(
            name='Test Account',
            owner_user=regular_user,
            created_by=regular_user,
        )

        # Authenticate as non-admin user
        client = APIClient()
        client.force_authenticate(user=regular_user)

        payload = {'name': 'Updated Name'}
        response = client.patch(f'/accounts/{account.id}/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_update_other_users_account(self):
        """Test user cannot update another user's account."""
        owner = UserModel.objects.create_user(
            username='owner2',
            password='testpass123',
            is_staff=False
        )
        other_user = UserModel.objects.create_user(
            username='other2',
            password='testpass123',
            is_staff=False
        )
        account = Account.objects.create(
            name='Owner Account',
            owner_user=owner,
            created_by=owner,
        )

        # Authenticate as different user (non-admin)
        client = APIClient()
        client.force_authenticate(user=other_user)

        payload = {'name': 'Hacked Name'}
        response = client.patch(f'/accounts/{account.id}/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAccountDelete:
    """Tests for DELETE /accounts/{id} endpoint."""

    client: Optional[APIClient]
    user: Optional[object]

    def setup_method(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username='testuser_delete',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_delete_account_soft_deletes(self):
        """Test DELETE /accounts/{id} soft deletes account."""
        account = Account.objects.create(
            name='Test Account',
            owner_user=self.user,
            created_by=self.user,
        )
        response = self.client.delete(f'/accounts/{account.id}/', format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Verify account is marked as invalid, not deleted
        account.refresh_from_db()
        assert account.is_invalid is True

    def test_non_admin_cannot_delete_account(self):
        """Test non-admin user cannot delete account (returns 403)."""
        # Create a non-admin user
        regular_user = UserModel.objects.create_user(
            username='regular2',
            password='testpass123',
            is_staff=False
        )
        account = Account.objects.create(
            name='Test Account',
            owner_user=regular_user,
            created_by=regular_user,
        )

        # Authenticate as non-admin user
        client = APIClient()
        client.force_authenticate(user=regular_user)

        response = client.delete(f'/accounts/{account.id}/', format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAccountAuth:
    """Tests for Account API authentication and authorization."""

    def test_unauthenticated_cannot_access_accounts(self):
        """Test unauthenticated user cannot access any endpoint."""
        client = APIClient()

        # Try to list accounts without authentication
        response = client.get('/accounts/', format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
