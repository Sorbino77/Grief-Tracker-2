"""Tests for the analytics pivot-table helper and view."""

from datetime import date

import pytest
from django.urls import reverse

from incidents.models import Carrier, Incident, IssueType, Status
from incidents.pivot import NONE_KEY, build_pivot, dimension_choices

pytestmark = pytest.mark.django_db


@pytest.fixture
def pivot_dataset(admin_user):
    """A handful of carriers x issue-types x years so the grid has shape."""
    arcese = Carrier.objects.create(name="Arcese")
    dsv = Carrier.objects.create(name="DSV")
    damage = IssueType.objects.create(name="DAMAGE")
    labels = IssueType.objects.create(name="NO LABELS")

    rows = [
        ("A1", arcese, damage, date(2024, 3, 1), Status.RESOLVED),
        ("A2", arcese, damage, date(2024, 6, 1), Status.RESOLVED),
        ("A3", arcese, labels, date(2025, 1, 1), Status.ONGOING),
        ("D1", dsv, damage, date(2024, 4, 1), Status.RESOLVED),
        ("D2", dsv, labels, date(2025, 2, 1), Status.ONGOING),
        ("D3", dsv, labels, date(2025, 3, 1), Status.RESOLVED),
    ]
    for ref, carrier, issue, d, status in rows:
        Incident.objects.create(
            primary_ref=ref,
            issue_date=d,
            carrier=carrier,
            issue_type=issue,
            status=status,
            created_by=admin_user,
        )
    return {"arcese": arcese, "dsv": dsv, "damage": damage, "labels": labels}


def test_dimension_choices_has_expected_keys():
    keys = {k for k, _ in dimension_choices()}
    assert {"carrier", "issue_type", "causing_party", "status", "year", "month"} <= keys


def test_pivot_2d_carrier_by_year(pivot_dataset):
    p = build_pivot(Incident.objects.all(), "carrier", "year")
    assert p["row_label"] == "Carrier"
    assert p["col_label"] == "Year"
    assert p["has_columns"] is True
    assert p["col_values"] == [2024, 2025]
    labels = [r["label"] for r in p["rows"]]
    assert labels == ["Arcese", "DSV"]
    arcese_row = p["rows"][0]
    assert arcese_row["cells"] == [2, 1]  # 2024: 2, 2025: 1
    assert arcese_row["total"] == 3
    dsv_row = p["rows"][1]
    assert dsv_row["cells"] == [1, 2]
    assert dsv_row["total"] == 3
    assert p["col_totals"] == [3, 3]
    assert p["grand_total"] == 6
    assert p["max_cell"] == 2


def test_pivot_1d_no_columns(pivot_dataset):
    p = build_pivot(Incident.objects.all(), "carrier", NONE_KEY)
    assert p["has_columns"] is False
    assert p["col_values"] == []
    assert p["col_totals"] == []
    assert {r["label"] for r in p["rows"]} == {"Arcese", "DSV"}
    totals = {r["label"]: r["total"] for r in p["rows"]}
    assert totals == {"Arcese": 3, "DSV": 3}
    assert p["grand_total"] == 6


def test_pivot_with_status_dimension(pivot_dataset):
    p = build_pivot(Incident.objects.all(), "issue_type", "status")
    labels = {r["label"]: dict(zip(p["col_values"], r["cells"], strict=False)) for r in p["rows"]}
    assert labels["DAMAGE"]["RESOLVED"] == 3
    assert labels["NO LABELS"]["ONGOING"] == 2
    assert labels["NO LABELS"]["RESOLVED"] == 1


def test_pivot_unknown_label_for_blanks(admin_user):
    """FK to None and blank CharField should both render as (unknown)."""
    Incident.objects.create(
        primary_ref="X",
        issue_date=date(2025, 1, 1),
        carrier=None,  # no carrier FK
        issue_type=None,
        country="",  # blank CharField
        created_by=admin_user,
    )
    p = build_pivot(Incident.objects.all(), "carrier", "country")
    assert p["rows"][0]["label"] == "(unknown)"
    assert p["col_values"] == ["(unknown)"]


def test_pivot_unknown_dimension_raises():
    with pytest.raises(ValueError, match="row dimension"):
        build_pivot(Incident.objects.all(), "nope")
    with pytest.raises(ValueError, match="column dimension"):
        build_pivot(Incident.objects.all(), "carrier", "nope")


def test_analytics_page_renders_pivot(client, viewer_user, pivot_dataset):
    client.force_login(viewer_user)
    resp = client.get(reverse("incidents:analytics") + "?row=carrier&col=year")
    assert resp.status_code == 200
    body = resp.content.decode()
    # Header line: "Pivot: Carrier x Year"
    assert "Pivot:" in body
    assert "Carrier" in body and "Year" in body
    # Both carriers visible
    assert "Arcese" in body and "DSV" in body
    # Year columns rendered
    assert ">2024<" in body and ">2025<" in body
    # Heatmap CSS hook present on cells
    assert "--cell-ratio:" in body
    # Selectors are pre-populated with current row/col
    assert '<option value="carrier" selected>' in body
    assert '<option value="year" selected>' in body


def test_analytics_page_invalid_dim_falls_back(client, viewer_user, pivot_dataset):
    """Bad ?row= / ?col= must not 500 — view normalises to the defaults."""
    client.force_login(viewer_user)
    resp = client.get(reverse("incidents:analytics") + "?row=evil&col=injection")
    assert resp.status_code == 200
    assert "Carrier" in resp.content.decode()


def test_analytics_page_with_no_columns(client, viewer_user, pivot_dataset):
    client.force_login(viewer_user)
    resp = client.get(reverse("incidents:analytics") + "?row=carrier&col=" + NONE_KEY)
    assert resp.status_code == 200
    body = resp.content.decode()
    # No "Total" column header in the row when has_columns is False
    # (the row total is still shown in the rightmost cell, though)
    assert "Carrier" in body
