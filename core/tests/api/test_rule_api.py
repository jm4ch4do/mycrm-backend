"""API tests for Rule endpoints."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Rule, Trigger

user_model = get_user_model()

CONDITIONS = {
    "operator": "AND",
    "conditions": [{"field": "stage", "op": "eq", "value": "qualified"}],
}


@pytest.fixture
def trigger(db):
    return Trigger.objects.create(
        name="Deal Stage Trigger",
        event_type="deal.stage_changed",
    )


@pytest.fixture
def rule(trigger, db):
    return Rule.objects.create(
        name="Deal Stage Qualified Rule",
        trigger=trigger,
        conditions=CONDITIONS,
    )


@pytest.mark.django_db
class TestRuleApiCrud:
    """CRUD tests for /rules/ endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="rule_admin",
            password="pass",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_rule_returns_201(self, trigger):
        """POST /rules/ creates a rule and returns 201."""
        response = self.client.post(
            "/rules/",
            {
                "name": "New Rule",
                "trigger_id": str(trigger.id),
                "conditions": CONDITIONS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Rule"
        assert response.data["trigger"]["id"] == str(trigger.id)

    def test_list_rules_returns_200(self, rule):
        """GET /rules/ returns 200 with paginated results."""
        response = self.client.get("/rules/")

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) >= 1

    def test_retrieve_rule_returns_200(self, rule):
        """GET /rules/{id}/ returns 200 with rule data."""
        response = self.client.get(f"/rules/{rule.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(rule.id)
        assert response.data["name"] == rule.name

    def test_update_rule_returns_200(self, rule, trigger):
        """PUT /rules/{id}/ updates the rule and returns 200."""
        response = self.client.put(
            f"/rules/{rule.id}/",
            {
                "name": "Updated Rule",
                "trigger_id": str(trigger.id),
                "conditions": CONDITIONS,
                "evaluation_order": 5,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Rule"
        assert response.data["evaluation_order"] == 5

    def test_delete_rule_returns_204(self, rule):
        """DELETE /rules/{id}/ soft-deletes and returns 204."""
        response = self.client.delete(f"/rules/{rule.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_deleted_rule_returns_404(self, rule):
        """GET /rules/{id}/ returns 404 for a soft-deleted rule."""
        self.client.delete(f"/rules/{rule.id}/")

        response = self.client.get(f"/rules/{rule.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_deleted_rule_excluded_from_list(self, rule):
        """Soft-deleted rule is excluded from GET /rules/ results."""
        self.client.delete(f"/rules/{rule.id}/")

        response = self.client.get("/rules/")
        ids = [r["id"] for r in response.data["results"]]
        assert str(rule.id) not in ids


@pytest.mark.django_db
class TestRuleApiPermissions:
    """Permission tests for /rules/ endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="rule_perm_admin",
            password="pass",
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="rule_perm_user",
            password="pass",
            is_staff=False,
        )

    def test_list_rules_unauthenticated_returns_403(self):
        response = self.client.get("/rules/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_rules_non_admin_returns_403(self, trigger):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get("/rules/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_rule_non_admin_returns_403(self, trigger):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(
            "/rules/",
            {
                "name": "Blocked Rule",
                "trigger_id": str(trigger.id),
                "conditions": CONDITIONS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_rule_admin_returns_201(self, trigger):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            "/rules/",
            {
                "name": "Allowed Rule",
                "trigger_id": str(trigger.id),
                "conditions": CONDITIONS,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_evaluate_rule_non_admin_returns_403(self, rule):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(
            f"/rules/{rule.id}/evaluate/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRuleEvaluateAction:
    """Tests for POST /rules/{id}/evaluate/ custom action."""

    def setup_method(self):
        self.client = APIClient()
        self.admin_user = user_model.objects.create_user(
            username="rule_eval_admin",
            password="pass",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_evaluate_rule_passing_payload_returns_true(self, rule):
        """Passing payload returns {"result": true}."""
        response = self.client.post(
            f"/rules/{rule.id}/evaluate/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"] is True

    def test_evaluate_rule_failing_payload_returns_false(self, rule):
        """Failing payload returns {"result": false}."""
        response = self.client.post(
            f"/rules/{rule.id}/evaluate/",
            {"event_payload": {"stage": "prospecting"}},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"] is False

    def test_evaluate_rule_missing_payload_returns_400(self, rule):
        """Missing event_payload returns 400."""
        response = self.client.post(
            f"/rules/{rule.id}/evaluate/",
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_evaluate_rule_malformed_conditions_returns_400(self, trigger):
        """Malformed condition tree returns 400."""
        bad_rule = Rule.objects.create(
            name="Bad Rule",
            trigger=trigger,
            conditions={"not_a_tree": True},
        )

        response = self.client.post(
            f"/rules/{bad_rule.id}/evaluate/",
            {"event_payload": {"stage": "qualified"}},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
