"""API views for user-related endpoints."""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.api.serializers.user import CurrentUserSerializer


class CurrentUserView(views.APIView):
    """Get information about the currently authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get(self, request):
        """Return current user information."""
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
