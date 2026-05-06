import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_api_requires_auth():
    c = APIClient()
    resp = c.get("/api/v1/incidents/")
    assert resp.status_code in (401, 403)


def test_api_viewer_read_only(viewer_user, sample_record, reference_data):
    c = APIClient()
    c.force_authenticate(user=viewer_user)
    resp = c.get("/api/v1/incidents/")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["count"] == 1

    bad = c.post(
        "/api/v1/incidents/",
        {
            "primary_ref": "A",
            "issue_date": "2025-01-01",
            "status": "ONGOING",
            "image_available": "NA",
            "causing_party": "UNKNOWN",
            "carrier": reference_data["carrier"].pk,
            "issue_type": reference_data["issue"].pk,
        },
        format="json",
    )
    assert bad.status_code in (403, 405)


def test_api_editor_can_post(editor_user, reference_data):
    c = APIClient()
    c.force_authenticate(user=editor_user)
    resp = c.post(
        "/api/v1/incidents/",
        {
            "primary_ref": "API-1",
            "issue_date": "2025-01-01",
            "status": "ONGOING",
            "image_available": "NA",
            "causing_party": "SUPPLIER",
            "carrier": reference_data["carrier"].pk,
            "issue_type": reference_data["issue"].pk,
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["primary_ref"] == "API-1"
