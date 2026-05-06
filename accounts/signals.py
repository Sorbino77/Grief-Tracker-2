"""Seed canonical Admin/Editor/Viewer Groups on migrate."""

from __future__ import annotations

from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

GROUPS = ("Admin", "Editor", "Viewer")


@receiver(post_migrate)
def ensure_role_groups(sender, **kwargs):  # pragma: no cover
    if sender.name != "accounts":
        return
    for name in GROUPS:
        Group.objects.get_or_create(name=name)
