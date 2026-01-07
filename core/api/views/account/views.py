from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from core.api.serializers import AccountSerializer
from core.models import Account
from core.services.domain.account_service import AccountService

from .pagination import AccountPagination
from .schemas import (
    CREATE_ACCOUNT_EXAMPLES,
    UPDATE_ACCOUNT_EXAMPLES
)


class AccountViewSet(viewsets.ModelViewSet):
    """API ViewSet for Account model."""

    # Endpoints:
    # POST   /accounts      → Create a new account
    # GET    /accounts      → List accounts (with filtering/pagination/sorting)
    # GET    /accounts/{id} → Retrieve a specific account
    # PUT    /accounts/{id} → Update an account
    # DELETE /accounts/{id} → Soft delete an account

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = AccountPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = [
        'status', 'type', 'company_size', 'owner_user'
    ]
    search_fields = [
        'name', 'industry', 'account_number'
    ]
    ordering_fields = [
        'name', 'created_at', 'updated_at', 'annual_revenue'
    ]
    ordering = ['-created_at']
    allowed_actions = [
        'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'
    ]

    # ===== Endpoint Definitions =====

    def destroy(self, request, *args, **kwargs):
        """Soft delete an account."""
        instance = self.get_object()
        AccountService.soft_delete_account(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ===== Query Methods =====

    def get_queryset(self):
        """Delegate queryset retrieval to service."""
        return AccountService.list_accounts()

    def get_object(self):
        """Delegate object retrieval to service."""
        return AccountService.get_account(self.kwargs['pk'])

    # ===== Persistence Methods =====

    def perform_create(self, serializer):
        """Delegate account creation to service."""
        AccountService.create_account(
            serializer.validated_data, self.request.user
        )

    def perform_update(self, serializer):
        """Delegate account update to service."""
        AccountService.update_account(
            serializer.instance,
            serializer.validated_data,
            self.request.user
        )




# Set docstrings for all action methods
AccountViewSet.list.__doc__ = "List all accounts with filtering, searching, and pagination."
AccountViewSet.create.__doc__ = "Create a new account."
AccountViewSet.retrieve.__doc__ = "Retrieve a specific account."
AccountViewSet.update.__doc__ = "Update an account (full update)."
AccountViewSet.partial_update.__doc__ = "Partial update an account."

# Apply decorators for methods with examples
AccountViewSet.create = extend_schema(examples=CREATE_ACCOUNT_EXAMPLES)(AccountViewSet.create)
AccountViewSet.update = extend_schema(examples=UPDATE_ACCOUNT_EXAMPLES)(AccountViewSet.update)
