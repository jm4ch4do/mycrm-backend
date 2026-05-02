"""
Constants and configuration for BDD tests.
"""

from steps.domain.entity_defaults import AccountDefaults, ContactDefaults, DealDefaults

# Entity mapping: maps entity names to their API endpoints, context attributes, and default handlers
ENTITY_CONFIG = {
    "accounts": {
        "endpoint": "/accounts/",
        "context_attr": "created_accounts",
        "defaults_class": AccountDefaults,
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
