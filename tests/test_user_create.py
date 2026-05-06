"""Tests for the in-app 'create user' flow (admin invites a teammate)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _post_create(client, **overrides):
    payload = {
        "username": "newbie",
        "email": "newbie@example.com",
        "role": "viewer",
        "password1": "S0meStrong-Passw0rd!",
        "password2": "S0meStrong-Passw0rd!",
    }
    payload.update(overrides)
    return client.post(reverse("accounts:user_create"), data=payload)


def test_anonymous_cannot_reach_user_create(client):
    resp = client.get(reverse("accounts:user_create"))
    assert resp.status_code in (301, 302)
    assert "login" in resp["Location"].lower()


def test_viewer_cannot_reach_user_create(client, viewer_user):
    client.force_login(viewer_user)
    resp = client.get(reverse("accounts:user_create"))
    assert resp.status_code == 403


def test_editor_cannot_reach_user_create(client, editor_user):
    client.force_login(editor_user)
    resp = client.get(reverse("accounts:user_create"))
    assert resp.status_code == 403


def test_admin_sees_form(client, admin_user):
    client.force_login(admin_user)
    resp = client.get(reverse("accounts:user_create"))
    assert resp.status_code == 200
    body = resp.content.decode().lower()
    assert "username" in body
    assert "email" in body
    assert "role" in body


def test_admin_creates_viewer(client, admin_user):
    client.force_login(admin_user)
    resp = _post_create(client)
    assert resp.status_code == 302
    user_model = get_user_model()
    new = user_model.objects.get(username="newbie")
    assert new.email == "newbie@example.com"
    assert new.role == "viewer"
    assert new.is_active is True
    assert new.is_staff is False
    assert new.is_superuser is False
    # Password must be hashed (Argon2 prefix), not stored raw.
    assert new.password.startswith("argon2$") or new.password.startswith("$argon2")
    # The hash actually verifies the plaintext.
    assert new.check_password("S0meStrong-Passw0rd!")
    assert not new.check_password("wrong-password")


def test_admin_creates_admin_grants_is_staff(client, admin_user):
    """Creating another Admin must give them is_staff=True so they can reach
    Django admin. is_superuser stays False — superuser is reserved for
    bootstrap / `createsuperuser`."""
    client.force_login(admin_user)
    resp = _post_create(client, username="boss", email="boss@example.com", role="admin")
    assert resp.status_code == 302
    user_model = get_user_model()
    new = user_model.objects.get(username="boss")
    assert new.role == "admin"
    assert new.is_staff is True
    assert new.is_superuser is False


def test_password_too_short_rejected(client, admin_user):
    client.force_login(admin_user)
    resp = _post_create(
        client,
        password1="short1A!",
        password2="short1A!",
    )
    # Form re-rendered with error → 200, no redirect.
    assert resp.status_code == 200
    body = resp.content.decode().lower()
    assert "at least 12" in body or "too short" in body


def test_password_mismatch_rejected(client, admin_user):
    client.force_login(admin_user)
    resp = _post_create(
        client,
        password1="S0meStrong-Passw0rd!",
        password2="DifferentP4ssw0rd!",
    )
    assert resp.status_code == 200
    user_model = get_user_model()
    assert not user_model.objects.filter(username="newbie").exists()


def test_duplicate_username_rejected(client, admin_user, editor_user):
    client.force_login(admin_user)
    resp = _post_create(client, username=editor_user.username, email="other@example.com")
    assert resp.status_code == 200
    body = resp.content.decode().lower()
    assert "already exists" in body


def test_duplicate_email_rejected(client, admin_user, editor_user):
    client.force_login(admin_user)
    resp = _post_create(client, username="someoneelse", email=editor_user.email)
    assert resp.status_code == 200
    body = resp.content.decode().lower()
    assert "already exists" in body


def test_password_similar_to_username_rejected(client, admin_user):
    client.force_login(admin_user)
    resp = _post_create(
        client,
        username="alicelongname",
        password1="alicelongname-1!",
        password2="alicelongname-1!",
    )
    assert resp.status_code == 200
    body = resp.content.decode().lower()
    assert "too similar" in body or "similar" in body


def test_invalid_role_rejected(client, admin_user):
    client.force_login(admin_user)
    resp = _post_create(client, role="god")
    # Django ChoiceField rejects unknown choices; form re-renders.
    assert resp.status_code == 200
    user_model = get_user_model()
    assert not user_model.objects.filter(username="newbie").exists()
