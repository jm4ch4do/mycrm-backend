"""
Then steps for verifying responses and entity states.
"""

from datetime import datetime

from behave import then

from steps.domain.constants import ENTITY_CONFIG
from steps.utils import normalize_entity_name, resolve_model, resolve_table_value


def _response_items(response_data):
    if isinstance(response_data, dict) and "results" in response_data:
        return response_data["results"]
    return response_data


def _resolve_item_value(item, field_path):
    current = item
    for part in field_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part)
    return current

# ---------------------------------------------------------------------------
# Response status assertions
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Response body assertions
# ---------------------------------------------------------------------------


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
    accounts = _response_items(context.response_data)

    for row in context.table:
        expected = {
            key: resolve_table_value(value, context) for key, value in row.items()
        }

        # Find matching account
        found = False
        for account in accounts:
            match = all(
                str(_resolve_item_value(account, key)) == str(value)
                for key, value in expected.items()
            )
            if match:
                found = True
                break

        assert found, f"Account not found in response: {expected}"


@then("the response should contain details")
def step_verify_account_details(context):
    """
    Verify that the response body contains expected key/value pairs.

    Supports both single-object and list responses:

    - Single-object (detail endpoint): every table row is checked against
      the response JSON object directly.
    - List response (has "results"): each table row must match at least one
      record in the list. Order of rows does not need to match order of results.

    Examples:
        Then the response should contain details
            | name      | status |
            | Acme Corp | active |

        Then the response should contain details
            | title          | type    |
            | Follow up call | call    |
            | Send proposal  | task    |
    """
    assert context.response.status_code == 200

    data = context.response_data
    records = data.get("results") if isinstance(data, dict) else None

    if records is not None:
        # List response — each table row must match at least one record (order-independent)
        for row in context.table:
            expected = {
                key: resolve_table_value(value, context)
                for key, value in row.items()
            }
            match = any(
                all(str(_resolve_item_value(record, k)) == str(v) for k, v in expected.items())
                for record in records
            )
            assert match, (
                f"No record found matching {expected}. "
                f"Available: {[{k: r.get(k) for k in expected} for r in records]}"
            )
    else:
        # Single-object response — check every row against the response object
        for row in context.table:
            for key, expected_value in row.items():
                actual_value = _resolve_item_value(data, key)
                expected_value = resolve_table_value(expected_value, context)
                assert (
                    str(actual_value) == str(expected_value)
                ), f"Expected {key}='{expected_value}', got '{actual_value}'"


@then('every item in the response has "{field}" "{expected}"')
def step_every_item_in_response_has_field_value(context, field, expected):
    """Assert every item in a list response has the expected field value."""
    items = _response_items(context.response_data)
    assert items, "Response contains no items."
    expected = resolve_table_value(expected, context)

    for item in items:
        actual_value = _resolve_item_value(item, field)
        assert str(actual_value) == str(expected), (
            f"Expected every item to have {field}='{expected}', got '{actual_value}'"
        )


@then('the response contains field "{field}"')
def step_response_contains_field(context, field):
    """
    Assert that the response JSON object contains the given top-level field.

    Useful for single-object endpoints (e.g. /me/) where you want to verify a
    key is present without asserting its value.

    Example:
        Then the response contains field "role"
        Then the response contains field "username"
    """
    assert (
        field in context.response_data
    ), f"Expected field '{field}' in response, got: {list(context.response_data.keys())}"


# ---------------------------------------------------------------------------
# Database state assertions
# ---------------------------------------------------------------------------


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

    model = resolve_model(entity)

    instance = model.objects.get(**{field: value})
    actual = str(getattr(instance, check_field))
    expected = str(resolve_table_value(expected, context))
    assert actual == expected, f"Expected {check_field}='{expected}', got '{actual}'"


@then('the "{entity}" with "{field}" "{value}" has a related "{related}"')
@then('the "{entity}" with "{field}" "{value}" has "{count}" related "{related}"')
def step_verify_entity_has_related(context, entity, field, value, related, count=None):
    """
    Verify that a related object exists on an entity, optionally checking count.

    Without count: asserts that the named related attribute exists and is not null.
    With count: asserts that the related manager returns exactly that count.

    Examples (existence check):
        Then the "user" with "username" "roleuser" has a "profile"
        Then the "account" with "name" "Acme Corp" has a "contacts"

    Examples (count check):
        Then the "workflow" with "name" "Qualify Deal Workflow" has "1" related "workflow_steps"
        Then the "account" with "name" "Acme Corp" has "5" related "contacts"
    """
    entity = normalize_entity_name(entity)
    model = resolve_model(entity)
    instance = model.objects.get(**{field: value})

    if count is not None:
        # Count check: use reverse manager for related collection
        related_manager = getattr(instance, related)
        actual_count = related_manager.count()
        expected_count = int(count)
        assert actual_count == expected_count, (
            f"Expected {expected_count} related '{related}', got {actual_count}"
        )
    else:
        # Existence check: verify related attribute exists and is not null
        try:
            related_obj = getattr(instance, related)
            if hasattr(related_obj, "pk"):
                assert related_obj.pk is not None, f"'{related}' on {entity} has no pk"
        except Exception as exc:
            raise AssertionError(f"'{related}' does not exist on {entity}: {exc}") from exc


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
    if isinstance(data, dict):
        results = data.get("results", data)
    else:
        results = data

    found = any(item.get(field) == value for item in results)
    assert not found, f"{entity} with {field}='{value}' should not appear in the list"


@then('every item in the response has field "{field}"')
def step_every_item_has_field(context, field):
    """
    Assert that every object in a list (or paginated) response has the given field.

    Works with both flat list responses and paginated responses that wrap items
    in a 'results' key.

    Example:
        Then every item in the response has field "role"
        Then every item in the response has field "status"
    """
    data = context.response_data
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(items) > 0, "Response contains no items."
    for item in items:
        assert field in item, f"Item missing field '{field}': {item}"


@then('the response is ordered by "{field}" descending')
def step_response_ordered_by_field_desc(context, field):
    """Assert response items are ordered descending by a given field.

    Works with both flat list responses and paginated responses with
    a top-level "results" key.
    """
    data = context.response_data
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(items) > 0, "Response contains no items."

    values = []
    for item in items:
        assert field in item, f"Item missing field '{field}': {item}"
        value = item[field]

        if isinstance(value, str) and field.endswith("_at"):
            # Handle ISO timestamps, including trailing Z.
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))

        values.append(value)

    assert values == sorted(values, reverse=True), (
        f"Response is not ordered by '{field}' descending. Values: {values}"
    )


@then('the execution result status is "{status_value}"')
def step_execution_result_status(context, status_value):
    """Assert execution result has the expected status."""
    assert context.execution_result is not None, "Expected execution_result to be set."
    assert context.execution_result.get("status") == status_value, (
        f"Expected status '{status_value}', got '{context.execution_result.get('status')}'"
    )


@then("no exception is raised")
def step_no_exception_raised(context):
    """Assert no exception was captured by the previous step."""
    assert getattr(context, "captured_exception", None) is None, (
        "Expected no exception, but one was captured: "
        f"{getattr(context, 'captured_exception', None)}"
    )


@then('the captured exception is "{exception_name}"')
def step_captured_exception_is(context, exception_name):
    """Assert the previously captured exception class name."""
    exc = getattr(context, "captured_exception", None)
    assert exc is not None, "Expected an exception to be captured, but none was found."
    assert exc.__class__.__name__ == exception_name, (
        f"Expected exception '{exception_name}', got '{exc.__class__.__name__}'"
    )
