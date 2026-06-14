"""Seed canonical Admin/Editor/Viewer Groups on migrate, auto-create accessibility prefs."""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import AccessibilityPreferences, User

GROUPS = ("Admin", "Editor", "Viewer")


@receiver(post_migrate)
def ensure_role_groups(sender, **kwargs):  # pragma: no cover
    if sender.name != "accounts":
        return
    for name in GROUPS:
        Group.objects.get_or_create(name=name)


@receiver(post_save, sender=User)
def create_accessibility_preferences(sender, instance, created, **kwargs):
    """Auto-create accessibility preferences for new users."""
    if created:
        AccessibilityPreferences.objects.get_or_create(user=instance)
