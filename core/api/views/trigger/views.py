from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.serializers.trigger import TriggerSerializer
from core.models import Trigger
from core.permissions import CanManageTriggers
from core.services.domain.trigger_service import TriggerService

from .pagination import TriggerPagination  # pylint: disable=relative-beyond-top-level


class TriggerViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Trigger model."""

    queryset = Trigger.objects.all()
    serializer_class = TriggerSerializer
    permission_classes = [CanManageTriggers]
    pagination_class = TriggerPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["event_type", "entity_type", "is_active"]
    search_fields = ["name", "description", "event_type", "entity_type"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):  # pylint: disable=unused-argument
        """Activate a trigger."""
        trigger = self.get_object()
        updated = TriggerService.update_trigger(
            trigger,
            {"is_active": True},
            request.user,
        )
        return Response(TriggerSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):  # pylint: disable=unused-argument
        """Deactivate a trigger."""
        trigger = self.get_object()
        updated = TriggerService.update_trigger(
            trigger,
            {"is_active": False},
            request.user,
        )
        return Response(TriggerSerializer(updated, context={"request": request}).data)

    def destroy(self, request, *args, **kwargs):
        """Soft delete a trigger."""
        instance = self.get_object()
        TriggerService.delete_trigger(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Delegate trigger list retrieval to the domain service."""
        return TriggerService.list_triggers()

    def get_object(self):
        """Delegate single-trigger retrieval to the domain service."""
        obj = TriggerService.get_trigger(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        """Delegate trigger creation to the domain service."""
        trigger = TriggerService.create_trigger(serializer.validated_data, self.request.user)
        serializer.instance = trigger

    def perform_update(self, serializer):
        """Delegate trigger update to the domain service."""
        TriggerService.update_trigger(
            serializer.instance,
            serializer.validated_data,
            self.request.user,
        )
