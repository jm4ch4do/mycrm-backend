"""API views for user-related endpoints."""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CurrentUserView(views.APIView):
    """Get information about the currently authenticated user."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return current user information."""
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_authenticated': user.is_authenticated,
        }, status=status.HTTP_200_OK)
