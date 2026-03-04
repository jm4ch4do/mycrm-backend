"""
Common utility functions for all behave steps.
"""

import json
import re
from urllib.parse import urlencode
from django.apps import apps


# Special pluralization rules for entity names
PLURALIZATION_RULES = {
    # Add special cases here where simple 's' addition doesn't work
    # e.g., "person": "people", "child": "children"
}


def normalize_entity_name(entity_name):
    """Normalize entity name to plural form for use in ENTITY_CONFIG."""
    entity_lower = entity_name.lower()

    # Check if it's a special case
    if entity_lower in PLURALIZATION_RULES:
        return PLURALIZATION_RULES[entity_lower]

    # If already ends with 's', assume it's plural
    if entity_lower.endswith("s"):
        return entity_lower

    # Simple pluralization: add 's'
    return entity_lower + "s"


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


def resolve_foreign_key_pattern(field_name, value):
    """
    Resolve foreign key references using two patterns:

    Pattern 1: {entity}_id_from_{field}
        Example: account_id_from_name = "Acme Corp"
        Looks up Account by name="Acme Corp"

    Pattern 2: {entity}_id (assumes lookup by field='name')
        Example: account_id = "Acme Corp"
        Looks up Account by name="Acme Corp"

    Args:
        field_name: Field name following the pattern
        value: Value to look up

    Returns:
        tuple: (entity_name, object_id) where object_id is a string UUID
        None: if the field doesn't match any pattern

    Raises:
        ValueError: If model not found or lookup fails
    """
    # Pattern 1: {entity}_id_from_{lookup_field}
    pattern_1 = re.compile(r"^(.+?)_id_from_(.+)$")
    # Pattern 2: {entity}_id (defaults to 'name' lookup)
    pattern_2 = re.compile(r"^(.+?)_id$")

    match = pattern_1.match(field_name)
    if match:
        entity_name = match.group(1)  # e.g., "account"
        lookup_field = match.group(2)  # e.g., "name"
    else:
        match = pattern_2.match(field_name)
        if match:
            entity_name = match.group(1)  # e.g., "account"
            lookup_field = "name"  # Default lookup by 'name'
        else:
            # No pattern match
            return None

    # Convert entity name to model name (account -> Account)
    model_name = entity_name.capitalize()

    try:
        # Get the model class
        model = apps.get_model("core", model_name)

        # Look up the object
        lookup = {lookup_field: value}
        obj = model.objects.get(**lookup)

        # Return entity name and object ID
        return (entity_name, str(obj.id))

    except LookupError as exc:
        raise ValueError(
            f"Model '{model_name}' not found for pattern '{field_name}'"
        ) from exc
    except model.DoesNotExist as exc:
        raise ValueError(
            f"{model_name} with {lookup_field}='{value}' does not exist"
        ) from exc


def build_url_with_query_params(endpoint, context):
    """
    Build a full URL with query parameters from context table.

    Expects context.table with columns: field, operator, value

    Supported operators:
        - eq (or equals): equality (default) - translates to ?field=value
        - ne, lt, gt, lte, gte, in, contains, icontains, startswith, endswith, isnull
          These use Django's double underscore syntax: ?field__operator=value

    Args:
        endpoint: Base URL endpoint (e.g., "/accounts/")
        context: Behave context object with optional table attribute

    Returns:
        Full URL with query parameters appended
    """
    query_params = {}

    if hasattr(context, "table") and context.table:
        for row in context.table:
            field = row["field"]
            operator = row.get("operator", "eq").lower()
            value = row["value"]

            # Build the query parameter key based on operator
            if operator in ("eq", "equals"):
                # For equality, just use the field name
                param_key = field
            else:
                # For other operators, use Django's double underscore syntax
                # Supports: ne, lt, gt, lte, gte, in, contains, icontains,
                #          startswith, endswith, isnull, etc.
                param_key = f"{field}__{operator}"

            query_params[param_key] = value

    # Build the full URL with query parameters
    if query_params:
        query_string = urlencode(query_params)
        return f"{endpoint}?{query_string}"
    else:
        return endpoint


def response_to_context(context, response):
    """
    Store response in context and parse JSON data if available.

    Args:
        context: Behave context object
        response: Django test client response object
    """
    context.response = response

    # Try to parse JSON response if available
    if response.content:
        try:
            context.response_data = response.json()
        except json.JSONDecodeError:
            context.response_data = None
    else:
        context.response_data = None
