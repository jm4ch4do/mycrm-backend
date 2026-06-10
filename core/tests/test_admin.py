"""Tests for Django admin registrations and configurations."""

import pytest
from django.contrib import admin

from core.admin import RuleAdmin, TriggerAdmin
from core.models import Rule, Trigger


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


@pytest.mark.django_db
class TestRuleAdmin:
    """Test Rule model admin configuration."""

    def test_rule_is_registered_in_admin(self):
        """Rule model is registered on admin site."""
        assert Rule in admin.site._registry
        assert isinstance(admin.site._registry[Rule], RuleAdmin)

    def test_rule_admin_has_expected_configuration(self):
        """Rule admin exposes the expected list, filter, and readonly fields."""
        model_admin = admin.site._registry[Rule]
        assert model_admin.list_display == (
            "name",
            "trigger",
            "evaluation_order",
            "is_active",
            "is_invalid",
            "created_at",
        )
        assert model_admin.list_filter == ("is_active", "is_invalid", "trigger")
        assert model_admin.search_fields == ("name", "trigger__name")
        assert model_admin.ordering == ("evaluation_order", "created_at")
        assert "id" in model_admin.readonly_fields
        assert "created_at" in model_admin.readonly_fields
        assert "updated_at" in model_admin.readonly_fields
        assert "created_by" in model_admin.readonly_fields
        assert "updated_by" in model_admin.readonly_fields
