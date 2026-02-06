"""
Then steps for verifying responses and entity states.
"""

from behave import then
from core.models import Account


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
