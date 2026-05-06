"""Role-based permission helpers usable from views & DRF.

Centralising these means a future change (e.g. splitting Editor into
Editor + Importer) only touches this file.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework import permissions

from .models import Role


def role_required(*roles: str):
    """Decorator: deny if request.user.role is not in ``roles``.

    Always wraps in ``login_required`` first so anonymous users get the
    standard 302-to-login behaviour rather than a 403.
    """
    allowed = set(roles)

    def decorator(view):
        @wraps(view)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or getattr(user, "role", None) in allowed:
                return view(request, *args, **kwargs)
            raise PermissionDenied("You don't have permission to perform this action.")

        return _wrapped

    return decorator


# DRF permissions
class IsViewer(permissions.IsAuthenticated):
    """Anyone authenticated counts as a viewer."""


class IsEditor(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or u.role in {Role.ADMIN, Role.EDITOR}))


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or u.role == Role.ADMIN))


class ReadOnlyOrEditor(permissions.BasePermission):
    """Safe methods for any authenticated user; writes for editors+."""

    def has_permission(self, request, view) -> bool:
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return u.is_superuser or u.role in {Role.ADMIN, Role.EDITOR}
