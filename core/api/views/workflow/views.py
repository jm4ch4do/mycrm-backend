from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.api.serializers.workflow import WorkflowSerializer
from core.models import Workflow
from core.services.domain.workflow_service import WorkflowService

from .pagination import WorkflowPagination


class WorkflowViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Workflow model."""

    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAdminUser]
    pagination_class = WorkflowPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["trigger", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Delegate workflow list retrieval to the domain service."""
        return WorkflowService.list_workflows()

    def get_object(self):
        """Delegate single-workflow retrieval to the domain service."""
        obj = WorkflowService.get_workflow(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def destroy(self, request, *args, **kwargs):
        """Soft delete a workflow."""
        instance = self.get_object()
        WorkflowService.delete_workflow(instance, updated_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):  # pylint: disable=unused-argument
        """Activate a workflow."""
        workflow = self.get_object()
        updated = WorkflowService.update_workflow(
            workflow,
            {"is_active": True},
            updated_by=request.user,
        )
        return Response(WorkflowSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):  # pylint: disable=unused-argument
        """Deactivate a workflow."""
        workflow = self.get_object()
        updated = WorkflowService.update_workflow(
            workflow,
            {"is_active": False},
            updated_by=request.user,
        )
        return Response(WorkflowSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="steps")
    def add_step(self, request, pk=None):  # pylint: disable=unused-argument
        """Add a workflow step at the requested order."""
        workflow = self.get_object()
        action_id = request.data.get("action_id")
        step_order = request.data.get("step_order")

        if action_id is None or step_order is None:
            return Response(
                {"detail": "'action_id' and 'step_order' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            step = WorkflowService.add_step(
                workflow=workflow,
                action_id=action_id,
                step_order=int(step_order),
                updated_by=request.user,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": str(step.id),
                "action": {
                    "id": str(step.action.id),
                    "name": step.action.name,
                },
                "step_order": step.step_order,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path=r"steps/(?P<step_order>[0-9]+)")
    def remove_step(self, request, pk=None, step_order=None):  # pylint: disable=unused-argument
        """Remove workflow step by step_order."""
        workflow = self.get_object()
        WorkflowService.remove_step(
            workflow=workflow,
            step_order=int(step_order),
            updated_by=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
