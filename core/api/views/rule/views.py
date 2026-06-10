from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.api.serializers.rule import RuleSerializer
from core.models import Event, Rule
from core.services.domain.rule_service import RuleEvaluationError, RuleService

from .pagination import RulePagination


class RuleViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Rule model."""

    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [IsAdminUser]
    pagination_class = RulePagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["trigger", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["evaluation_order", "created_at"]
    ordering = ["evaluation_order", "created_at"]

    def get_queryset(self):
        """Delegate rule list retrieval to the domain service."""
        return RuleService.list_rules()

    def get_object(self):
        """Delegate single-rule retrieval to the domain service."""
        obj = RuleService.get_rule(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        """Delegate rule creation to the domain service."""
        rule = RuleService.create_rule(serializer.validated_data, created_by=self.request.user)
        serializer.instance = rule

    def perform_update(self, serializer):
        """Delegate rule update to the domain service."""
        RuleService.update_rule(
            serializer.instance,
            serializer.validated_data,
            updated_by=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        """Soft delete a rule."""
        instance = self.get_object()
        RuleService.delete_rule(instance, updated_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate(self, request, pk=None):  # pylint: disable=unused-argument
        """Evaluate this rule's condition tree against a sample event payload."""
        event_payload = request.data.get("event_payload")
        if event_payload is None or not isinstance(event_payload, dict):
            return Response(
                {"detail": "'event_payload' is required and must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rule = self.get_object()

        # Build a lightweight in-memory Event for dry-run evaluation.
        mock_event = Event(after_state=event_payload)

        try:
            result = RuleService.evaluate_rule(rule, mock_event)
        except RuleEvaluationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"result": result}, status=status.HTTP_200_OK)
