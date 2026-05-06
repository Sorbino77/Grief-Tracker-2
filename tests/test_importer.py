"""Importer tests against a tiny synthesised xlsx and a CSV."""

import io

import pytest
from openpyxl import Workbook

from incidents.importers import IncidentImporter
from incidents.models import Carrier, Incident, IssueType, Location

pytestmark = pytest.mark.django_db


def _make_xlsx_bytes() -> io.BytesIO:
    """Build a tiny in-memory xlsx with header at row 1."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Incidents"
    ws.append(
        [
            "Primary Ref",
            "Ship ID",
            "TO Ref",
            "Supplier Name",
            "Ctry",
            "Loc",
            "Carrier",
            "Issue type",
            "Date",
            "Image",
            "Causing party",
            "Resolve Date",
            "Status",
            "Note",
        ]
    )
    ws.append(
        [
            "5014641074",
            "20241213-S-70149",
            "20241213617107",
            "Carraro",
            "GB",
            "DK-BM01",
            "Arcese",
            "DAMAGE",
            "2025-01-02",
            "Yes",
            "MIXED",
            "2025-01-08",
            "SOLVED",
            "Pallet broken",
        ]
    )
    ws.append(
        [
            "5014663869",
            "20241213-S-70401",
            "20241213617318",
            "LMS",
            "GB",
            "DX01-L5",
            "Arcese",
            "DAMAGED LABEL",
            "2025-01-02",
            "Yes",
            "MIXED",
            "2025-01-02",
            "SOLVED",
            "",
        ]
    )
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_xlsx_import_creates_records():
    importer = IncidentImporter()
    report = importer.import_stream(
        _make_xlsx_bytes(),
        filename="t.xlsx",
        sheet="Incidents",
        header_row=1,
    )
    assert report.created == 2
    assert report.skipped == 0
    assert Incident.objects.count() == 2
    assert Carrier.objects.filter(name="Arcese").exists()
    assert IssueType.objects.filter(name="DAMAGE").exists()
    assert Location.objects.filter(code="DK-BM01").exists()


def test_xlsx_import_is_idempotent():
    importer1 = IncidentImporter()
    importer1.import_stream(_make_xlsx_bytes(), filename="t.xlsx", sheet="Incidents", header_row=1)
    importer2 = IncidentImporter()
    report = importer2.import_stream(_make_xlsx_bytes(), filename="t.xlsx", sheet="Incidents", header_row=1)
    assert report.updated == 2
    assert report.created == 0
    assert Incident.objects.count() == 2


def test_dry_run_doesnt_persist():
    importer = IncidentImporter(dry_run=True)
    report = importer.import_stream(
        _make_xlsx_bytes(),
        filename="t.xlsx",
        sheet="Incidents",
        header_row=1,
    )
    assert report.dry_run is True
    assert Incident.objects.count() == 0


def test_csv_import():
    csv_bytes = io.BytesIO(
        b"Primary Ref,Ship ID,Carrier,Issue type,Date,Causing party,Status\n"
        b"R1,S-1,DHL,NO LABELS,2025-02-01,SUPPLIER,SOLVED\n"
        b"R2,S-2,DHL,NO LABELS,2025-02-02,CARRIER,ONGOING\n"
    )
    importer = IncidentImporter()
    report = importer.import_stream(csv_bytes, filename="t.csv")
    assert report.created == 2
    assert Incident.objects.filter(status="RESOLVED").count() == 1
    assert Incident.objects.filter(status="ONGOING").count() == 1


def test_legacy_kn_ref_header_still_works():
    """Old K+N spreadsheets must still import."""
    csv_bytes = io.BytesIO(b"K&N REF,Carrier,Issue type,Date,Status\n" b"LEG-1,DHL,X,2025-02-01,ONGOING\n")
    importer = IncidentImporter()
    report = importer.import_stream(csv_bytes, filename="legacy.csv")
    assert report.created == 1
    assert Incident.objects.filter(primary_ref="LEG-1").exists()


def test_unsupported_filetype_rejected():
    importer = IncidentImporter()
    with pytest.raises(ValueError, match="Unsupported"):
        importer.import_stream(io.BytesIO(b"x"), filename="evil.exe")


def test_import_skips_rows_with_bad_dates():
    csv_bytes = io.BytesIO(
        b"Primary Ref,Carrier,Issue type,Date,Status\n"
        b"GOOD,DHL,X,2025-02-01,ONGOING\n"
        b"BAD,DHL,X,not-a-date,ONGOING\n"
    )
    importer = IncidentImporter()
    report = importer.import_stream(csv_bytes, filename="t.csv")
    assert report.created == 1
    assert report.skipped == 1
    assert any("date" in msg.lower() for _, msg in report.errors)
