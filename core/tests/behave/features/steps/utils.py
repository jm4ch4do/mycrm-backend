"""Common utility functions for all behave steps."""

import json
import re
from types import SimpleNamespace
from urllib.parse import urlencode
from django.apps import apps
from django.contrib.auth import get_user_model

# Maps plural entity names to their Django model class names (irregular plurals).
SINGULAR_MAP = {
    "activities": "Activity",
    "execution_logs": "ExecutionLog",
}


class EntityContext(SimpleNamespace):
    """Namespace that exposes the latest created entity instance."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.latest = None

    def __getattr__(self, attr):
        latest = self.__dict__.get("latest")
        if latest is not None:
            return getattr(latest, attr)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{attr}'"
        )


def entity_to_model_name(entity_name):
    """Convert a plural entity name to its Django model class name."""
    entity_lower = entity_name.lower()
    if entity_lower in SINGULAR_MAP:
        return SINGULAR_MAP[entity_lower]
    return entity_lower.rstrip("s").capitalize()


def resolve_model(entity_name):
    """Return the model class for a plural or singular entity name."""
    name = entity_to_model_name(entity_name)
    if name.lower() == "user":
        return get_user_model()
    return apps.get_model("core", name)


def ensure_entity_context(context, entity_name):
    """Return the context namespace used to store created entity instances."""
    existing = getattr(context, entity_name, None)
    if isinstance(existing, EntityContext):
        return existing

    entity_context = EntityContext()
    if existing is not None:
        entity_context.latest = existing
    setattr(context, entity_name, entity_context)
    return entity_context


def store_entity_on_context(context, entity_name, entity, tid=None):
    """Store an entity under ``context.<entity_name>`` and optional test id."""
    entity_context = ensure_entity_context(context, entity_name)
    entity_context.latest = entity
    if tid:
        setattr(entity_context, tid, entity)
    return entity_context


def resolve_context_reference(value, context):
    """Resolve ``@entity.attr`` references against behave context objects.

    If the resolved target is an object instance and no explicit field is
    provided (e.g. ``@event.e1``), this returns the object's ``id`` when
    available.
    """
    if not isinstance(value, str) or not value.startswith("@"):
        return value

    parts = value[1:].split(".")
    target = context
    for part in parts:
        target = getattr(target, part)

    # If reference stops at @entity.tid, default to that object's id.
    if len(parts) == 2 and hasattr(target, "id"):
        return str(target.id)

    if hasattr(target, "id") and len(parts) > 2:
        return str(target)

    if hasattr(target, "id"):
        return str(target.id)
    return target


def resolve_table_value(value, context):
    """Resolve table cell values that may reference context objects."""
    if isinstance(value, str):
        value = resolve_url_placeholders(value, context)
        return resolve_context_reference(value, context)
    return value


# Special pluralization rules for entity names (irregular plurals).
PLURALIZATION_RULES = {
    # Maps singular -> plural where adding 's' would be wrong.
    "activity": "activities",
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
    Resolve foreign key references using two patterns.

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


def resolve_url_placeholders(endpoint, context):
    """
    Replace ``{context.varname.attr}`` placeholders in a URL using context attributes.

    The ``context.`` prefix is required to make it explicit that the value is
    read from the behave context.  The bare ``{varname.attr}`` form is also
    accepted for backward compatibility.

    For each token the corresponding object is retrieved via
    ``getattr(context, varname)`` and the placeholder is replaced with
    ``str(getattr(obj, attr))``.

    Examples:
        /tasks/{context.task.id}/complete/  →  /tasks/<uuid>/complete/
        /users/{context.targetuser.id}/     →  /users/42/

    Raises:
        AttributeError: if ``context`` has no attribute ``varname``.
    """

    def _replace(match):
        name, attr = match.group(1), match.group(2)
        obj = getattr(context, name)
        return str(getattr(obj, attr))

    def _replace_context_ref(match):
        return str(resolve_context_reference(match.group(0), context))

    # Matches both {context.varname.attr} and legacy {varname.attr}
    endpoint = re.sub(r"\{(?:context\.)?([^.}]+)\.([^}]+)\}", _replace, endpoint)
    return re.sub(r"@([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+)", _replace_context_ref, endpoint)


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
            value = resolve_url_placeholders(row["value"], context)
            value = resolve_table_value(value, context)

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
