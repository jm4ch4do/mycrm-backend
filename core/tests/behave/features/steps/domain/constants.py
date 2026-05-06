"""Constants and configuration for BDD tests."""

from steps.domain.entity_defaults import (
    AccountDefaults,
    ActivityDefaults,
    ContactDefaults,
    DealDefaults,
    TaskDefaults,
)

# Per-entity step configuration: endpoint URL, context attribute, defaults
# class, and an optional db_create factory for direct-DB creation.
ENTITY_CONFIG = {
    "accounts": {
        "endpoint": "/accounts/",
        "context_attr": "created_accounts",
        "defaults_class": AccountDefaults,
    },
    "activities": {
        "endpoint": "/activities/",
        "context_attr": "created_activities",
        "defaults_class": ActivityDefaults,
    },
    "contacts": {
        "endpoint": "/contacts/",
        "context_attr": "created_contacts",
        "defaults_class": ContactDefaults,
    },
    "deals": {
        "endpoint": "/deals/",
        "context_attr": "created_deals",
        "defaults_class": DealDefaults,
    },
    "tasks": {
        "endpoint": "/tasks/",
        "context_attr": "created_tasks",
        "defaults_class": TaskDefaults,
        "db_create": TaskDefaults.db_create,
    },
}
