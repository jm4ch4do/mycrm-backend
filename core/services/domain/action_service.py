"""Business logic service for Action model."""

from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.models import Action, ActionType, Note, Task
from core.services.domain.deal_service import DealService
from core.services.domain.event_service import emit_event
from core.services.domain.note_service import NoteService
from core.services.domain.task_service import TaskService

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User

    from core.models import Event, ExecutionLog


user_model = get_user_model()


def _validate_action_type(action_type: str) -> str:
    """Validate and normalize action_type."""
    if action_type not in ActionType.values:
        raise ValueError(f"Unsupported action_type '{action_type}'.")
    return action_type


def _required_keys_for_action_type(action_type: str) -> set[str]:
    """Return the required parameter keys for an action type."""
    return {
        ActionType.CREATE_TASK: {"title"},
        ActionType.UPDATE_DEAL_STAGE: {"stage"},
        ActionType.ASSIGN_OWNER: {"owner_user_id"},
        ActionType.ADD_NOTE: {"body"},
        ActionType.EMIT_EVENT: {"event_type"},
    }[action_type]


def _validate_parameters(action_type: str, parameters: dict[str, Any] | None) -> list[str]:
    """Validate parameters for the given action type and return notes."""
    notes: list[str] = []
    payload = parameters or {}

    if not isinstance(payload, dict):
        raise ValueError("parameters must be a JSON object.")

    missing = sorted(
        key for key in _required_keys_for_action_type(action_type) if not payload.get(key)
    )
    if missing:
        raise ValueError(
            f"parameters for '{action_type}' are missing required keys: {', '.join(missing)}."
        )

    if action_type == ActionType.CREATE_TASK and "due_days_from_now" in payload:
        try:
            int(payload["due_days_from_now"])
        except (TypeError, ValueError) as exc:
            raise ValueError("due_days_from_now must be an integer.") from exc
        notes.append("due_days_from_now accepted")

    if action_type == ActionType.ASSIGN_OWNER:
        owner_user_id = payload.get("owner_user_id")
        if not user_model.objects.filter(id=owner_user_id).exists():
            raise ValueError("owner_user_id must reference an existing user.")
        notes.append("owner_user_id resolved")

    return notes


def _resolve_related_target(event: Event) -> tuple[str | None, Any | None]:
    """Resolve the model instance targeted by the event entity reference."""
    entity_type = (event.entity_type or "").strip().lower().rstrip("s")
    if not entity_type:
        return None, None

    model_name = entity_type.capitalize()
    try:
        model = apps.get_model("core", model_name)
    except LookupError:
        return entity_type, None

    try:
        return entity_type, model.objects.get(id=event.entity_id)
    except model.DoesNotExist:
        return entity_type, None


def _get_execution_user(action: Action, execution_log: ExecutionLog):
    """Resolve the user context for handlers that create or update records."""
    return execution_log.triggered_by or action.updated_by or action.created_by


