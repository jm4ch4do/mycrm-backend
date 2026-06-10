"""Unit tests for custom permission classes."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from core.permissions import CanManageTriggers

user_model = get_user_model()


@pytest.mark.django_db
class TestCanManageTriggers:
    """Test trigger-specific permission behavior."""

    def setup_method(self):
        self.permission = CanManageTriggers()
        self.factory = APIRequestFactory()
        self.staff_user = user_model.objects.create_user(
            username="perm_staff",
            password="pass",
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="perm_regular",
            password="pass",
            is_staff=False,
        )

    def test_safe_method_requires_authentication(self):
        """Safe methods are allowed for authenticated users only."""
        request = self.factory.get("/triggers/")
        request.user = self.regular_user

        assert self.permission.has_permission(request, view=None) is True

    def test_safe_method_denies_unauthenticated(self):
        """Safe methods are denied for unauthenticated users."""
        request = self.factory.get("/triggers/")
        request.user = type("Anonymous", (), {"is_authenticated": False, "is_staff": False})()

        assert self.permission.has_permission(request, view=None) is False

    def test_write_method_allows_staff(self):
        """Write methods are allowed for staff users."""
        request = self.factory.post("/triggers/", {}, format="json")
        request.user = self.staff_user

        assert self.permission.has_permission(request, view=None) is True

    def test_write_method_denies_non_staff(self):
        """Write methods are denied for non-staff users."""
        request = self.factory.post("/triggers/", {}, format="json")
        request.user = self.regular_user

        assert self.permission.has_permission(request, view=None) is False
