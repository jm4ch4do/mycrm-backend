from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.api.serializers.action import ActionSerializer
from core.models import Action
from core.services.domain.action_service import ActionService


class ActionViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Action model."""

    queryset = Action.objects.all()
    serializer_class = ActionSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAdminUser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["action_type"]
    search_fields = ["name", "action_type"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Delegate action list retrieval to the domain service."""
        return ActionService.list_actions(filters=self.request.query_params)

    def get_object(self):
        """Delegate single-action retrieval to the domain service."""
        try:
            obj = ActionService.get_action(self.kwargs["pk"])
        except Action.DoesNotExist as exc:
            raise NotFound("No Action matches the given query.") from exc
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, *args, **kwargs):
        """Soft delete an action."""
        instance = self.get_object()
        ActionService.delete_action(instance, updated_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="dry_run")
    def dry_run(self, request, pk=None):  # pylint: disable=unused-argument
        """Validate an action's parameters without executing it."""
        action_obj = self.get_object()
        event_payload = request.data.get("event_payload")
        if event_payload is None or not isinstance(event_payload, dict):
            return Response(
                {"detail": "'event_payload' is required and must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = ActionService.dry_run(action_obj, event_payload=event_payload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
