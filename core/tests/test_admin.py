"""Tests for Django admin registrations and configurations."""

import pytest
from django.contrib import admin

from core.admin import TriggerAdmin
from core.models import Trigger


@pytest.mark.django_db
class TestTriggerAdmin:
    """Test Trigger model admin configuration."""

    def test_trigger_is_registered_in_admin(self):
        """Trigger model is registered on admin site."""
        assert Trigger in admin.site._registry
        assert isinstance(admin.site._registry[Trigger], TriggerAdmin)

    def test_trigger_admin_has_expected_readonly_fields(self):
        """Trigger admin includes expected audit readonly fields."""
        model_admin = admin.site._registry[Trigger]
        assert "id" in model_admin.readonly_fields
        assert "created_at" in model_admin.readonly_fields
        assert "updated_at" in model_admin.readonly_fields
        assert "created_by" in model_admin.readonly_fields
        assert "updated_by" in model_admin.readonly_fields
