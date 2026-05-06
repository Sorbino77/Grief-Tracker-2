"""Bootstrap a fresh installation: groups + a default admin (env-controlled).

Usage in Docker entrypoint:
    python manage.py migrate
    python manage.py seed_demo

Reads ``DJANGO_SUPERUSER_USERNAME``, ``DJANGO_SUPERUSER_PASSWORD``,
``DJANGO_SUPERUSER_EMAIL`` from env. Skips silently if any are missing — never
hardcodes credentials, in line with OWASP A05.
"""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed reference groups and (optionally) a superuser from env vars."

    def handle(self, *args, **opts):
        for name in ("Admin", "Editor", "Viewer"):
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Groups OK"))

        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        if username and password and email:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "role": "admin", "is_staff": True, "is_superuser": True},
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
            else:
                self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists; not modified."))
        else:
            self.stdout.write(
                "Skipping superuser creation (set DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD to enable)."
            )
