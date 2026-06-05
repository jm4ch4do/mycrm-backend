from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.serializers.call import CallCompleteSerializer, CallSerializer
from core.models import Call
from core.permissions import IsCallOwnerOrAdmin
from core.services.domain.call_service import CallService

from .pagination import CallPagination  # pylint: disable=relative-beyond-top-level


class CallViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Call model.

    Endpoints:
    POST   /calls/                   → Create a new call
    GET    /calls/                   → List calls (filter/paginate/sort)
    GET    /calls/{id}/              → Retrieve a specific call
    PUT    /calls/{id}/              → Full update a call
    PATCH  /calls/{id}/              → Partial update a call
    DELETE /calls/{id}/              → Soft delete a call
    POST   /calls/{id}/complete_call/ → Mark call as complete
    """

    queryset = Call.objects.select_related("activity").all()
    serializer_class = CallSerializer
    permission_classes = [IsCallOwnerOrAdmin]
    pagination_class = CallPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "direction",
        "outcome",
        "activity__account",
        "activity__deal",
        "activity__owner_user",
    ]
    search_fields = ["activity__title", "phone_number", "summary"]
    ordering_fields = [
        "activity__created_at",
        "activity__due_at",
    ]
    ordering = ["-activity__created_at"]

    # ===== Custom actions =====

    @action(detail=True, methods=["post"], url_path="complete_call")
    def complete_call(self, request, pk=None):  # pylint: disable=unused-argument
        """Mark a call as completed with an outcome."""
        call = self.get_object()
        serializer = CallCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = CallService.complete_call(
            call,
            serializer.validated_data["outcome"],
            serializer.validated_data.get("summary"),
            serializer.validated_data.get("duration_seconds"),
            request.user,
        )
        return Response(CallSerializer(updated, context={"request": request}).data)

    # ===== Endpoint overrides =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a call."""
        instance = self.get_object()
        CallService.soft_delete_call(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query methods =====

    def get_queryset(self):
        """Return only active (non-soft-deleted) calls."""
        return CallService.list_calls().select_related("activity")

    def get_object(self):
        """Retrieve call and enforce object-level permissions."""
        obj = CallService.get_call(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


# Docstrings for auto-generated schema
CallViewSet.list.__doc__ = (
    "List all active calls with filtering, searching, and pagination."
)
CallViewSet.create.__doc__ = "Create a new call."
CallViewSet.retrieve.__doc__ = "Retrieve a specific call."
CallViewSet.update.__doc__ = "Update a call (full update)."
CallViewSet.partial_update.__doc__ = "Partial update a call."
