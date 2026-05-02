"""
Given steps for creating entities through the API.
"""

import json
from behave import given
from django.apps import apps
from django.contrib.auth import get_user_model
from steps.domain.constants import ENTITY_CONFIG
from steps.utils import normalize_entity_name
from steps.domain.user_steps import create_users_from_table

user_model = get_user_model()


@given('a new "{entity}" is created')
def step_create_entity_directly(context, entity):
    """
    Create a single entity directly in the database from a column-keyed table.

    Table headers are field names; each row creates one object. The value in
    the first column is used as the context label for that object — stored via
    setattr() (for URL placeholder resolution) and in context.named_<entity>s
    (for domain-specific Then steps).

    For 'user' entities, delegates to create_users_from_table() which handles
    password hashing. All other models use objects.create() directly.
    Models are resolved from the 'core' app by capitalising the entity name.

    Examples:
        Given a new "user" is created
            | username   | password    |
            | targetuser | testpass123 |

        Given a new "account" is created
            | name      | status |
            | Acme Corp | active |
    """
    entity_lower = entity.lower()

    if entity_lower == "user":
        create_users_from_table(context)
        return

    try:
        model = apps.get_model("core", entity_lower.capitalize())
    except LookupError:
        raise ValueError(
            f"Unknown entity '{entity}'. Is it registered in the core app?"
        )

    for row in context.table:
        data = {key: value for key, value in row.items()}
        obj = model.objects.create(**data)

        label = data[context.table.headings[0]]
        setattr(context, label, obj)

        dict_attr = f"named_{entity_lower}s"
        if not hasattr(context, dict_attr):
            setattr(context, dict_attr, {})
        getattr(context, dict_attr)[label] = obj


@given('I am "{auth_state}"')
@given('I am "{auth_state}" as "{auth}"')
def step_auth(context, auth_state, auth=None):
    """Unified auth step. Logs out when auth_state is 'not authenticated';
    logs in when auth_state is 'authenticated' using the auth target."""
    state = auth_state.strip().lower()
    if state == "not authenticated":
        context.client.logout()
    elif state == "authenticated":
        target = (auth or "").strip().lower()
        if target in ("a staff user", "staff user"):
            user = user_model.objects.create_user(
                username="behave_staff", password="pass", is_staff=True
            )
        elif target in ("a regular user", "regular user"):
            user = user_model.objects.create_user(
                username="behave_regular", password="pass"
            )
        else:
            raise ValueError(f"Unknown auth target: '{auth}'")
        context.client.force_login(user)
        context.auth_user = user
    else:
        raise ValueError(f"Unknown auth state: '{auth_state}'")


@given('I create "{entity}" through the API')
@given('I create a "{entity}" through the API')
@given('I create an "{entity}" through the API')
def step_create_entities(context, entity):
    """
    Create one or more entities through the API using a data table.

    Each row in the table becomes a separate POST request. Columns map to
    entity fields; missing columns are filled with defaults from the entity's
    defaults class (see entity_defaults.py). Foreign keys use the name-based
    resolution pattern (e.g. account_id = "Acme Corp").

    An optional "owner_username" column controls which user owns the entity.
    If omitted, the default test user is used.

    Examples:
        Given I create "accounts" through the API
            | name      | status | type     |
            | Acme Corp | active | customer |

        Given I create "deals" through the API
            | name              | account_id | stage    | status | amount    | currency |
            | Enterprise License | Acme Corp  | proposal | open   | 120000.00 | usd      |

        Given I create "contacts" through the API
            | first_name | last_name | email          | account_id | role           | seniority |
            | John       | Doe       | john@acme.com  | Acme Corp  | decision_maker | executive |
    """
    entity = normalize_entity_name(entity)

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
        complete_data = defaults_class.prepare_entity_data(row_data)
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
@given('I generate "{count}" "{entity}" with "{field}" "{value}" through the API')
def step_generate_multiple_entities(context, count, entity, field=None, value=None):
    """
    Generate multiple entities with auto-generated default values.

    Creates the specified number of entities, each with a unique set of
    defaults produced by the entity's defaults class. An optional field/value
    override can be applied to every generated entity (useful for setting a
    shared foreign key).

    Examples:
        Given I generate "50" "contacts" through the API

        Given I generate "10" "deals" with "account_id" "Acme Corp" through the API

        Given I generate "5" "accounts" through the API
    """
    entity = normalize_entity_name(entity)

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
        row_data = {}
        if field:
            row_data[field] = value
        complete_data = defaults_class.prepare_entity_data(row_data)
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
