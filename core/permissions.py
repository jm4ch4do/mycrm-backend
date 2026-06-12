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
        - All authenticated users (for safe methods)
        - Owners and admins (for modifications)
        """
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Safe methods (GET, HEAD, OPTIONS) - allow all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

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
        - All authenticated users (for safe methods)
        - Owners and admins (for modifications)
        """
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Safe methods (GET, HEAD, OPTIONS) - allow all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Modification methods (PUT, PATCH, DELETE) - allow owner only
        return obj.owner_user == request.user


class IsDealOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow deal owners or admins to modify deals.

    - Admins can always modify
    - Only deal owners can update/delete their own deals
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
        - All authenticated users (for safe methods)
        - Owners and admins (for modifications)
        """
        # Admins always have permission
        if request.user and request.user.is_staff:
            return True

        # Safe methods (GET, HEAD, OPTIONS) - allow all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Modification methods (PUT, PATCH, DELETE) - allow owner only
        return obj.owner_user == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allow any authenticated user to read.
    Only staff/admin can perform write operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class IsActivityOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow activity owners or admins to modify activities.

    - Admins can always modify
    - Only activity owners can update/delete their own activities
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_user == request.user


class IsTaskOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow task owners or admins to modify tasks.

    - Admins can always modify
    - Only the owner (via task.activity.owner_user) can update/delete their tasks
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.activity.owner_user == request.user


class IsMeetingOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow meeting owners or admins to modify meetings.

    - Admins can always modify
    - Only the owner (via meeting.activity.owner_user) can update/delete their meetings
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.activity.owner_user == request.user


class IsCallOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow call owners or admins to modify calls.

    - Admins can always modify
    - Only the owner (via call.activity.owner_user) can update/delete their calls
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.activity.owner_user == request.user


class IsNoteAuthorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow note authors or admins to modify notes.

    - Admins can always modify
    - Only the author can update/delete their notes
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class CanViewTimeline(permissions.BasePermission):
    """
    Permission for read-only timeline endpoints.

    - Authenticated users may request timelines for any entity they can view.
    - Timeline endpoints are read-only (GET, HEAD, OPTIONS).
    - Note visibility filtering is handled by the service layer based on authorship.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """
        Allow all authenticated users to view timelines (read-only).
        Staff users always have permission.
        """
        if request.user and request.user.is_staff:
            return True
        # All authenticated users can view timelines
        # Note visibility is filtered by the service layer
        return True


class CanViewEvents(permissions.BasePermission):
    """Permission for read-only event endpoints.

    - list: admin/staff users only (full event log)
    - retrieve: any authenticated user
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        action = getattr(view, "action", None)
        if action == "list":
            return bool(request.user.is_staff)

        if action == "retrieve":
            return True

        # For unsupported methods (create/update/delete), allow the request to
        # reach the viewset so DRF can return 405 Method Not Allowed.
        return True

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated)


class CanViewExecutionLogs(permissions.BasePermission):
    """Permission for read-only execution-log endpoints.

    - list/retrieve: admin/staff users only
    - unsupported write methods: allowed to reach the viewset so DRF returns 405
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        action = getattr(view, "action", None)
        if action in {"list", "retrieve"}:
            return bool(request.user.is_staff)

        return True

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_staff)


class CanManageTriggers(permissions.BasePermission):
    """Permission rules for trigger management endpoints.

    - list/retrieve: any authenticated user
    - create/update/delete/custom write actions: staff/admin only
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.is_staff)
