"""Constants and configuration for BDD tests."""

from steps.domain.defaults import (
    AccountDefaults,
    ActivityDefaults,
    CallDefaults,
    ContactDefaults,
    DealDefaults,
    EventDefaults,
    MeetingDefaults,
    NoteDefaults,
    RuleDefaults,
    TaskDefaults,
    TriggerDefaults,
    WorkflowDefaults,
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
    "calls": {
        "endpoint": "/calls/",
        "context_attr": "created_calls",
        "defaults_class": CallDefaults,
        "db_create": CallDefaults.db_create,
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
    "events": {
        "endpoint": "/events/",
        "context_attr": "created_events",
        "defaults_class": EventDefaults,
        "db_create": EventDefaults.db_create,
    },
    "meetings": {
        "endpoint": "/meetings/",
        "context_attr": "created_meetings",
        "defaults_class": MeetingDefaults,
        "db_create": MeetingDefaults.db_create,
    },
    "notes": {
        "endpoint": "/notes/",
        "context_attr": "created_notes",
        "defaults_class": NoteDefaults,
    },
    "rules": {
        "endpoint": "/rules/",
        "context_attr": "created_rules",
        "defaults_class": RuleDefaults,
        "db_create": RuleDefaults.db_create,
    },
    "tasks": {
        "endpoint": "/tasks/",
        "context_attr": "created_tasks",
        "defaults_class": TaskDefaults,
        "db_create": TaskDefaults.db_create,
    },
    "triggers": {
        "endpoint": "/triggers/",
        "context_attr": "created_triggers",
        "defaults_class": TriggerDefaults,
    },
    "workflows": {
        "endpoint": "/workflows/",
        "context_attr": "created_workflows",
        "defaults_class": WorkflowDefaults,
    },
}
