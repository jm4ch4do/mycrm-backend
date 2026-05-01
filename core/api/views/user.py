"""API views for user-related endpoints."""

from rest_framework import mixins, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.serializers.user import CurrentUserSerializer, UserSerializer
from core.permissions import IsStaffOrReadOnly
from core.services.domain.user_service import UserService


class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CurrentUserView(APIView):
    """Get information about the currently authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get(self, request):
        """Return current user information."""
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API ViewSet for User model.

    Endpoints:
    GET    /users/      → List all users with their CRM roles
    GET    /users/{id}/ → Retrieve a specific user with their role
    PUT    /users/{id}/ → Update role only (staff/admin only)
    """

    serializer_class = UserSerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class = UserPagination
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        """Delegate queryset retrieval to service."""
        return UserService.list_users()

    def get_object(self):
        """Delegate object retrieval to service."""
        obj = UserService.get_user(self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, *args, **kwargs):
        """Role-only update — bypass standard serializer write flow."""
        instance = self.get_object()
        role = request.data.get("role")
        UserService.update_user_role(instance, role)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
