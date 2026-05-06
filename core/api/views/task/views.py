from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.serializers.task import TaskSerializer
from core.models import Task
from core.permissions import IsTaskOwnerOrAdmin
from core.services.domain.task_service import TaskService

from .pagination import TaskPagination  # pylint: disable=relative-beyond-top-level


class TaskViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Task model.

    Endpoints:
    POST   /tasks/              → Create a new task
    GET    /tasks/              → List tasks (filter/paginate/sort)
    GET    /tasks/{id}/         → Retrieve a specific task
    PUT    /tasks/{id}/         → Full update a task
    PATCH  /tasks/{id}/         → Partial update a task
    DELETE /tasks/{id}/         → Soft delete a task
    POST   /tasks/{id}/complete/ → Mark task as completed
    """

    queryset = Task.objects.select_related("activity").all()
    serializer_class = TaskSerializer
    permission_classes = [IsTaskOwnerOrAdmin]
    pagination_class = TaskPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "state",
        "priority",
        "category",
        "activity__account",
        "activity__contact",
        "activity__deal",
        "activity__owner_user",
    ]
    search_fields = ["activity__title", "activity__description"]
    ordering_fields = [
        "activity__created_at",
        "activity__updated_at",
        "activity__due_at",
    ]
    ordering = ["-activity__created_at"]

    # ===== Custom actions =====

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):  # pylint: disable=unused-argument
        """Mark a task as completed."""
        task = self.get_object()
        updated = TaskService.complete_task(task, request.user)
        return Response(TaskSerializer(updated, context={"request": request}).data)

    # ===== Endpoint overrides =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a task."""
        instance = self.get_object()
        TaskService.soft_delete_task(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query methods =====

    def get_queryset(self):
        """Return only active (non-soft-deleted) tasks."""
        return TaskService.list_tasks().select_related("activity")

    def get_object(self):
        """Retrieve task and enforce object-level permissions."""
        obj = TaskService.get_task(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


# Docstrings for auto-generated schema
TaskViewSet.list.__doc__ = (
    "List all active tasks with filtering, searching, and pagination."
)
TaskViewSet.create.__doc__ = "Create a new task."
TaskViewSet.retrieve.__doc__ = "Retrieve a specific task."
TaskViewSet.update.__doc__ = "Update a task (full update)."
TaskViewSet.partial_update.__doc__ = "Partial update a task."
