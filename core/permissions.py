from rest_framework import permissions


class IsAccountOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow account owners or admins to modify accounts.

    - Admins can always modify
    - Only account owners can update/delete their own accounts
    """

    def has_permission(self, request, view):
        """
        Allow access to:
        - List and retrieve operations for all authenticated users
        - Create operations for all authenticated users
        - Update and delete only for owners/admins
        """
        # Allow GET, HEAD, OPTIONS for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Allow POST, PUT, PATCH, DELETE for authenticated users
        # (object-level permission will check ownership for modifications)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Allow object access only to:
        - Owners (for safe methods and modifications)
        - Admins (for any operation)
        """
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Safe methods (GET, HEAD, OPTIONS) - allow owner
        if request.method in permissions.SAFE_METHODS:
            return obj.owner_user == request.user

        # Modification methods (PUT, PATCH, DELETE) - allow owner only
        return obj.owner_user == request.user


class IsContactOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow contact owners or admins to modify contacts.

    - Admins can always modify
    - Only contact owners can update/delete their own contacts
    """

    def has_permission(self, request, view):
        """
        Allow access to:
        - List and retrieve operations for all authenticated users
        - Create operations for all authenticated users
        - Update and delete only for owners/admins
        """
        # Allow GET, HEAD, OPTIONS for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Allow POST, PUT, PATCH, DELETE for authenticated users
        # (object-level permission will check ownership for modifications)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Allow object access only to:
        - Owners (for safe methods and modifications)
        - Admins (for any operation)
        """
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Safe methods (GET, HEAD, OPTIONS) - allow owner
        if request.method in permissions.SAFE_METHODS:
            return obj.owner_user == request.user

        # Modification methods (PUT, PATCH, DELETE) - allow owner only
        return obj.owner_user == request.user
