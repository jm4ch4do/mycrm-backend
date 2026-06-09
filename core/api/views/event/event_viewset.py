"""Read-only API ViewSet for Event model."""

from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response

from core.models import Event
from core.api.serializers.event import EventSerializer
from core.permissions import CanViewEvents
from core.services.domain.event_service import EventService

from .pagination import EventPagination  # pylint: disable=relative-beyond-top-level


class EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only endpoints for immutable event records."""

    serializer_class = EventSerializer
    permission_classes = [CanViewEvents]
    pagination_class = EventPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["event_type", "source_service", "entity_type", "entity_id"]
    search_fields = ["event_type", "entity_type"]
    ordering_fields = ["occurred_at", "created_at"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        """Delegate event list retrieval to the domain service."""
        return EventService.list_events()

    def retrieve(self, request, *args, **kwargs):
        """Delegate single-event retrieval to the domain service."""
        try:
            event = EventService.get_event(kwargs["pk"])
        except Event.DoesNotExist as exc:
            raise Http404("Event not found.") from exc
        self.check_object_permissions(request, event)
        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)
