"""
When steps for API requests and entity operations.
"""

import json
from behave import given, when
from django.apps import apps

import utils as _sutils
from steps.constants import ENTITY_CONFIG
from steps.utils import normalize_entity_name, resolve_foreign_key_pattern

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
    """
    Update an account's status field by looking it up by name.

    This is a convenience step for a common account operation. For generic
    entity updates, prefer the 'I update "{entity}"' step instead.

    Example:
        When I update the account "Acme Corp" status to "inactive"
    """
    # Find the account by name
    account = Account.objects.get(name=account_name)

    response = context.client.patch(
        f"/accounts/{account.id}/",
        data=json.dumps({"status": new_status}),
        content_type="application/json",
    )

    assert response.status_code == 200, f"Failed to update account: {response.content}"
    _sutils.response_to_context(context, response)


@when('I request details for "{entity}" with "{field}" "{value}"')
def step_request_entity_details(context, entity, field, value):
    """
    Request details for a single entity by looking it up via a unique field.

    Looks up the entity in the database by the given field/value, then sends
    a GET request to its detail endpoint (e.g. /accounts/{id}/).

    Examples:
        When I request details for "accounts" with "name" "Acme Corp"
        When I request details for "deals" with "name" "Enterprise License"
        When I request details for "contacts" with "email" "john@acme.com"
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    # Get the model dynamically
    model_name = entity.rstrip("s").capitalize()  # accounts -> Account
    model = apps.get_model("core", model_name)

    # Find the entity by field
    lookup = {field: value}
    instance = model.objects.get(**lookup)

    response = context.client.get(f"{endpoint}{instance.id}/")
    _sutils.response_to_context(context, response)


@when('I request details for "{entity}" by "{field}" "{value}"')
def step_request_entities_by_field(context, entity, field, value):
    """
    Request a filtered list of entities by a foreign key relationship.

    Uses the FK pattern resolution to translate field/value into a query
    parameter. The field must follow one of these patterns:
        - {entity}_id            — looks up the related entity by "name"
        - {entity}_id_from_{fld} — looks up the related entity by "{fld}"

    Examples:
        When I request details for "contacts" by "account_id" "Acme Corp"
            -> resolves to GET /contacts/?account={uuid-of-acme}

        When I request details for "deals" by "account_id_from_name" "Acme Corp"
            -> resolves to GET /deals/?account={uuid-of-acme}
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    # Use the shared pattern resolution utility
    resolution = resolve_foreign_key_pattern(field, value)

    if not resolution:
        raise ValueError(
            f"Field '{field}' must match pattern {{entity}}_id or {{entity}}_id_from_{{field}}"
        )

    entity_name, object_id = resolution

    # Build the query with the ID
    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    # Filter by the entity field (e.g., ?account={uuid})
    response = context.client.get(f"{endpoint}?{entity_name}={object_id}")
    _sutils.response_to_context(context, response)


@when('I update "{entity}" with "{field}" "{value}"')
def step_update_entity(context, entity, field, value):
    """
    Update an entity identified by field/value with data from a table row.

    Looks up the entity by the given field, then sends a PATCH request with
    the key/value pairs from the first row of the data table.

    Example:
        When I update "deals" with "name" "Enterprise License"
            | stage       | amount    |
            | negotiation | 150000.00 |

        When I update "accounts" with "name" "Acme Corp"
            | status   |
            | inactive |
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    model_name = entity.rstrip("s").capitalize()
    model = apps.get_model("core", model_name)

    instance = model.objects.get(**{field: value})
    update_data = dict(context.table[0].items())

    response = context.client.patch(
        f"{endpoint}{instance.id}/",
        data=json.dumps(update_data),
        content_type="application/json",
    )
    _sutils.response_to_context(context, response)


@when('I soft delete "{entity}" with "{field}" "{value}"')
def step_soft_delete_entity(context, entity, field, value):
    """
    Soft delete an entity identified by a unique field/value.

    Sends a DELETE request to the entity's detail endpoint. The API is
    expected to set is_invalid=True rather than physically removing the record.

    Examples:
        When I soft delete "deals" with "name" "Old Deal"
        When I soft delete "accounts" with "name" "Defunct Corp"
        When I soft delete "contacts" with "email" "former@acme.com"
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    model_name = entity.rstrip("s").capitalize()
    model = apps.get_model("core", model_name)

    instance = model.objects.get(**{field: value})

    response = context.client.delete(f"{endpoint}{instance.id}/")
    _sutils.response_to_context(context, response)
