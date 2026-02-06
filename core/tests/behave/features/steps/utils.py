"""
Common utility functions for all behave steps.
"""

import json
from urllib.parse import urlencode


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
