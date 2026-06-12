# pyright: reportPrivateUsage=false
"""Tests for Django admin registrations and configurations."""

import pytest
from django.contrib import admin

from core.admin import ExecutionLogAdmin, RuleAdmin, TriggerAdmin
from core.models import ExecutionLog, Rule, Trigger


@pytest.mark.django_db
class TestTriggerAdmin:
    """Test Trigger model admin configuration."""

    def test_trigger_is_registered_in_admin(self):
        """Trigger model is registered on admin site."""
        registry = getattr(admin.site, "_registry")
        assert Trigger in registry
        assert isinstance(registry[Trigger], TriggerAdmin)

    def test_trigger_admin_has_expected_readonly_fields(self):
        """Trigger admin includes expected audit readonly fields."""
        registry = getattr(admin.site, "_registry")
        model_admin = registry[Trigger]
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
        registry = getattr(admin.site, "_registry")
        assert Rule in registry
        assert isinstance(registry[Rule], RuleAdmin)

    def test_rule_admin_has_expected_configuration(self):
        """Rule admin exposes the expected list, filter, and readonly fields."""
        registry = getattr(admin.site, "_registry")
        model_admin = registry[Rule]
        assert model_admin.list_display == (
            "name",
            "trigger",
            "evaluation_order",
            "is_active",
            "is_invalid",
            "created_at",
        )
        assert model_admin.search_fields == ("name", "trigger__name")
        assert model_admin.ordering == ("evaluation_order", "created_at")
        assert "id" in model_admin.readonly_fields
        assert "created_at" in model_admin.readonly_fields
        assert "updated_at" in model_admin.readonly_fields
        assert "created_by" in model_admin.readonly_fields
        assert "updated_by" in model_admin.readonly_fields


@pytest.mark.django_db
class TestExecutionLogAdmin:
    """Test ExecutionLog model admin configuration."""

    def test_execution_log_is_registered_in_admin(self):
        """ExecutionLog model is registered on admin site."""
        registry = getattr(admin.site, "_registry")
        assert ExecutionLog in registry
        assert isinstance(registry[ExecutionLog], ExecutionLogAdmin)

    def test_execution_log_admin_is_read_only(self):
        """ExecutionLog admin is fully read-only."""
        registry = getattr(admin.site, "_registry")
        model_admin = registry[ExecutionLog]
        assert model_admin.list_display == (
            "id",
            "workflow",
            "event",
            "status",
            "started_at",
            "finished_at",
        )
        assert model_admin.list_filter == ("status", "workflow")
        assert model_admin.search_fields == ("workflow__name",)
        assert model_admin.ordering == ("-started_at",)
        assert "id" in model_admin.readonly_fields
        assert "workflow" in model_admin.readonly_fields
        assert "event" in model_admin.readonly_fields
        assert "status" in model_admin.readonly_fields
        assert "started_at" in model_admin.readonly_fields
        assert "finished_at" in model_admin.readonly_fields
        assert "logs" in model_admin.readonly_fields
        assert "created_at" in model_admin.readonly_fields
        assert "created_by" in model_admin.readonly_fields

    def test_execution_log_admin_disables_mutations(self):
        """ExecutionLog admin cannot add, change, or delete."""
        registry = getattr(admin.site, "_registry")
        model_admin = registry[ExecutionLog]
        assert model_admin.has_add_permission(None) is False
        assert model_admin.has_change_permission(None) is False
        assert model_admin.has_delete_permission(None) is False
