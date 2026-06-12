"""Default values handler for ExecutionLog entities."""

from core.models import ExecutionLog
from steps.domain.defaults.base import BaseEntityDefaults


class ExecutionLogDefaults(BaseEntityDefaults):
    """Default values handler for ExecutionLog entities."""

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STEP_LOG_ENTRY = {
        "step_order": 1,
        "action_type": "create_task",
        "status": "success",
        "result": {},
        "error": None,
    }

    @classmethod
    def _get_defaults(cls, row_data):
        defaults = {
            "status": cls.STATUS_PENDING,
            "logs": [],
        }
        return {**defaults, **row_data}

    @classmethod
    def db_create(cls, data, user):
        payload = cls.prepare_entity_data(data)

        workflow_id = payload.pop("workflow", None)
        event_id = payload.pop("event", None)

        return ExecutionLog.objects.create(
            workflow_id=workflow_id,
            event_id=event_id,
            created_by=user,
            **payload,
        )
