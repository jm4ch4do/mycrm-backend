"""
When steps for API requests and entity operations.
"""

import json
from behave import when
from django.apps import apps

import utils as _sutils
from steps.domain.constants import ENTITY_CONFIG
from steps.utils import (
    entity_to_model_name,
    normalize_entity_name,
    resolve_foreign_key_pattern,
)

# ---------------------------------------------------------------------------
# Generic HTTP request
# ---------------------------------------------------------------------------


@when('I send a "{method}" request to "{endpoint}"')
@when('I send a "{method}" request to "{endpoint}" with body')
def step_send_request_to_endpoint(context, method, endpoint):
    """
    Send an HTTP request to any API endpoint.

    For GET requests an optional data table supplies query parameters:
        When I send a "GET" request to "/accounts/"
            | field  | operator | value  |
            | status | eq       | active |

    For POST/PUT/PATCH requests an optional data table supplies the request
    body as field/value pairs:
        When I send a "PUT" request to "/users/{targetuser.id}/"
            | field | value   |
            | role  | manager |

    Supported query-param operators (GET only):
        eq (or equals), ne, lt, gt, lte, gte, in, contains, icontains,
        startswith, endswith, isnull
    """
    # Resolve {varname.attr} placeholders (e.g. {targetuser.id} -> 42)
    endpoint = _sutils.resolve_url_placeholders(endpoint, context)

    method = method.upper()

    if method == "GET":
        full_url = _sutils.build_url_with_query_params(endpoint, context)
        response = context.client.get(full_url)
    else:
        # For write methods, use the step's own table as the request body.
        if hasattr(context, "table") and context.table:
            body = {row["field"]: row["value"] for row in context.table}
        else:
            body = getattr(context, "request_data", {})

        kwargs = dict(
            data=json.dumps(body) if body else None,
            content_type="application/json",
        )
        if method == "POST":
            response = context.client.post(endpoint, **kwargs)
        elif method == "PUT":
            response = context.client.put(endpoint, **kwargs)
        elif method == "PATCH":
            response = context.client.patch(endpoint, **kwargs)
        elif method == "DELETE":
            response = context.client.delete(endpoint)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    _sutils.response_to_context(context, response)


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


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
    model = apps.get_model("core", entity_to_model_name(entity))

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


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


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

    model = apps.get_model("core", entity_to_model_name(entity))

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

    model = apps.get_model("core", entity_to_model_name(entity))

    instance = model.objects.get(**{field: value})

    response = context.client.delete(f"{endpoint}{instance.id}/")
    _sutils.response_to_context(context, response)
