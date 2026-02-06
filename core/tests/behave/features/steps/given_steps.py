"""
Given steps for creating entities through the API.
"""

import json
from behave import given
from django.contrib.auth import get_user_model
from steps.constants import ENTITY_CONFIG

User = get_user_model()


@given('I create "{entity}" through the API')
def step_create_entities(context, entity):
    """Create entities through the Django test client."""
    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}. Add it to ENTITY_CONFIG.")

    # Get entity configuration and defaults handler
    config = ENTITY_CONFIG[entity]
    context_attr = config["context_attr"]
    endpoint = config["endpoint"]
    defaults_class = config["defaults_class"]

    if not hasattr(context, context_attr):
        setattr(context, context_attr, [])

    created_list = getattr(context, context_attr)

    for row in context.table:
        # Apply defaults to row data
        row_data = {key: value for key, value in row.items()}
        complete_data = defaults_class.get_defaults(row_data)
        owner_username = complete_data.pop("owner_username", None)

        # Get or create user for entity ownership
        if owner_username:
            user = defaults_class.get_or_create_user(context, owner_username)
        else:
            user = context.test_user

        context.client.force_login(user)

        # Create entity via API
        response = context.client.post(
            endpoint,
            data=json.dumps(complete_data),
            content_type="application/json",
        )

        assert (
            response.status_code == 201
        ), f"Failed to create {entity}: {response.content}"
        created_list.append(response.json())

    context.response = response


@given('I generate "{count}" "{entity}" through the API')
def step_generate_multiple_entities(context, count, entity):
    """Generate multiple entities with auto-generated defaults."""
    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}. Add it to ENTITY_CONFIG.")

    count = int(count)

    # Get entity configuration and defaults handler
    config = ENTITY_CONFIG[entity]
    context_attr = config["context_attr"]
    endpoint = config["endpoint"]
    defaults_class = config["defaults_class"]

    if not hasattr(context, context_attr):
        setattr(context, context_attr, [])

    created_list = getattr(context, context_attr)

    # Get or create default user once
    default_username = defaults_class.DEFAULT_OWNER_USERNAME
    user = defaults_class.get_or_create_user(context, default_username)
    context.client.force_login(user)

    for _ in range(count):
        # Use all defaults (empty row data)
        complete_data = defaults_class.get_defaults({})
        complete_data.pop("owner_username", None)

        # Create entity via API
        response = context.client.post(
            endpoint,
            data=json.dumps(complete_data),
            content_type="application/json",
        )

        assert (
            response.status_code == 201
        ), f"Failed to create {entity}: {response.content}"
        created_list.append(response.json())

    context.response = response
