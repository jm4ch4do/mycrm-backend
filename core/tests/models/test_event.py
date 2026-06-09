"""Unit tests for Event model."""

import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import Event, EventSourceService


class TestEventModel:
    """Test Event model creation, constraints, and ordering."""

    def test_event_str_returns_type_and_entity(
        self, db, test_user
    ):  # pylint: disable=unused-argument
        """__str__ returns event type plus polymorphic entity reference."""
        entity_id = uuid.uuid4()
        event = Event.objects.create(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=entity_id,
            after_state={"stage": "qualified"},
            created_by=test_user,
        )

        assert str(event) == f"deal.stage_changed (Deal:{entity_id})"

    def test_event_requires_event_type(self, db):  # pylint: disable=unused-argument
        """event_type is required and validated by model constraints."""
        event = Event(
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "qualified"},
        )

        with pytest.raises(ValidationError):
            event.full_clean()

    def test_event_requires_after_state(self, db):  # pylint: disable=unused-argument
        """after_state is required and cannot be null."""
        event = Event(
            event_type="deal.stage_changed",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state=None,
        )

        with pytest.raises(ValidationError):
            event.full_clean()

    def test_event_before_state_nullable(self, db):  # pylint: disable=unused-argument
        """before_state accepts null values for create-style events."""
        event = Event.objects.create(
            event_type="deal.created",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            before_state=None,
            after_state={"stage": "lead"},
        )

        assert event.before_state is None

    def test_event_emitted_by_user_id_nullable(
        self, db
    ):  # pylint: disable=unused-argument
        """emitted_by_user_id accepts null for system-generated events."""
        event = Event.objects.create(
            event_type="task.completed",
            source_service=EventSourceService.ACTIVITIES,
            entity_type="Task",
            entity_id=uuid.uuid4(),
            after_state={"state": "completed"},
            emitted_by_user_id=None,
        )

        assert event.emitted_by_user_id is None

    def test_event_ordering_is_newest_first(
        self, db
    ):  # pylint: disable=unused-argument
        """Default ordering returns newest events first by occurred_at."""
        older = Event.objects.create(
            event_type="deal.created",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "lead"},
            occurred_at=timezone.now() - timedelta(minutes=5),
        )
        newer = Event.objects.create(
            event_type="deal.updated",
            source_service=EventSourceService.CORE,
            entity_type="Deal",
            entity_id=uuid.uuid4(),
            after_state={"stage": "qualified"},
            occurred_at=timezone.now(),
        )

        events = list(Event.objects.all())

        assert events[0] == newer
        assert events[1] == older
