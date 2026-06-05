"""Given steps: authentication, direct-DB entity creation, and API creation."""

import json
from types import SimpleNamespace

from behave import given
from django.apps import apps
from django.contrib.auth import get_user_model
from steps.domain.constants import ENTITY_CONFIG
from steps.domain.defaults import BaseEntityDefaults
from steps.utils import entity_to_model_name, normalize_entity_name
from steps.domain.user_steps import create_users_from_table

user_model = get_user_model()


# ---------------------------------------------------------------------------
# Authentication setup
# ---------------------------------------------------------------------------


@given('I am "{auth_state}"')
@given('I am "{auth_state}" as "{auth}"')
def step_auth(context, auth_state, auth=None):
    """
    Unified auth step.

    Logs out when auth_state is 'not authenticated';
    logs in when auth_state is 'authenticated' using the auth target.
    """
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


# ---------------------------------------------------------------------------
# Direct DB operations (bypass the API — for test setup only)
# ---------------------------------------------------------------------------


@given('I create a new "{entity}"')
def step_create_entity_directly(context, entity):
    """
    Create entities directly in the database using a Gherkin table.

    Each row in the table creates one record. Column headers are ORM field
    names; ``*_id`` columns accept a name value resolved to a UUID
    (e.g. ``account_id = "Acme Corp"``).

    Each created object is stored on the context under its first-column label
    and under ``context.<entity>`` so the most recently created object is
    accessible for URL placeholders without a separate ``I store`` step.
    Objects are also collected in ``context.named_<entity>s``.

    User entities are handled separately for password hashing. Entities
    with a ``db_create`` factory in ``ENTITY_CONFIG`` use that factory;
    all others use ``Model.objects.create()`` directly.

    Examples:
        Given I create a new "account"
            | name      | status |
            | Acme Corp | active |

        Given I create a new "task"
            | title   | account_id |
            | My Task | Acme Corp  |
    """
    entity_lower = entity.lower()

    if entity_lower == "user":
        create_users_from_table(context)
        return

    normalized = normalize_entity_name(entity_lower)
    model_name = entity_to_model_name(normalized)
    try:
        model = apps.get_model("core", model_name)
    except LookupError as exc:
        raise ValueError(
            f"Unknown entity '{entity}'. Is it registered in the core app?"
        ) from exc

    config = ENTITY_CONFIG.get(normalized, {})
    db_create = config.get("db_create")

    field_names = {f.name for f in model._meta.get_fields()}
    fk_attnames = {
        f.name: f.attname
        for f in model._meta.get_fields()
        if hasattr(f, "attname") and f.attname != f.name
    }

    for row in context.table:
        data = {key: value for key, value in row.items()}
        data = BaseEntityDefaults.resolve_foreign_key_references(data)

        # Convert string boolean values to actual booleans
        for key, value in data.items():
            if isinstance(value, str):
                if value.lower() == "true":
                    data[key] = True
                elif value.lower() == "false":
                    data[key] = False

        if db_create:
            obj = db_create(data, context.test_user)
        else:
            data = {fk_attnames.get(k, k): v for k, v in data.items()}
            if (
                "owner_user" in field_names
                and "owner_user_id" not in data
                and "owner_user" not in data
            ):
                data["owner_user"] = context.test_user
            if (
                "author" in field_names
                and "author_id" not in data
                and "author" not in data
            ):
                data["author"] = context.test_user
            obj = model.objects.create(**data)

        label = list(row.as_dict().values())[0]
        setattr(context, label, obj)
        setattr(context, entity_lower, obj)

        dict_attr = f"named_{entity_lower}s"
        if not hasattr(context, dict_attr):
            setattr(context, dict_attr, {})
        getattr(context, dict_attr)[label] = obj


@given('I store the "{entity}" with "{field}" "{value}" as "{alias}"')
def step_store_entity_as(context, entity, field, value, alias):
    """
    Look up an entity by field/value and store it on context under an alias.

    The stored alias is available in URL placeholders as ``{alias.attr}``.
    Supports ORM double-underscore lookups for traversing related fields
    (e.g. ``activity__title``).

    Examples:
        Given I store the "task" with "activity__title" "My Task" as "my_task"
        Given I store the "account" with "name" "Acme Corp" as "acme"
        When I send a "POST" request to "/tasks/{context.my_task.id}/complete/"
    """
    entity = normalize_entity_name(entity)
    model = apps.get_model("core", entity_to_model_name(entity))
    instance = model.objects.get(**{field: value})
    setattr(context, alias, instance)


@given('I update "{entity}" with "{field}" "{value}"')
def step_update_entity_directly(context, entity, field, value):
    """
    Update an entity directly in the database from a table row.

    Bypasses the API — use in Given (setup) context only.
    Use 'When I update ...' to exercise the API update path.

    Example:
        Given I update "activities" with "title" "My Task"
            | status    |
            | completed |
    """
    entity = normalize_entity_name(entity)
    model = apps.get_model("core", entity_to_model_name(entity))
    instance = model.objects.get(**{field: value})

    field_names = {f.name for f in model._meta.get_fields()}
    update_data = dict(context.table[0].items())

    for k, v in update_data.items():
        setattr(instance, k, v)
    if "updated_by" in field_names:
        instance.updated_by = context.test_user
    instance.save()


