"""
Steps for contact association operations (add/remove contacts to/from entities).
"""

import json

from behave import given, when
from django.apps import apps

import utils as _sutils
from steps.constants import ENTITY_CONFIG
from steps.utils import normalize_entity_name

from core.models import Contact


@given('I add contact "{email}" to "{entity}" with "{field}" "{value}"')
@when('I add contact "{email}" to "{entity}" with "{field}" "{value}"')
def step_add_contact_to_entity(context, email, entity, field, value):
    """
    Add a contact to an entity via the API.

    Looks up both the contact (by email) and the target entity (by field/value),
    then POSTs the contact's ID to the entity's /contacts/ sub-endpoint.
    Works with any entity that has a contacts association endpoint.

    Examples:
        Given I add contact "john@acme.com" to "deal" with "name" "Enterprise License"
        When I add contact "sarah@acme.com" to "deal" with "name" "Support Contract"
        Given I add contact "jane@acme.com" to "account" with "name" "Acme Corp"
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    model_name = entity.rstrip("s").capitalize()
    model = apps.get_model("core", model_name)

    instance = model.objects.get(**{field: value})
    contact = Contact.objects.get(email=email)

    response = context.client.post(
        f"{endpoint}{instance.id}/contacts/",
        data=json.dumps({"contact": str(contact.id)}),
        content_type="application/json",
    )
    _sutils.response_to_context(context, response)


@when('I remove contact "{email}" from "{entity}" with "{field}" "{value}"')
def step_remove_contact_from_entity(context, email, entity, field, value):
    """
    Remove a contact from an entity via the API.

    Looks up both the contact (by email) and the target entity (by field/value),
    then sends a DELETE request to the entity's /contacts/{contact_id}/ sub-endpoint.

    Examples:
        When I remove contact "john@acme.com" from "deal" with "name" "Enterprise License"
        When I remove contact "jane@acme.com" from "account" with "name" "Acme Corp"
    """
    entity = normalize_entity_name(entity)

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unknown entity type: {entity}")

    config = ENTITY_CONFIG[entity]
    endpoint = config["endpoint"]

    model_name = entity.rstrip("s").capitalize()
    model = apps.get_model("core", model_name)

    instance = model.objects.get(**{field: value})
    contact = Contact.objects.get(email=email)

    response = context.client.delete(
        f"{endpoint}{instance.id}/contacts/{contact.id}/",
    )
    _sutils.response_to_context(context, response)