class ActionService:
    """Service layer for Action business logic."""

    @staticmethod
    def validate_parameters_for_type(
        action_type: str,
        parameters: dict[str, Any] | None,
    ) -> list[str]:
        """Validate a parameter payload for an action type and return notes."""
        normalized_type = _validate_action_type(action_type)
        return _validate_parameters(normalized_type, parameters)

    @staticmethod
    def list_actions(filters: dict[str, Any] | None = None) -> QuerySet[Action]:
        """List non-deleted actions with optional filtering."""
        queryset = Action.objects.filter(is_invalid=False)

        if filters:
            allowed = {"action_type"}
            applied_filters = {
                key: value
                for key, value in filters.items()
                if key in allowed and value not in (None, "")
            }
            if applied_filters:
                queryset = queryset.filter(**applied_filters)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_action(action_id: UUID | str) -> Action:
        """Retrieve a non-deleted action by ID."""
        return Action.objects.get(id=action_id, is_invalid=False)

    @staticmethod
    @transaction.atomic
    def create_action(data: dict[str, Any], created_by: User) -> Action:
        """Create an action and set audit fields."""
        payload = data.copy()
        payload["action_type"] = _validate_action_type(payload.get("action_type", ""))

        if payload.get("parameters") is not None:
            _validate_parameters(payload["action_type"], payload.get("parameters"))

        return Action.objects.create(
            created_by=created_by,
            updated_by=created_by,
            **payload,
        )

    @staticmethod
    @transaction.atomic
    def update_action(action: Action, data: dict[str, Any], updated_by: User) -> Action:
        """Update mutable action fields and set updated_by."""
        payload = data.copy()

        for field in ["id", "created_at", "created_by", "is_invalid"]:
            payload.pop(field, None)

        action_type = payload.get("action_type", action.action_type)
        payload["action_type"] = _validate_action_type(action_type)

        if "parameters" in payload and payload["parameters"] is not None:
            _validate_parameters(payload["action_type"], payload["parameters"])

        payload["updated_by"] = updated_by
        for field, value in payload.items():
            setattr(action, field, value)

        action.save()
        return action

    @staticmethod
    @transaction.atomic
    def delete_action(action: Action, updated_by: User) -> None:
        """Soft-delete an action by marking it invalid."""
        action.is_invalid = True
        action.updated_by = updated_by
        action.save()

    @staticmethod
    def dry_run(action: Action, event_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Validate action parameters against its type without execution."""
        notes = _validate_parameters(action.action_type, action.parameters)
        if event_payload is not None:
            if not isinstance(event_payload, dict):
                raise ValueError("event_payload must be a JSON object.")
            notes.append("event_payload accepted")
        return {"valid": True, "notes": notes}

    @staticmethod
    def execute_action(action: Action, event: Event, execution_log: ExecutionLog) -> dict[str, Any]:
        """Execute an action handler and return a result dict."""
        handlers = {
            ActionType.CREATE_TASK: ActionService._handle_create_task,
            ActionType.UPDATE_DEAL_STAGE: ActionService._handle_update_deal_stage,
            ActionType.ASSIGN_OWNER: ActionService._handle_assign_owner,
            ActionType.ADD_NOTE: ActionService._handle_add_note,
            ActionType.EMIT_EVENT: ActionService._handle_emit_event,
        }

        handler = handlers.get(action.action_type)
        if handler is None:
            raise ValueError(f"Unsupported action_type '{action.action_type}'.")

        if action.is_invalid:
            return {"status": "failed", "error": "Action is soft-deleted."}

        started = monotonic()
        try:
            result = handler(action, event, execution_log)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return {"status": "failed", "error": str(exc)}

        if action.timeout_seconds is not None:
            elapsed = monotonic() - started
            if elapsed > action.timeout_seconds:
                return {
                    "status": "failed",
                    "error": f"Action exceeded timeout of {action.timeout_seconds} seconds.",
                }

        return {"status": "success", "result": result}

    @staticmethod
    def _handle_create_task(action: Action, event: Event, execution_log: ExecutionLog) -> dict[str, Any]:
        """Create or reuse a task for the event target."""
        parameters = action.parameters or {}
        _validate_parameters(action.action_type, parameters)
        user = _get_execution_user(action, execution_log)
        if user is None:
            raise ValueError("Action execution requires a user context.")

        entity_type, target = _resolve_related_target(event)
        filters = {
            "activity__title": parameters["title"],
            "activity__is_invalid": False,
        }
        if entity_type in {"account", "contact", "deal"} and target is not None:
            filters[f"activity__{entity_type}"] = target

        existing_task = Task.objects.filter(**filters).first()
        if existing_task is not None:
            return {"task_id": str(existing_task.id), "created": False}

        task_data: dict[str, Any] = {
            "title": parameters["title"],
            "description": parameters.get("description"),
        }
        if entity_type in {"account", "contact", "deal"} and target is not None:
            task_data[entity_type] = target
        if parameters.get("due_days_from_now") is not None:
            task_data["due_at"] = timezone.now() + timezone.timedelta(
                days=int(parameters["due_days_from_now"])
            )

        task = TaskService.create_task(task_data, user)
        return {"task_id": str(task.id), "created": True}

    @staticmethod
    def _handle_update_deal_stage(
        action: Action,
        event: Event,
        execution_log: ExecutionLog,
    ) -> dict[str, Any]:
        """Update a deal stage using the event target or an explicit parameter."""
        parameters = action.parameters or {}
        _validate_parameters(action.action_type, parameters)
        user = _get_execution_user(action, execution_log)
        if user is None:
            raise ValueError("Action execution requires a user context.")

        deal_id = parameters.get("deal_id")
        if deal_id is None and (event.entity_type or "").strip().lower() == "deal":
            deal_id = event.entity_id
        if deal_id is None:
            raise ValueError("update_deal_stage requires a deal target.")

        deal = DealService.get_deal(deal_id)
        updated = DealService.update_deal(deal, {"stage": parameters["stage"]}, user)
        return {"deal_id": str(updated.id), "stage": updated.stage}

    @staticmethod
    def _handle_assign_owner(action: Action, event: Event, execution_log: ExecutionLog) -> dict[str, Any]:
        """Assign an owner to the event target entity."""
        parameters = action.parameters or {}
        _validate_parameters(action.action_type, parameters)

        owner = user_model.objects.get(id=parameters["owner_user_id"])
        entity_type, target = _resolve_related_target(event)
        if target is None:
            raise ValueError("assign_owner requires a resolvable event target.")
        if not hasattr(target, "owner_user"):
            raise ValueError(f"{target.__class__.__name__} does not support owner assignment.")

        target.owner_user = owner
        if hasattr(target, "updated_by"):
            target.updated_by = _get_execution_user(action, execution_log)
            target.save(update_fields=["owner_user", "updated_by"])
        else:
            target.save(update_fields=["owner_user"])

        return {
            "entity_type": entity_type,
            "entity_id": str(target.id),
            "owner_user_id": str(owner.id),
        }

    @staticmethod
    def _handle_add_note(action: Action, event: Event, execution_log: ExecutionLog) -> dict[str, Any]:
        """Create or reuse a note for the event target."""
        parameters = action.parameters or {}
        _validate_parameters(action.action_type, parameters)
        user = _get_execution_user(action, execution_log)
        if user is None:
            raise ValueError("Action execution requires a user context.")

        entity_type, target = _resolve_related_target(event)
        filters = {
            "body": parameters["body"],
            "title": parameters.get("title", ""),
            "is_invalid": False,
        }
        if entity_type in {"account", "contact", "deal"} and target is not None:
            filters[entity_type] = target

        existing_note = Note.objects.filter(**filters).first()
        if existing_note is not None:
            return {"note_id": str(existing_note.id), "created": False}

        note_data: dict[str, Any] = {
            "title": parameters.get("title", ""),
            "body": parameters["body"],
        }
        if entity_type in {"account", "contact", "deal"} and target is not None:
            note_data[entity_type] = target
        if parameters.get("visibility") is not None:
            note_data["visibility"] = parameters["visibility"]

        note = NoteService.create_note(note_data, user)
        return {"note_id": str(note.id), "created": True}

    @staticmethod
    def _handle_emit_event(action: Action, event: Event, execution_log: ExecutionLog) -> dict[str, Any]:
        """Emit a downstream event record."""
        parameters = action.parameters or {}
        _validate_parameters(action.action_type, parameters)

        emitted_event = emit_event(
            event_type=parameters["event_type"],
            source_service=parameters.get("source_service", event.source_service),
            entity_type=parameters.get("entity_type", event.entity_type),
            entity_id=parameters.get("entity_id", event.entity_id),
            after_state=parameters.get("after_state", event.after_state),
            before_state=parameters.get("before_state", event.before_state),
            metadata=parameters.get("metadata"),
            emitted_by_user_id=getattr(execution_log.triggered_by, "id", None),
            created_by=_get_execution_user(action, execution_log),
        )
        return {"event_id": str(emitted_event.id)}