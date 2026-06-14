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


class AccessibilityPreferences(models.Model):
    """Gaming-style accessibility settings for users.

    Includes options for visual, motor, cognitive, and audio accessibility.
    All settings are optional and default to standard experience.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="accessibility_prefs")

    # Visual accessibility
    high_contrast_mode = models.BooleanField(
        default=False, help_text="Increase color contrast for better visibility"
    )
    dyslexia_friendly_font = models.BooleanField(
        default=False, help_text="Use dyslexia-friendly font (OpenDyslexic)"
    )
    font_size = models.CharField(
        max_length=10,
        choices=[
            ("normal", "Normal (100%)"),
            ("large", "Large (125%)"),
            ("xlarge", "Extra Large (150%)"),
            ("xxlarge", "Huge (175%)"),
        ],
        default="normal",
        help_text="Base font size scaling",
    )
    colorblind_mode = models.CharField(
        max_length=20,
        choices=[
            ("none", "None (Standard)"),
            ("protanopia", "Red-Blind (Protanopia)"),
            ("deuteranopia", "Green-Blind (Deuteranopia)"),
            ("tritanopia", "Blue-Yellow Blind (Tritanopia)"),
            ("achromatopsia", "Complete Color Blind (Achromatopsia)"),
        ],
        default="none",
        help_text="Color vision deficiency mode",
    )

    # Motor accessibility
    reduced_motion = models.BooleanField(
        default=False, help_text="Reduce or disable animations and transitions"
    )
    large_touch_targets = models.BooleanField(
        default=False, help_text="Increase button and interactive element sizes"
    )
    keyboard_navigation_hints = models.BooleanField(
        default=False, help_text="Show keyboard navigation shortcuts and focus indicators"
    )

    # Cognitive accessibility
    simplified_layout = models.BooleanField(
        default=False, help_text="Hide advanced features, focus on essential content"
    )
    reading_guide = models.BooleanField(default=False, help_text="Highlight current line with reading guide")

    # Audio/Content
    captions = models.BooleanField(default=False, help_text="Show captions for audio content")
    screen_reader_mode = models.BooleanField(
        default=False, help_text="Optimize for screen reader compatibility"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Accessibility Preferences"
        verbose_name_plural = "Accessibility Preferences"

    def __str__(self) -> str:  # pragma: no cover
        return f"Accessibility settings for {self.user.username}"
