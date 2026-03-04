from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from core.api.serializers import ContactSerializer
from core.models import Contact
from core.permissions import IsContactOwnerOrAdmin
from core.services.domain.contact_service import ContactService

from .pagination import ContactPagination
from .schemas import CREATE_CONTACT_EXAMPLES, UPDATE_CONTACT_EXAMPLES


class ContactViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Contact model."""

    # Endpoints:
    # POST   /contacts      → Create a new contact
    # GET    /contacts      → List contacts (with filtering/pagination/sorting)
    # GET    /contacts/{id} → Retrieve a specific contact
    # PUT    /contacts/{id} → Update a contact
    # DELETE /contacts/{id} → Soft delete a contact

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsContactOwnerOrAdmin]
    pagination_class = ContactPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["account", "role", "seniority", "owner_user"]
    search_fields = ["first_name", "last_name", "email", "job_title"]
    ordering_fields = ["first_name", "last_name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    allowed_actions = [
        "list",
        "retrieve",
        "create",
        "update",
        "partial_update",
        "destroy",
    ]

    # ===== Endpoint Definitions =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a contact."""
        instance = self.get_object()
        ContactService.soft_delete_contact(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query Methods =====

    def get_queryset(self):
        """Delegate queryset retrieval to service."""
        return ContactService.list_contacts()

    def get_object(self):
        """Delegate object retrieval to service."""
        return ContactService.get_contact(self.kwargs["pk"])

    # ===== Persistence Methods =====

    def perform_create(self, serializer):
        """Delegate contact creation to service."""
        ContactService.create_contact(serializer.validated_data, self.request.user)

    def perform_update(self, serializer):
        """Delegate contact update to service."""
        ContactService.update_contact(
            serializer.instance, serializer.validated_data, self.request.user
        )


# Set docstrings for all action methods
ContactViewSet.list.__doc__ = (
    "List all contacts with filtering, searching, and pagination."
)
ContactViewSet.create.__doc__ = "Create a new contact."
ContactViewSet.retrieve.__doc__ = "Retrieve a specific contact."
ContactViewSet.update.__doc__ = "Update a contact (full update)."
ContactViewSet.partial_update.__doc__ = "Partial update a contact."

# Apply decorators for methods with examples
ContactViewSet.create = extend_schema(examples=CREATE_CONTACT_EXAMPLES)(
    ContactViewSet.create
)
ContactViewSet.update = extend_schema(examples=UPDATE_CONTACT_EXAMPLES)(
    ContactViewSet.update
)
