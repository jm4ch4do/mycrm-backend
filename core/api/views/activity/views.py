from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from core.api.serializers.activity import ActivitySerializer
from core.models import Activity
from core.permissions import IsActivityOwnerOrAdmin
from core.services.domain.activity_service import ActivityService

from .pagination import ActivityPagination
from .schemas import CREATE_ACTIVITY_EXAMPLES, UPDATE_ACTIVITY_EXAMPLES


class ActivityViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Activity model."""

    # Endpoints:
    # POST   /activities/       → Create a new activity
    # GET    /activities/       → List activities (with filtering/pagination/sorting)
    # GET    /activities/{id}/  → Retrieve a specific activity
    # PUT    /activities/{id}/  → Update an activity
    # PATCH  /activities/{id}/  → Partial update an activity
    # DELETE /activities/{id}/  → Soft delete an activity

    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsActivityOwnerOrAdmin]
    pagination_class = ActivityPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["type", "status", "account", "contact", "deal", "owner_user"]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at", "updated_at", "due_at"]
    ordering = ["-created_at"]

    # ===== Endpoint Definitions =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete an activity."""
        instance = self.get_object()
        ActivityService.soft_delete_activity(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query Methods =====

    def get_queryset(self):
        """Delegate queryset retrieval to service."""
        return ActivityService.list_activities()

    def get_object(self):
        """Delegate object retrieval to service."""
        obj = ActivityService.get_activity(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    # ===== Persistence Methods =====

    def perform_create(self, serializer):
        """Delegate activity creation to service."""
        ActivityService.create_activity(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        """Delegate activity update to service."""
        ActivityService.update_activity(
            serializer.instance, serializer.validated_data, self.request.user
        )


# Set docstrings for all action methods
ActivityViewSet.list.__doc__ = (
    "List all activities with filtering, searching, and pagination."
)
ActivityViewSet.create.__doc__ = "Create a new activity."
ActivityViewSet.retrieve.__doc__ = "Retrieve a specific activity."
ActivityViewSet.update.__doc__ = "Update an activity (full update)."
ActivityViewSet.partial_update.__doc__ = "Partial update an activity."

# Apply decorators for methods with examples
ActivityViewSet.create = extend_schema(examples=CREATE_ACTIVITY_EXAMPLES)(
    ActivityViewSet.create
)
ActivityViewSet.update = extend_schema(examples=UPDATE_ACTIVITY_EXAMPLES)(
    ActivityViewSet.update
)
