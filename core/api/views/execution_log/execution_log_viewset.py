"""Read-only API ViewSet for ExecutionLog model."""

from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response

from core.api.serializers.execution_log import ExecutionLogSerializer
from core.models import ExecutionLog
from core.permissions import CanViewExecutionLogs
from core.services.domain.execution_log_service import ExecutionLogService

from .pagination import ExecutionLogPagination


class ExecutionLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only endpoints for workflow execution history."""

    serializer_class = ExecutionLogSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [CanViewExecutionLogs]
    pagination_class = ExecutionLogPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["workflow", "event", "status"]
    search_fields = ["workflow__name"]
    ordering_fields = ["started_at", "finished_at", "created_at"]
    ordering = ["-started_at"]

    def get_queryset(self):
        """Delegate execution-log list retrieval to the domain service."""
        return ExecutionLogService.list_execution_logs(filters=self.request.query_params)

    def retrieve(self, request, *args, **kwargs):
        """Delegate single execution-log retrieval to the domain service."""
        try:
            execution_log = ExecutionLogService.get_execution_log(kwargs["pk"])
        except ExecutionLog.DoesNotExist as exc:
            raise Http404("Execution log not found.") from exc
        self.check_object_permissions(request, execution_log)
        serializer = self.get_serializer(execution_log)
        return Response(serializer.data, status=status.HTTP_200_OK)