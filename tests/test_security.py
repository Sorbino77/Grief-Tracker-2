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
