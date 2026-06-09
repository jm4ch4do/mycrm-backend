"""Tests for EventService and emit_event utility."""

from __future__ import annotations

import uuid

import pytest

from core.models import Event, EventSourceService
from core.services.domain.event_service import EventService, emit_event


@pytest.mark.django_db
class TestEmitEvent:
    """Test emit_event utility behavior."""

    def test_emit_event_creates_event_record(self, test_user):
        """emit_event creates and returns an Event record."""
        entity_id = uuid.uuid4()

        event = emit_event(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=entity_id,
            before_state={"stage": "lead"},
            after_state={"stage": "qualified"},
            metadata={"request_id": "req-123"},
            emitted_by_user_id=test_user.id,
            created_by=test_user,
        )

        assert Event.objects.count() == 1
        assert event.event_type == "deal.stage_changed"
        assert event.source_service == EventSourceService.CORE
        assert event.entity_type == "Deal"
        assert event.entity_id == entity_id
        assert event.before_state == {"stage": "lead"}
        assert event.after_state == {"stage": "qualified"}
        assert event.metadata == {"request_id": "req-123"}
        assert event.emitted_by_user_id == test_user.id

    def test_emit_event_requires_event_type(self):
        """emit_event raises ValueError when event_type is blank/invalid."""
        with pytest.raises(ValueError, match="event_type"):
            emit_event(
                event_type="",
                source_service=EventSourceService.CORE,
                entity_type="Deal",
                entity_id=uuid.uuid4(),
                after_state={"stage": "qualified"},
            )

        with pytest.raises(ValueError, match="dot-notation"):
            emit_event(
                event_type="deal_updated",
                source_service=EventSourceService.CORE,
                entity_type="Deal",
                entity_id=uuid.uuid4(),
                after_state={"stage": "qualified"},
            )

    def test_emit_event_requires_after_state(self):
        """emit_event raises ValueError when after_state is missing."""
        with pytest.raises(ValueError, match="after_state"):
            emit_event(
                event_type="deal.stage_changed",
                source_service=EventSourceService.CORE,
                entity_type="Deal",
                entity_id=uuid.uuid4(),
                after_state=None,
            )

    def test_emit_event_before_state_optional(self):
        """emit_event allows before_state to be omitted (None)."""
        event = emit_event(
            event_type="deal.created",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "lead"},
        )

        assert event.before_state is None

    def test_emit_event_sets_created_by(self, test_user):
        """emit_event stores created_by when provided by caller."""
        event = emit_event(
            event_type="task.completed",
            source_service=EventSourceService.ACTIVITIES,
            entity_type="Task",
            entity_id=uuid.uuid4(),
            after_state={"state": "completed"},
            created_by=test_user,
        )

        assert event.created_by == test_user


@pytest.mark.django_db
class TestEventServiceRead:
    """Test EventService read methods."""

    def test_get_event_returns_correct_record(self):
        """get_event returns the expected event by id."""
        event = Event.objects.create(
            event_type="deal.created",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "lead"},
        )

        fetched = EventService.get_event(event.id)
        assert fetched.id == event.id

    def test_get_event_raises_for_unknown_id(self):
        """get_event raises Event.DoesNotExist for unknown ids."""
        with pytest.raises(Event.DoesNotExist):
            EventService.get_event(uuid.uuid4())

    def test_list_events_filters_by_event_type(self):
        """list_events applies event_type filtering."""
        Event.objects.create(
            event_type="task.completed",
            source_service=EventSourceService.ACTIVITIES,
            entity_type="Task",
            entity_id=uuid.uuid4(),
            after_state={"state": "completed"},
        )
        Event.objects.create(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "qualified"},
        )

        events = list(EventService.list_events({"event_type": "task.completed"}))

        assert len(events) == 1
        assert events[0].event_type == "task.completed"

    def test_list_events_filters_by_entity_type_and_id(self):
        """list_events applies entity_type + entity_id filtering."""
        target_id = uuid.uuid4()
        Event.objects.create(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=target_id,
            after_state={"stage": "qualified"},
        )
        Event.objects.create(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "proposal"},
        )

        events = list(
            EventService.list_events(
                {
                    "entity_type": "Deal",
                    "entity_id": target_id,
                }
            )
        )

        assert len(events) == 1
        assert events[0].entity_type == "Deal"
        assert events[0].entity_id == target_id
