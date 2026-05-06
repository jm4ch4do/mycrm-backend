from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.serializers.activity import ActivitySerializer
from core.api.serializers.deal import DealContactAssocSerializer, DealSerializer
from core.models import Deal
from core.permissions import IsDealOwnerOrAdmin
from core.services.domain.deal_service import DealService

from .pagination import DealPagination
from .schemas import CREATE_DEAL_EXAMPLES, UPDATE_DEAL_EXAMPLES


class DealViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Deal model."""

    # Endpoints:
    # POST   /deals          → Create a new deal
    # GET    /deals          → List deals (with filtering/pagination/sorting)
    # GET    /deals/{id}     → Retrieve a specific deal
    # PUT    /deals/{id}     → Update a deal
    # PATCH  /deals/{id}     → Partial update a deal
    # DELETE /deals/{id}     → Soft delete a deal
    # POST   /deals/{id}/contacts/              → Add contact to deal
    # DELETE /deals/{id}/contacts/{contact_id}/  → Remove contact from deal

    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsDealOwnerOrAdmin]
    pagination_class = DealPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["stage", "status", "account", "owner_user"]
    search_fields = ["name", "loss_reason"]
    ordering_fields = [
        "name",
        "created_at",
        "updated_at",
        "amount",
        "expected_close_date",
    ]
    ordering = ["-created_at"]

    # ===== Endpoint Definitions =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a deal."""
        instance = self.get_object()
        DealService.soft_delete_deal(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        """List all activities for this deal."""
        deal = self.get_object()
        qs = deal.activities.filter(is_invalid=False)
        serializer = ActivitySerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="contacts")
    def add_contact(self, request, pk=None):
        """Add a contact to this deal."""
        deal = self.get_object()
        serializer = DealContactAssocSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data["contact"]
        assoc = DealService.add_contact(deal, contact)
        return Response(
            DealContactAssocSerializer(assoc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"contacts/(?P<contact_id>[^/.]+)",
    )
    def remove_contact(self, request, pk=None, contact_id=None):
        """Remove a contact from this deal."""
        deal = self.get_object()
        DealService.remove_contact(deal, contact_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query Methods =====

    def get_queryset(self):
        """Delegate queryset retrieval to service."""
        return DealService.list_deals()

    def get_object(self):
        """Delegate object retrieval to service."""
        obj = DealService.get_deal(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    # ===== Persistence Methods =====

    def perform_create(self, serializer):
        """Delegate deal creation to service."""
        DealService.create_deal(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        """Delegate deal update to service."""
        DealService.update_deal(
            serializer.instance, serializer.validated_data, self.request.user
        )


# Set docstrings for all action methods
DealViewSet.list.__doc__ = "List all deals with filtering, searching, and pagination."
DealViewSet.create.__doc__ = "Create a new deal."
DealViewSet.retrieve.__doc__ = "Retrieve a specific deal."
DealViewSet.update.__doc__ = "Update a deal (full update)."
DealViewSet.partial_update.__doc__ = "Partial update a deal."

# Apply decorators for methods with examples
DealViewSet.create = extend_schema(examples=CREATE_DEAL_EXAMPLES)(DealViewSet.create)
DealViewSet.update = extend_schema(examples=UPDATE_DEAL_EXAMPLES)(DealViewSet.update)
DealViewSet.partial_update = extend_schema(examples=UPDATE_DEAL_EXAMPLES)(
    DealViewSet.partial_update
)
