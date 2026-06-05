"""ViewSet for the read-only Timeline/Activity Feed API."""

from django.apps import apps
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.api.serializers.timeline import TimelineItemSerializer
from core.permissions import CanViewTimeline
from core.services.domain.timeline_service import TimelineService

from .pagination import TimelinePagination  # pylint: disable=relative-beyond-top-level

# Valid entity types: maps entity_type → (app_label, model_name, url_kwarg)
_ENTITY_CONFIG = {
    "account": ("core", "Account", "account_pk"),
    "contact": ("core", "Contact", "contact_pk"),
    "deal": ("core", "Deal", "deal_pk"),
}


class TimelineViewSet(viewsets.ViewSet):
    """Read-only timeline endpoint nested under Account, Contact, and Deal.

    Endpoints:
    GET /accounts/{account_pk}/timeline/  → Timeline for an Account
    GET /contacts/{contact_pk}/timeline/  → Timeline for a Contact
    GET /deals/{deal_pk}/timeline/        → Timeline for a Deal

    All other HTTP methods return 405 Method Not Allowed.
    """

    http_method_names = ["get", "head", "options"]
    permission_classes = [IsAuthenticated, CanViewTimeline]
    pagination_class = TimelinePagination

    def list(self, request, *args, **kwargs):
        """Return a paginated timeline for the parent entity."""
        entity_type, entity_id = self._resolve_entity(kwargs)

        # Fetch parent entity and run object-level permission check
        app_label, model_name, _ = _ENTITY_CONFIG[entity_type]
        model = apps.get_model(app_label, model_name)
        parent = get_object_or_404(model, pk=entity_id)
        self.check_object_permissions(request, parent)

        items = TimelineService.get_timeline(entity_type, entity_id, request.user)

        # Apply optional ?type= filter
        type_filter = request.query_params.get("type")
        if type_filter:
            items = [item for item in items if item["type"] == type_filter]

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request)
        if page is not None:
            serializer = TimelineItemSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = TimelineItemSerializer(items, many=True)
        return Response(serializer.data)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_entity(kwargs: dict) -> tuple[str, str]:
        """Extract entity_type and entity_id from URL kwargs."""
        for entity_type, (_, _, kwarg_name) in _ENTITY_CONFIG.items():
            entity_id = kwargs.get(kwarg_name)
            if entity_id is not None:
                return entity_type, str(entity_id)
        raise ValueError("No recognised entity PK found in URL kwargs.")
