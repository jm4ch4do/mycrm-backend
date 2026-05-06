"""API unit tests for Deal endpoints.

Smoke-level checks only: endpoint wiring, required-field validation,
auth boundary, and soft-delete behaviour.
Full CRUD and filter scenarios are covered by the behave feature tests.
"""

from typing import Optional

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Account, Deal

UserModel = get_user_model()


@pytest.mark.django_db
class TestDealAPI:
    """Basic smoke tests for /deals/ endpoint."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="dealapiuser", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(name="Test Corp", owner_user=self.user)

    def test_create_deal_returns_201(self):
        """POST /deals/ with minimum required fields returns 201."""
        payload = {"name": "New Deal", "account": str(self.account.id)}
        response = self.client.post("/deals/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Deal"

    def test_create_deal_missing_name_returns_400(self):
        """POST /deals/ without name returns 400."""
        payload = {"account": str(self.account.id)}
        response = self.client.post("/deals/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_retrieve_deal_returns_200(self):
        """GET /deals/{id}/ returns 200 with correct id."""
        deal = Deal.objects.create(
            name="Retrieve Me", owner_user=self.user, account=self.account
        )
        response = self.client.get(f"/deals/{deal.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(deal.id)

    def test_soft_delete_deal_returns_204_and_sets_is_invalid(self):
        """DELETE /deals/{id}/ soft-deletes the record."""
        deal = Deal.objects.create(
            name="To Delete", owner_user=self.user, account=self.account
        )
        response = self.client.delete(f"/deals/{deal.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        deal.refresh_from_db()
        assert deal.is_invalid is True

    def test_unauthenticated_request_returns_403(self):
        """Unauthenticated requests to /deals/ are rejected."""
        unauth = APIClient()
        response = unauth.get("/deals/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
