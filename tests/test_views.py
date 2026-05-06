"""View-level tests covering RBAC and basic happy paths."""

from datetime import date

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _login(client, user):
    client.force_login(user)


def test_anonymous_redirected_from_list(client):
    resp = client.get(reverse("incidents:list"))
    assert resp.status_code in (302, 301)
    assert "/accounts/login" in resp["Location"] or "login" in resp["Location"]


def test_viewer_can_see_list(client, viewer_user, sample_record):
    _login(client, viewer_user)
    resp = client.get(reverse("incidents:list"))
    assert resp.status_code == 200
    assert sample_record.primary_ref.encode() in resp.content


def test_viewer_cannot_create(client, viewer_user):
    _login(client, viewer_user)
    resp = client.get(reverse("incidents:create"))
    assert resp.status_code == 403


def test_editor_can_create(client, editor_user, reference_data):
    _login(client, editor_user)
    resp = client.post(
        reverse("incidents:create"),
        data={
            "primary_ref": "NEW-001",
            "ship_id": "20250101-S-001",
            "transport_order_ref": "",
            "supplier_name": "Acme",
            "country": "BE",
            "location": reference_data["loc"].pk,
            "carrier": reference_data["carrier"].pk,
            "issue_type": reference_data["issue"].pk,
            "issue_date": "2025-01-15",
            "image_available": "YES",
            "causing_party": "SUPPLIER",
            "resolve_date": "",
            "status": "ONGOING",
            "note": "test",
        },
    )
    assert resp.status_code == 302


def test_editor_cannot_delete(client, editor_user, sample_record):
    _login(client, editor_user)
    resp = client.post(reverse("incidents:delete", kwargs={"pk": sample_record.pk}))
    assert resp.status_code == 403


def test_admin_can_delete(client, admin_user, sample_record):
    _login(client, admin_user)
    resp = client.post(reverse("incidents:delete", kwargs={"pk": sample_record.pk}))
    assert resp.status_code == 302


def test_invalid_primary_ref_rejected(client, editor_user, reference_data):
    _login(client, editor_user)
    resp = client.post(
        reverse("incidents:create"),
        data={
            "primary_ref": "<script>alert(1)</script>",
            "issue_date": "2025-01-15",
            "image_available": "NA",
            "causing_party": "UNKNOWN",
            "status": "ONGOING",
            "carrier": reference_data["carrier"].pk,
            "issue_type": reference_data["issue"].pk,
        },
    )
    assert resp.status_code == 200
    body = resp.content.lower()
    assert b"only letters" in body or b"primary reference" in body


def test_future_issue_date_rejected(client, editor_user, reference_data):
    _login(client, editor_user)
    resp = client.post(
        reverse("incidents:create"),
        data={
            "primary_ref": "FUT-1",
            "issue_date": "2099-01-01",
            "image_available": "NA",
            "causing_party": "UNKNOWN",
            "status": "ONGOING",
            "carrier": reference_data["carrier"].pk,
            "issue_type": reference_data["issue"].pk,
        },
    )
    assert resp.status_code == 200
    assert b"future" in resp.content.lower()


def test_filter_by_status(client, viewer_user, reference_data, admin_user):
    from incidents.models import Incident

    Incident.objects.create(
        primary_ref="A",
        issue_date=date(2025, 1, 1),
        carrier=reference_data["carrier"],
        issue_type=reference_data["issue"],
        status="ONGOING",
        created_by=admin_user,
    )
    Incident.objects.create(
        primary_ref="B",
        issue_date=date(2025, 1, 2),
        carrier=reference_data["carrier"],
        issue_type=reference_data["issue"],
        status="RESOLVED",
        created_by=admin_user,
    )
    _login(client, viewer_user)
    resp = client.get(reverse("incidents:list") + "?status=ONGOING")
    assert resp.status_code == 200
    assert b">A<" in resp.content
    assert b">B<" not in resp.content


def test_healthz_open(client):
    resp = client.get("/healthz/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
