from rest_framework import permissions

class IsAdminSelf(permissions.BasePermission):
    """Разрешение для пользователей с правами администратора, модератора
    или автора.
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            obj.id == request.user.id
            or request.user.is_staff  
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение для пользователей с правами администратора.
    """

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff