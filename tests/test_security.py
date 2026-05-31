"""OWASP-flavoured security tests."""

import pytest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse

pytestmark = [pytest.mark.django_db, pytest.mark.security]


def test_security_headers_present(client, viewer_user):
    client.force_login(viewer_user)
    resp = client.get(reverse("incidents:list"))
    assert resp["X-Frame-Options"].upper() == "DENY"
    assert resp["X-Content-Type-Options"].lower() == "nosniff"
    assert "same-origin" in resp.get("Referrer-Policy", "").lower()
    csp = resp.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_admin_csrf_required(client, admin_user, sample_record):
    """Even admins can't make a state-changing request without a CSRF token."""
    csrf_client = type(client)(enforce_csrf_checks=True)
    csrf_client.force_login(admin_user)
    resp = csrf_client.post(
        reverse("incidents:delete", kwargs={"pk": sample_record.pk}),
    )
    assert resp.status_code == 403


def test_password_too_short_rejected(user_model, db):
    with pytest.raises(ValidationError):
        validate_password("short1A!")


def test_axes_failure_limit_reasonable(settings):
    assert settings.AXES_FAILURE_LIMIT <= 10


def test_session_cookie_httponly(settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True


def test_argon2_is_default_hasher(settings):
    assert settings.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")


# ---------- self-demotion guard ----------


@pytest.mark.parametrize("target_role", ["editor", "viewer"])
def test_admin_cannot_demote_self_via_change_role_view(client, admin_user, target_role):
    """Posting to change_role with self.pk and a lower role must be rejected."""
    client.force_login(admin_user)
    resp = client.post(
        reverse("accounts:change_role", kwargs={"pk": admin_user.pk}),
        data={"role": target_role},
        follow=True,
    )
    admin_user.refresh_from_db()
    assert admin_user.role == "admin", "admin role must be preserved"
    # Error message bubbles up via Django messages framework.
    assert any("your own role" in m.message.lower() for m in resp.context["messages"]), (
        "expected a friendly error message about not changing your own role"
    )


def test_admin_can_still_change_other_users(client, admin_user, editor_user):
    """The guard must only apply to self — other users are still editable."""
    client.force_login(admin_user)
    resp = client.post(
        reverse("accounts:change_role", kwargs={"pk": editor_user.pk}),
        data={"role": "viewer"},
    )
    assert resp.status_code == 302
    editor_user.refresh_from_db()
    assert editor_user.role == "viewer"


def test_admin_can_keep_own_role_admin(client, admin_user):
    """Posting role=admin for self is a no-op — must NOT trigger the error."""
    client.force_login(admin_user)
    resp = client.post(
        reverse("accounts:change_role", kwargs={"pk": admin_user.pk}),
        data={"role": "admin"},
        follow=True,
    )
    admin_user.refresh_from_db()
    assert admin_user.role == "admin"
    msgs = [m.message.lower() for m in resp.context["messages"]]
    assert not any("your own role" in m for m in msgs)


def test_django_admin_save_model_blocks_self_demote(admin_user):
    """The Django admin save path must also reject self-demotion."""
    from django.contrib.admin.sites import AdminSite
    from django.test import RequestFactory

    from accounts.admin import CustomUserAdmin
    from accounts.models import User

    site = AdminSite()
    model_admin = CustomUserAdmin(User, site)
    rf = RequestFactory()
    request = rf.post(f"/admin/accounts/user/{admin_user.pk}/change/")

    # Real Django loads request.user separately from the form's `obj`, so
    # mutating one must not mutate the other. Use distinct instances.
    request.user = User.objects.get(pk=admin_user.pk)
    request._messages = _DummyMessages()

    tampered = User.objects.get(pk=admin_user.pk)
    tampered.role = "viewer"  # simulate the admin form posting a demotion
    model_admin.save_model(request, tampered, form=None, change=True)

    admin_user.refresh_from_db()
    assert admin_user.role == "admin", "Django admin must NOT have persisted the demotion"


class _DummyMessages:
    """Minimal storage stub so messages.error() doesn't blow up in tests."""

    def __init__(self):
        self.added = []

    def add(self, level, message, extra_tags=""):
        self.added.append((level, message, extra_tags))

    def update(self, response):  # called by middleware on real requests
        return response
