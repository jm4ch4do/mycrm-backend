"""
Then steps for verifying responses and entity states.
"""

from behave import then
from django.apps import apps

from core.models import Account
from steps.constants import ENTITY_CONFIG
from steps.utils import normalize_entity_name


@then('the response status code is "{status_code}"')
@then('the response status code is "{status_code}" and contains "{count}" records')
def step_verify_status_code(context, status_code, count=None):
    """
    Verify the HTTP response status code and optionally the record count.

    Works with both flat list responses and paginated responses that wrap
    results in a "results" key.

    Examples:
        Then the response status code is "200"
        Then the response status code is "200" and contains "5" records
        Then the response status code is "201"
        Then the response status code is "404"
    """
    status_code = int(status_code)

    assert (
        context.response.status_code == status_code
    ), f"Expected {status_code}, got {context.response.status_code}"

    if count is not None:
        count = int(count)
        # Handle both list and paginated responses
        if (
            isinstance(context.response_data, dict)
            and "results" in context.response_data
        ):
            actual_count = len(context.response_data["results"])
        else:
            actual_count = len(context.response_data)

        assert actual_count == count, f"Expected {count} records, got {actual_count}"


@then("the response contains")
def step_verify_accounts_in_response(context):
    """
    Verify that specific entities appear in the response data.

    Each row in the data table is matched against the response items. Every
    column in the row must match for an item to be considered a match. Works
    with both flat list and paginated responses.

    Example:
        Then the response contains
            | name      | status |
            | Acme Corp | active |
            | Tech Co   | active |
    """
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


@then('the first "{entity}" should have {field} "{expected_value}"')
def step_verify_first_entity_field(context, entity, field, expected_value):
    """
    Verify a field value of the first entity in the response list.

    Useful for checking ordering or verifying the top result after filtering.
    Works with both flat list and paginated responses.

    Examples:
        Then the first "account" should have name "Acme Corp"
        Then the first "deal" should have stage "proposal"
    """
    entity = normalize_entity_name(entity)

    # Handle both list and paginated responses
    if isinstance(context.response_data, dict) and "results" in context.response_data:
        items = context.response_data["results"]
    else:
        items = context.response_data

    assert len(items) > 0, f"No {entity} in response"
    actual_value = items[0][field]
    assert (
        actual_value == expected_value
    ), f"Expected {field}='{expected_value}', got '{actual_value}'"


@then('the account "{account_name}" should have status "{expected_status}"')
def step_verify_account_status(context, account_name, expected_status):
    """
    Verify an account's current status directly in the database.

    This is a convenience step for a common assertion. For generic entity
    field checks, prefer the 'the "{entity}" with ... should have' step.

    Example:
        Then the account "Acme Corp" should have status "inactive"
    """
    account = Account.objects.get(name=account_name)
    assert (
        account.status == expected_status
    ), f"Expected status '{expected_status}', got '{account.status}'"


@then("the response should contain account details")
def step_verify_account_details(context):
    """
    Verify that the response body contains expected key/value pairs.

    Checks each column in the data table against the top-level keys of the
    response JSON. Intended for single-object detail endpoints.

    Example:
        Then the response should contain account details
            | name      | status | type     |
            | Acme Corp | active | customer |
    """
    assert context.response.status_code == 200

    for row in context.table:
        for key, expected_value in row.items():
            actual_value = context.response_data.get(key)
            assert (
                actual_value == expected_value
            ), f"Expected {key}='{expected_value}', got '{actual_value}'"


@then(
    'the "{entity}" with "{field}" "{value}" should have "{check_field}" "{expected}"'
)
def step_verify_entity_field_value(
    context, entity, field, value, check_field, expected
):
    """
    Verify a field value of an entity directly in the database.

    Looks up the entity by field/value, then asserts that check_field equals
    the expected value (compared as strings).

    Examples:
        Then the "deal" with "name" "Enterprise License" should have "stage" "negotiation"
        Then the "account" with "name" "Acme Corp" should have "status" "inactive"
        Then the "contact" with "email" "john@acme.com" should have "role" "decision_maker"
    """
    entity = normalize_entity_name(entity)

    model_name = entity.rstrip("s").capitalize()
    model = apps.get_model("core", model_name)

    instance = model.objects.get(**{field: value})
    actual = str(getattr(instance, check_field))
    assert actual == expected, f"Expected {check_field}='{expected}', got '{actual}'"


@then('the "{entity}" with "{field}" "{value}" should not appear in the list')
def step_verify_entity_not_in_list(context, entity, field, value):
    """
    Verify that an entity does not appear in the listing endpoint.

    Sends a GET to the entity's list endpoint and asserts that no item in the
    response matches the given field/value. Useful after soft deletes to
    confirm the record is excluded from the active list.

    Examples:
        Then the "deal" with "name" "Old Deal" should not appear in the list
        Then the "account" with "name" "Defunct Corp" should not appear in the list
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    response = context.client.get(endpoint)
    data = response.json()
    results = data.get("results", data)

    found = any(item.get(field) == value for item in results)
    assert not found, f"{entity} with {field}='{value}' should not appear in the list"