@given('I delete "{entity}" with "{field}" "{value}"')
@given('I delete "{entity}" with "{field}" "{value}" using "{delete_type}"')
def step_delete_entity_directly(context, entity, field, value, delete_type=None):
    """
    Delete an entity directly in the database, bypassing the API.

    Use for test setup only. To exercise the API soft-delete path, use
    ``When I soft delete ...`` instead.

    Omitting ``using`` performs a permanent (hard) delete. Adding
    ``using "soft delete"`` sets ``is_invalid=True`` without removing
    the row. ``using "hard delete"`` is accepted but redundant.

    Examples:
        Given I delete "activities" with "title" "Old Task"
        Given I delete "activities" with "title" "Old Task" using "soft delete"
        Given I delete "activities" with "title" "Old Task" using "hard delete"
    """
    entity = normalize_entity_name(entity)
    model = apps.get_model("core", entity_to_model_name(entity))

    if delete_type and delete_type.strip().lower() == "soft delete":
        instance = model.objects.get(**{field: value})
        field_names = {f.name for f in model._meta.get_fields()}
        if "is_invalid" not in field_names:
            raise ValueError(
                f"Model {model.__name__} does not support soft delete "
                "(no is_invalid field)"
            )
        instance.is_invalid = True
        if "updated_by" in field_names:
            instance.updated_by = context.test_user
        instance.save()
    else:
        model.objects.filter(**{field: value}).delete()


# ---------------------------------------------------------------------------
# API-based entity creation
# ---------------------------------------------------------------------------


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
            | name   | account_id | stage |
            | Deal 1 | Acme Corp  | lead  |

        Given I create "contacts" through the API
            | first_name | last_name | account_id |
            | John       | Doe       | Acme Corp  |
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
        author_username = complete_data.pop("author_username", None)

        # Get or create user for entity ownership (check author_username first for Note entities)
        if author_username:
            user = defaults_class.get_or_create_user(context, author_username)
        elif owner_username:
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
        created_obj = response.json()
        created_list.append(created_obj)
        
        # Store the last created object as singular attribute (e.g., context.account)
        # This allows URL placeholders like {account.id} to work
        entity_singular = entity.rstrip('s')  # Simple pluralization removal
        setattr(context, entity_singular, SimpleNamespace(**created_obj))

    context.response = response


@given('I generate "{count}" "{entity}" through the API')
@given('I generate "{count}" "{entity}" with "{field}" "{value}" through the API')
def step_generate_multiple_entities(context, count, entity, field=None, value=None):
    """
    Generate a set number of entities using auto-generated default values.

    Each entity is created with a unique set of defaults from the entity's
    defaults class. An optional field/value pair can be applied to every
    entity, useful for setting a shared foreign key across all records.

    Examples:
        Given I generate "50" "contacts" through the API
        Given I generate "10" "tasks" with "account_id" "Acme" through the API
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
    default_username = (
        getattr(defaults_class, "DEFAULT_AUTHOR_USERNAME", None)
        or getattr(defaults_class, "DEFAULT_OWNER_USERNAME", None)
    )
    user = defaults_class.get_or_create_user(context, default_username)
    context.client.force_login(user)

    for _ in range(count):
        # Use all defaults (empty row data)
        row_data = {}
        if field:
            row_data[field] = value
        complete_data = defaults_class.prepare_entity_data(row_data)
        complete_data.pop("owner_username", None)
        complete_data.pop("author_username", None)

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


@given('I create "{count}" "{entity}" for "{parent_entity}" "{parent_value}"')
def step_create_multiple_entities_for_parent(context, count, entity, parent_entity, parent_value):
    """
    Create multiple entities for a specific parent entity.
    
    Uses auto-generated default values for each entity, with all linked to the specified parent.
    
    Examples:
        Given I create "25" tasks for account "Test Corp"
        Given I create "10" notes for contact "John Doe"
    """
    entity = normalize_entity_name(entity)
    parent_entity = normalize_entity_name(parent_entity)
    
    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}. Add it to ENTITY_CONFIG.")
    
    count = int(count)
    
    # Determine the foreign key field name (e.g., "account_id" for parent "account")
    parent_singular = parent_entity.rstrip('s')
    fk_field = f"{parent_singular}_id"
    
    # Get entity configuration and defaults handler
    config = ENTITY_CONFIG[entity]
    context_attr = config["context_attr"]
    endpoint = config["endpoint"]
    defaults_class = config["defaults_class"]
    
    if not hasattr(context, context_attr):
        setattr(context, context_attr, [])
    
    created_list = getattr(context, context_attr)
    
    # Create the specified number of entities
    for i in range(count):
        # Generate defaults
        row_data = {fk_field: parent_value}
        complete_data = defaults_class.prepare_entity_data(row_data)
        
        # Add a unique title/name to avoid duplicates
        if 'title' in complete_data:
            complete_data['title'] = f"{complete_data.get('title', 'Item')} {i+1}"
        elif 'name' in complete_data:
            complete_data['name'] = f"{complete_data.get('name', 'Item')} {i+1}"
        
        owner_username = complete_data.pop("owner_username", None)
        author_username = complete_data.pop("author_username", None)
        
        # Get or create user
        if author_username:
            user = defaults_class.get_or_create_user(context, author_username)
        elif owner_username:
            user = defaults_class.get_or_create_user(context, owner_username)
        else:
            user = context.test_user
        
        context.client.force_login(user)
        
        # Create via API
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
