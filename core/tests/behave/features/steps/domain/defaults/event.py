"""Default payloads for Event-related BDD setup."""

import uuid

from core.services.domain.event_service import emit_event
from steps.domain.defaults.base import BaseEntityDefaults


class EventDefaults(BaseEntityDefaults):
    """Defaults for immutable Event test records."""

    EVENT_TYPE = "deal.stage_changed"
    SOURCE_SERVICE = "core"
    ENTITY_TYPE = "Deal"
    AFTER_STATE = {"stage": "qualified"}

    @staticmethod
    def _get_defaults(row_data):
        data = {
            "event_type": EventDefaults.EVENT_TYPE,
            "source_service": EventDefaults.SOURCE_SERVICE,
            "entity_type": EventDefaults.ENTITY_TYPE,
            "entity_id": uuid.uuid4(),
            "after_state": EventDefaults.AFTER_STATE,
        }
        data.update(row_data)
        return data

    @staticmethod
    def db_create(data, user):
        """Create Event via shared emit_event utility (no direct ORM create)."""
        payload = EventDefaults._get_defaults(data)

        # Generic FK resolver rewrites e.g. deal_id -> deal. Map back here.
        for model_key, model_name in {
            "account": "Account",
            "activity": "Activity",
            "call": "Call",
            "contact": "Contact",
            "deal": "Deal",
            "meeting": "Meeting",
            "note": "Note",
            "task": "Task",
        }.items():
            if model_key in payload and "entity_id" not in payload:
                payload["entity_id"] = payload.pop(model_key)
                payload.setdefault("entity_type", model_name)

        return emit_event(
            event_type=payload["event_type"],
            source_service=payload["source_service"],
            entity_type=payload["entity_type"],
            entity_id=payload["entity_id"],
            after_state=payload["after_state"],
            before_state=payload.get("before_state"),
            metadata=payload.get("metadata"),
            emitted_by_user_id=payload.get("emitted_by_user_id"),
            created_by=user,
        )
