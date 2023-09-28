"""Пермишны для API."""
from rest_framework import permissions


class IsAdminSelfOrReadOnly(permissions.BasePermission):
    """Администратор или автор.

    Разрешение для пользователей с правами администратора
    или автора.
    """

    def has_permission(self, request, view):
        """Разрешение на уровне выборки."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Разрешение на уровне объекта."""
        return (
            obj.id == request.user.id
            or request.user.is_staff
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение для пользователей с правами администратора."""

    def has_permission(self, request, view):
        """Разрешение на уровне выборки."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        """Разрешение на уровне объекта."""
        return request.user.is_staff
