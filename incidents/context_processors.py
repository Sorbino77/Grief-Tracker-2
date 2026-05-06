"""Expose role booleans to all templates so the nav can hide/show buttons."""

from accounts.models import Role


def user_role(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"is_admin": False, "is_editor": False, "user_role": None}
    return {
        "is_admin": user.is_admin,
        "is_editor": user.is_editor,
        "user_role": getattr(user, "role", Role.VIEWER),
    }
