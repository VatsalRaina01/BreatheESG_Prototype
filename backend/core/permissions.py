from rest_framework.permissions import BasePermission


class TenantAccessPermission(BasePermission):
    """Ensures the user belongs to a tenant."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'tenant', None) is not None
        )
