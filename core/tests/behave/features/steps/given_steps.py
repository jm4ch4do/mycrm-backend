"""
Given steps: authentication setup, direct-DB state preparation, and API-based entity creation.
"""

import json
from behave import given
from django.apps import apps
from django.contrib.auth import get_user_model
from steps.domain.constants import ENTITY_CONFIG
from steps.domain.entity_defaults import BaseEntityDefaults
from steps.utils import entity_to_model_name, normalize_entity_name
from steps.domain.user_steps import create_users_from_table

user_model = get_user_model()


# ---------------------------------------------------------------------------
# Authentication setup
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Direct DB operations (bypass the API — for test setup only)
# ---------------------------------------------------------------------------


@given('I create a new "{entity}"')
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
        Given I create a new "user"
            | username   | password    |
            | targetuser | testpass123 |

        Given I create a new "account"
            | name      | status |
            | Acme Corp | active |
    """
    entity_lower = entity.lower()

    if entity_lower == "user":
        create_users_from_table(context)
        return

    model_name = entity_to_model_name(normalize_entity_name(entity_lower))
    try:
        model = apps.get_model("core", model_name)
    except LookupError as exc:
        raise ValueError(
            f"Unknown entity '{entity}'. Is it registered in the core app?"
        ) from exc

    field_names = {f.name for f in model._meta.get_fields()}

    # Map FK field names to their attname (e.g. 'account' -> 'account_id')
    # The ORM accepts account_id="<uuid>" but not account="<uuid-string>"
    fk_attnames = {
        f.name: f.attname
        for f in model._meta.get_fields()
        if hasattr(f, "attname") and f.attname != f.name
    }

    for row in context.table:
        data = {key: value for key, value in row.items()}

        # Resolve FK references (e.g. account_id="Acme Corp" -> account="<uuid>")
        data = BaseEntityDefaults.resolve_foreign_key_references(data)

        # Rename FK keys to _id form so the ORM accepts string UUIDs
        data = {fk_attnames.get(k, k): v for k, v in data.items()}

        # Inject owner_user from the test context if the model has it and it wasn't supplied
        if (
            "owner_user" in field_names
            and "owner_user_id" not in data
            and "owner_user" not in data
        ):
            data["owner_user"] = context.test_user

        obj = model.objects.create(**data)

        label = list(row.as_dict().values())[0]
        setattr(context, label, obj)

        dict_attr = f"named_{entity_lower}s"
        if not hasattr(context, dict_attr):
            setattr(context, dict_attr, {})
        getattr(context, dict_attr)[label] = obj


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
    Delete an entity directly in the database.

    Bypasses the API — use in Given (setup) context only.
    Use 'When I soft delete ...' to exercise the API delete path.

    Default is a permanent (hard) delete — omitting 'using' is the preferred form.
    Add 'using "soft delete"' to set is_invalid=True and keep the row instead.
    'using "hard delete"' is also accepted for explicitness but not normally needed.

    Examples:
        Given I delete "activities" with "title" "Old Task"                          # preferred
        Given I delete "activities" with "title" "Old Task" using "soft delete"
        Given I delete "activities" with "title" "Old Task" using "hard delete"      # explicit, same as default
    """
    entity = normalize_entity_name(entity)
    model = apps.get_model("core", entity_to_model_name(entity))

    if delete_type and delete_type.strip().lower() == "soft delete":
        instance = model.objects.get(**{field: value})
        field_names = {f.name for f in model._meta.get_fields()}
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
