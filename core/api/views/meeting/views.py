from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.api.serializers.meeting import (
    MeetingCompleteSerializer,
    MeetingContactAssocSerializer,
    MeetingSerializer,
    MeetingUserAssocSerializer,
)
from core.models import Meeting
from core.permissions import IsMeetingOwnerOrAdmin
from core.services.domain.meeting_service import MeetingService

from .pagination import MeetingPagination


class MeetingViewSet(viewsets.ModelViewSet):  # pylint: disable=too-many-ancestors
    """API ViewSet for Meeting model.

    Endpoints:
    POST   /meetings/                             → Create a new meeting
    GET    /meetings/                             → List meetings (filter/paginate/sort)
    GET    /meetings/{id}/                        → Retrieve a specific meeting
    PUT    /meetings/{id}/                        → Full update a meeting
    PATCH  /meetings/{id}/                        → Partial update a meeting
    DELETE /meetings/{id}/                        → Soft delete a meeting
    POST   /meetings/{id}/complete/               → Mark meeting as complete
    POST   /meetings/{id}/users/                  → Add user participant
    DELETE /meetings/{id}/users/{user_id}/        → Remove user participant
    POST   /meetings/{id}/contacts/               → Add contact participant
    DELETE /meetings/{id}/contacts/{contact_id}/  → Remove contact participant
    """

    queryset = Meeting.objects.select_related("activity").all()
    serializer_class = MeetingSerializer
    permission_classes = [IsMeetingOwnerOrAdmin]
    pagination_class = MeetingPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "outcome",
        "activity__account",
        "activity__contact",
        "activity__deal",
        "activity__owner_user",
    ]
    search_fields = ["activity__title", "activity__description", "location"]
    ordering_fields = [
        "start_time",
        "end_time",
        "activity__created_at",
        "activity__updated_at",
    ]
    ordering = ["-start_time"]

    # ===== Custom actions =====

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):  # pylint: disable=unused-argument
        """Mark a meeting as completed with an outcome."""
        meeting = self.get_object()
        serializer = MeetingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = MeetingService.complete_meeting(
            meeting,
            serializer.validated_data["outcome"],
            serializer.validated_data.get("summary"),
            request.user,
        )
        return Response(MeetingSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="users")
    def add_user(self, request, pk=None):  # pylint: disable=unused-argument
        """Add a user participant to this meeting."""
        meeting = self.get_object()
        serializer = MeetingUserAssocSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        assoc = MeetingService.add_user_participant(meeting, user)
        return Response(
            MeetingUserAssocSerializer(assoc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"users/(?P<user_id>[^/.]+)",
    )
    def remove_user(
        self, request, pk=None, user_id=None
    ):  # pylint: disable=unused-argument
        """Remove a user participant from this meeting."""
        meeting = self.get_object()
        MeetingService.remove_user_participant(meeting, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="contacts")
    def add_contact(self, request, pk=None):  # pylint: disable=unused-argument
        """Add a contact participant to this meeting."""
        meeting = self.get_object()
        serializer = MeetingContactAssocSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data["contact"]
        assoc = MeetingService.add_contact_participant(meeting, contact)
        return Response(
            MeetingContactAssocSerializer(assoc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"contacts/(?P<contact_id>[^/.]+)",
    )
    def remove_contact(
        self, request, pk=None, contact_id=None
    ):  # pylint: disable=unused-argument
        """Remove a contact participant from this meeting."""
        meeting = self.get_object()
        MeetingService.remove_contact_participant(meeting, contact_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Endpoint overrides =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete a meeting."""
        instance = self.get_object()
        MeetingService.soft_delete_meeting(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query methods =====

    def get_queryset(self):
        """Return only active (non-soft-deleted) meetings."""
        return MeetingService.list_meetings().select_related("activity")

    def get_object(self):
        """Retrieve meeting and enforce object-level permissions."""
        obj = MeetingService.get_meeting(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj


# Docstrings for auto-generated schema
MeetingViewSet.list.__doc__ = (
    "List all active meetings with filtering, searching, and pagination."
)
MeetingViewSet.create.__doc__ = "Create a new meeting."
MeetingViewSet.retrieve.__doc__ = "Retrieve a specific meeting."
MeetingViewSet.update.__doc__ = "Update a meeting (full update)."
MeetingViewSet.partial_update.__doc__ = "Partial update a meeting."
