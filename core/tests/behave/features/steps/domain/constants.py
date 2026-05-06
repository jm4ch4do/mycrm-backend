"""
Constants and configuration for BDD tests.
"""

from steps.domain.entity_defaults import AccountDefaults, ActivityDefaults, ContactDefaults, DealDefaults

# Entity mapping: maps entity names to their API endpoints, context attributes, and default handlers
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
}
