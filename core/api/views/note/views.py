from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from core.api.serializers.note import NoteSerializer
from core.models import Note
from core.permissions import IsNoteAuthorOrAdmin
from core.services.domain.note_service import NoteService

from .pagination import NotesPagination  # pylint: disable=relative-beyond-top-level


class NoteViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Note model.

    Endpoints:
    POST   /notes/           → Create a new note
    GET    /notes/           → List notes (filter/paginate/sort)
    GET    /notes/{id}/      → Retrieve a specific note
    PUT    /notes/{id}/      → Full update a note
    PATCH  /notes/{id}/      → Partial update a note
    DELETE /notes/{id}/      → Soft delete a note
    """

    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsNoteAuthorOrAdmin]
    pagination_class = NotesPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "visibility",
        "is_pinned",
        "author",
        "account",
        "contact",
        "deal",
    ]
    search_fields = ["title", "body"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "is_pinned",
    ]
    ordering = ["-created_at"]

    # ===== Endpoint overrides =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a note."""
        instance = self.get_object()
        NoteService.soft_delete_note(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query methods =====

    def get_queryset(self):
        """Return only active (non-soft-deleted) notes."""
        return NoteService.list_notes()

    def get_object(self):
        """Retrieve note and enforce object-level permissions."""
        obj = NoteService.get_note(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


# Docstrings for auto-generated schema
NoteViewSet.list.__doc__ = (
    "List all active notes with filtering, searching, and pagination."
)
NoteViewSet.create.__doc__ = "Create a new note."
NoteViewSet.retrieve.__doc__ = "Retrieve a specific note."
NoteViewSet.update.__doc__ = "Update a note (full update)."
NoteViewSet.partial_update.__doc__ = "Partial update a note."
