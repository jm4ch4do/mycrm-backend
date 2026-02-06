"""
When steps for API requests and entity operations.
"""

import json
from behave import when
import utils as _sutils
from core.models import Account


@when('I send a "{method}" request to "{endpoint}"')
def step_send_request_to_endpoint(context, method, endpoint):
    """
    Send an HTTP request to any API endpoint with optional query parameters.

    This is a generic step that allows calling any endpoint with any HTTP method
    and supports query parameters via a data table.

    Example without query params:
        When I send a "GET" request to "/accounts/"

    Example with query params:
        When I send a "GET" request to "/accounts/"
            | field  | operator | value  |
            | status | eq       | active |

    Supported operators:
        - eq (or equals): equality (default) - translates to ?field=value
        - ne, lt, gt, lte, gte, in, contains, icontains, startswith, endswith, isnull
          These use Django's double underscore syntax: ?field__operator=value
    """
    # Build the full URL with query parameters
    full_url = _sutils.build_url_with_query_params(endpoint, context)

    # Make the request based on HTTP method
    method = method.upper()
    if method == "GET":
        response = context.client.get(full_url)
    elif method == "POST":
        # For POST, use request body from context if available
        request_data = getattr(context, "request_data", {})
        response = context.client.post(
            full_url,
            data=json.dumps(request_data) if request_data else None,
            content_type="application/json",
        )
    elif method == "PATCH":
        request_data = getattr(context, "request_data", {})
        response = context.client.patch(
            full_url,
            data=json.dumps(request_data) if request_data else None,
            content_type="application/json",
        )
    elif method == "PUT":
        request_data = getattr(context, "request_data", {})
        response = context.client.put(
            full_url,
            data=json.dumps(request_data) if request_data else None,
            content_type="application/json",
        )
    elif method == "DELETE":
        response = context.client.delete(full_url)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    _sutils.response_to_context(context, response)


@when('I update the account "{account_name}" status to "{new_status}"')
def step_update_account_status(context, account_name, new_status):
    """Update an account's status."""
    # Find the account by name
    account = Account.objects.get(name=account_name)

    response = context.client.patch(
        f"/accounts/{account.id}/",
        data=json.dumps({"status": new_status}),
        content_type="application/json",
    )

    assert response.status_code == 200, f"Failed to update account: {response.content}"
    _sutils.response_to_context(context, response)


@when('I request details for account "{account_name}"')
def step_request_account_details(context, account_name):
    """Request details for a specific account."""
    # Find the account by name
    account = Account.objects.get(name=account_name)

    response = context.client.get(f"/accounts/{account.id}/")
    _sutils.response_to_context(context, response)
