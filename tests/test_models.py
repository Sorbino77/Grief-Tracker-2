from datetime import date

import pytest

from incidents.models import Incident


@pytest.mark.django_db
def test_record_str_uses_primary_ref(sample_record):
    assert sample_record.primary_ref in str(sample_record)


@pytest.mark.django_db
def test_mark_resolved_sets_status_and_date(reference_data, admin_user):
    rec = Incident.objects.create(
        primary_ref="X1",
        issue_date=date(2025, 1, 1),
        carrier=reference_data["carrier"],
        issue_type=reference_data["issue"],
        status="ONGOING",
        created_by=admin_user,
        updated_by=admin_user,
    )
    rec.mark_resolved(user=admin_user)
    rec.refresh_from_db()
    assert rec.status == "RESOLVED"
    assert rec.resolve_date is not None
    assert rec.is_resolved


@pytest.mark.django_db
def test_unique_constraint_primary_ref_issue_type(reference_data, admin_user):
    common = {
        "primary_ref": "DUPE-1",
        "issue_date": date(2025, 1, 1),
        "carrier": reference_data["carrier"],
        "issue_type": reference_data["issue"],
        "created_by": admin_user,
        "updated_by": admin_user,
    }
    Incident.objects.create(**common)
    with pytest.raises(Exception):
        Incident.objects.create(**common)


def test_role_helpers(admin_user, editor_user, viewer_user):
    assert admin_user.is_admin and admin_user.is_editor and admin_user.is_viewer
    assert not editor_user.is_admin and editor_user.is_editor
    assert not viewer_user.is_editor
    assert viewer_user.is_viewer
