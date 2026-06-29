from rest_framework import permissions


class IsWarehouseAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class IsWarehouseManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'MANAGER'])


class IsWarehouseStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'MANAGER', 'STAFF'])


class ReadOnlyOrAuthenticated(permissions.BasePermission):
    """
    Allow unauthenticated read-only access (GET, HEAD, OPTIONS).
    Write operations (POST, PUT, PATCH, DELETE) require a valid authenticated user.
    Used for warehouse structure endpoints so the frontend/Digital Twin can read
    real warehouse data without a JWT token in the demo/development flow.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

