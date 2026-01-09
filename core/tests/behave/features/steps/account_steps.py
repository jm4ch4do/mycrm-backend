"""
Step definitions for Account CRUD operations.
"""

import json
from behave import given, when, then
from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Account

User = get_user_model()


def parse_literal(value):
    """Parse string values to appropriate Python types."""
    if not value:
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null" or lowered == "none":
        return None
    return value


@given("I create accounts through the API")
def step_create_accounts(context):
    """Create accounts through the Django test client."""
    context.client = Client()
    context.created_accounts = []
    context.users = {}

    for row in context.table:
        # Create or get user for owner
        username = row["owner_username"]
        if username not in context.users:
            # Create a new staff user for the test
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password="testpass123",
                is_staff=True,  # Make users staff so they can update accounts
            )
            context.users[username] = user
        else:
            user = context.users[username]

        # Create account
        account_data = {
            "name": row["name"],
            "status": row["status"],
            "type": row["type"],
        }

        # Add optional fields if present
        if "industry" in row.headings:
            account_data["industry"] = row.get("industry", "")
        if "website" in row.headings:
            account_data["website"] = row.get("website", "")

        # Authenticate as the owner user
        context.client.force_login(user)

        response = context.client.post(
            "/accounts/",
            data=json.dumps(account_data),
            content_type="application/json",
        )

        assert (
            response.status_code == 201
        ), f"Failed to create account: {response.content}"
        context.created_accounts.append(response.json())

    context.response = response


@when("I request all accounts from the API")
def step_request_all_accounts(context):
    """Request all accounts from the API."""
    if not hasattr(context, "client"):
        context.client = Client()

    # Login as any existing user
    if hasattr(context, "users") and context.users:
        user = list(context.users.values())[0]
        context.client.force_login(user)

    response = context.client.get("/accounts/")
    context.response = response
    context.response_data = response.json()


@when('I request accounts with status "{status}"')
def step_request_accounts_by_status(context, status):
    """Request accounts filtered by status."""
    if not hasattr(context, "client"):
        context.client = Client()

    # Login as any existing user
    if hasattr(context, "users") and context.users:
        user = list(context.users.values())[0]
        context.client.force_login(user)

    response = context.client.get(f"/accounts/?status={status}")
    context.response = response
    context.response_data = response.json()


@when('I update the account "{account_name}" status to "{new_status}"')
def step_update_account_status(context, account_name, new_status):
    """Update an account's status."""
    # Find the account by name
    account = Account.objects.get(name=account_name)

    # Login as the owner
    context.client.force_login(account.owner_user)

    response = context.client.patch(
        f"/accounts/{account.id}/",
        data=json.dumps({"status": new_status}),
        content_type="application/json",
    )

    assert response.status_code == 200, f"Failed to update account: {response.content}"
    context.response = response
    context.response_data = response.json()


@when('I request details for account "{account_name}"')
def step_request_account_details(context, account_name):
    """Request details for a specific account."""
    # Find the account by name
    account = Account.objects.get(name=account_name)

    # Login as the owner
    context.client.force_login(account.owner_user)

    response = context.client.get(f"/accounts/{account.id}/")
    context.response = response
    context.response_data = response.json()


@then("the response should contain {count:d} accounts")
def step_verify_account_count(context, count):
    """Verify the number of accounts in the response."""
    assert (
        context.response.status_code == 200
    ), f"Expected 200, got {context.response.status_code}"

    # Handle both list and paginated responses
    if isinstance(context.response_data, dict) and "results" in context.response_data:
        actual_count = len(context.response_data["results"])
    else:
        actual_count = len(context.response_data)

    assert actual_count == count, f"Expected {count} accounts, got {actual_count}"


@then("the response should include the following accounts")
def step_verify_accounts_in_response(context):
    """Verify that specific accounts are in the response."""
    # Handle both list and paginated responses
    if isinstance(context.response_data, dict) and "results" in context.response_data:
        accounts = context.response_data["results"]
    else:
        accounts = context.response_data

    for row in context.table:
        expected = {key: value for key, value in row.items()}

        # Find matching account
        found = False
        for account in accounts:
            match = all(account.get(key) == value for key, value in expected.items())
            if match:
                found = True
                break

        assert found, f"Account not found in response: {expected}"


@then('the first account should have name "{expected_name}"')
def step_verify_first_account_name(context, expected_name):
    """Verify the name of the first account."""
    # Handle both list and paginated responses
    if isinstance(context.response_data, dict) and "results" in context.response_data:
        accounts = context.response_data["results"]
    else:
        accounts = context.response_data

    assert len(accounts) > 0, "No accounts in response"
    actual_name = accounts[0]["name"]
    assert (
        actual_name == expected_name
    ), f"Expected name '{expected_name}', got '{actual_name}'"


@then('the account "{account_name}" should have status "{expected_status}"')
def step_verify_account_status(context, account_name, expected_status):
    """Verify an account's status."""
    account = Account.objects.get(name=account_name)
    assert (
        account.status == expected_status
    ), f"Expected status '{expected_status}', got '{account.status}'"


@then("the response should contain account details")
def step_verify_account_details(context):
    """Verify account details in the response."""
    assert context.response.status_code == 200

    for row in context.table:
        for key, expected_value in row.items():
            actual_value = context.response_data.get(key)
            assert (
                actual_value == expected_value
            ), f"Expected {key}='{expected_value}', got '{actual_value}'"
