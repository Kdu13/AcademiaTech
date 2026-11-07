from rest_framework.permissions import SAFE_METHODS, BasePermission

from login.permissions import is_admin_user


class ReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin_user(request.user)
