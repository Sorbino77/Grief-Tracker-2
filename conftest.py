"""Project-wide pytest fixtures.

Tests run against SQLite in-memory by default — see env vars below. Production
code stays on PostgreSQL via docker-compose.

NOTE: env vars are set here at module import, but pytest-django also reads
Django settings during ``pytest_load_initial_conftests`` with ``tryfirst=True``
— which can run *before* this module is imported. To make tests robust, the
settings module honours ``DJANGO_TESTING`` and falls back to a safe dev secret.
The values below are still set as a belt-and-braces measure.
"""

from __future__ import annotations

import os

# Set test env BEFORE Django is imported anywhere.
os.environ.setdefault("DJANGO_TESTING", "True")
os.environ.setdefault("USE_POSTGRES", "False")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-please-do-not-use-in-prod")
os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
os.environ.setdefault("OAUTH_GOOGLE_ENABLED", "False")
os.environ.setdefault("OAUTH_MICROSOFT_ENABLED", "False")

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from incidents.models import Carrier, Incident, IssueType, Location

_TEST_PASSWORD = "A-strong-pass-123!"  # noqa: S105 — fixture-only constant.


@pytest.fixture
def user_model():
    return get_user_model()


@pytest.fixture
def admin_user(db, user_model):
    return user_model.objects.create_user(
        username="alice",
        email="alice@example.com",
        password=_TEST_PASSWORD,
        role="admin",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def editor_user(db, user_model):
    return user_model.objects.create_user(
        username="bob",
        email="bob@example.com",
        password=_TEST_PASSWORD,
        role="editor",
    )


@pytest.fixture
def viewer_user(db, user_model):
    return user_model.objects.create_user(
        username="carol",
        email="carol@example.com",
        password=_TEST_PASSWORD,
        role="viewer",
    )


@pytest.fixture
def reference_data(db):
    carrier = Carrier.objects.create(name="Arcese")
    issue = IssueType.objects.create(name="DAMAGE")
    loc = Location.objects.create(code="DK-BM01", facility_name="ACM", country="GB")
    return {"carrier": carrier, "issue": issue, "loc": loc}


@pytest.fixture
def sample_record(db, reference_data, admin_user):
    return Incident.objects.create(
        primary_ref="5014641074",
        ship_id="20241213-S-70149",
        supplier_name="Carraro Drive Tech Spa",
        country="GB",
        location=reference_data["loc"],
        carrier=reference_data["carrier"],
        issue_type=reference_data["issue"],
        issue_date=date(2025, 1, 2),
        causing_party="MIXED",
        resolve_date=date(2025, 1, 8),
        status="RESOLVED",
        note="Pallet completely broken",
        created_by=admin_user,
        updated_by=admin_user,
    )
