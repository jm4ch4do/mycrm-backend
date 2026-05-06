"""API unit tests for Contact endpoints.

Smoke-level checks only: endpoint wiring, required-field validation,
auth boundary, and soft-delete behaviour.
Full CRUD and filter scenarios are covered by the behave feature tests.
"""

from typing import Optional

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Account, Contact

UserModel = get_user_model()


@pytest.mark.django_db
class TestContactAPI:
    """Basic smoke tests for /contacts/ endpoint."""

    client: Optional[APIClient]
    user: Optional[object]
    account: Optional[object]

    def setup_method(self):
        self.client = APIClient()
        self.user = UserModel.objects.create_user(
            username="contactapiuser", password="testpass123", is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(name="Test Corp", owner_user=self.user)

    def test_create_contact_returns_201(self):
        """POST /contacts/ with minimum required fields returns 201."""
        payload = {"first_name": "Jane", "account": str(self.account.id)}
        response = self.client.post("/contacts/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Jane"

    def test_create_contact_missing_first_name_returns_400(self):
        """POST /contacts/ without first_name returns 400."""
        payload = {"last_name": "Doe", "account": str(self.account.id)}
        response = self.client.post("/contacts/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "first_name" in response.data

    def test_retrieve_contact_returns_200(self):
        """GET /contacts/{id}/ returns 200 with correct id."""
        contact = Contact.objects.create(
            first_name="John", owner_user=self.user, account=self.account
        )
        response = self.client.get(f"/contacts/{contact.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(contact.id)

    def test_soft_delete_contact_returns_204_and_sets_is_invalid(self):
        """DELETE /contacts/{id}/ soft-deletes the record."""
        contact = Contact.objects.create(
            first_name="ToDelete", owner_user=self.user, account=self.account
        )
        response = self.client.delete(f"/contacts/{contact.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        contact.refresh_from_db()
        assert contact.is_invalid is True

    def test_unauthenticated_request_returns_403(self):
        """Unauthenticated requests to /contacts/ are rejected."""
        unauth = APIClient()
        response = unauth.get("/contacts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
