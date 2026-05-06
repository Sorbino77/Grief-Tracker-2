"""Custom user model with role helpers.

We subclass AbstractUser rather than swap to AbstractBaseUser so we keep all the
hardened defaults (password hashing, permissions framework, admin integration)
while still being able to add fields later without a painful migration.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    EDITOR = "editor", "Editor"
    VIEWER = "viewer", "Viewer"


class User(AbstractUser):
    """Custom user. ``role`` is the authoritative role field; we ALSO mirror
    the role into a Django ``Group`` so the standard ``user.has_perm`` checks
    keep working.

    Email is required and unique to support OAuth sign-in flows where the
    upstream provider (Google/Microsoft) is the source of truth.
    """

    email = models.EmailField("email address", unique=True)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="Role determines what the user can do in the app.",
    )

    # Limit which fields the admin UI shows; mostly informational.
    class Meta:
        ordering = ["username"]

    # ----- role helpers (used by views & templates) -----
    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_editor(self) -> bool:
        return self.is_admin or self.role == Role.EDITOR

    @property
    def is_viewer(self) -> bool:
        # Every authenticated user is at least a viewer.
        return self.is_authenticated

    def __str__(self) -> str:  # pragma: no cover
        return self.username
