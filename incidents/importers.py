"""Spreadsheet importer.

Accepts .xlsx / .xlsm / .csv. Forgiving about header variations, performs
``get_or_create`` on reference data, reports per-row errors instead of failing
the whole batch, de-duplicates on (primary_ref, issue_type), and runs in a
transaction; ``--dry-run`` validates without writing.
"""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from django.db import transaction
from openpyxl import load_workbook

from .models import (
    Carrier,
    CausingParty,
    ImageAvailable,
    Incident,
    IssueType,
    Location,
    Status,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 200_000
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm", ".csv"}

_HEADER_ALIASES: dict[str, str] = {
    # Primary reference — also recognise legacy K+N column names so old
    # spreadsheets import unchanged.
    "primary ref": "primary_ref",
    "primary reference": "primary_ref",
    "ref": "primary_ref",
    "ref1": "primary_ref",
    "ref2": "primary_ref",
    "ref3": "primary_ref",
    "k&n ref": "primary_ref",
    "kn ref": "primary_ref",
    "kuehne ref": "primary_ref",
    # Shipment ID
    "ship id": "ship_id",
    "shipid": "ship_id",
    "shipment id": "ship_id",
    # Transport order ref
    "to ref": "transport_order_ref",
    "transport order ref": "transport_order_ref",
    "transport order reference": "transport_order_ref",
    # Free-text fields
    "supplier name": "supplier_name",
    "supplier": "supplier_name",
    "ctry": "country",
    "country": "country",
    "loc": "location",
    "location": "location",
    "carrier": "carrier",
    "issue type": "issue_type",
    "issuetype": "issue_type",
    "date": "issue_date",
    "issue date": "issue_date",
    "image": "image_available",
    "causing party": "causing_party",
    "resolve date": "resolve_date",
    "resolvedate": "resolve_date",
    "status": "status",
    "note": "note",
    "notes": "note",
    "comment": "note",
}


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total(self) -> int:
        return self.created + self.updated + self.skipped

    def as_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "dry_run": self.dry_run,
            "total": self.total,
        }


def _norm(s: Any) -> str:
    return str(s).strip().lower() if s is not None else ""


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_str(value: Any, *, max_len: int | None = None) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if max_len is not None:
        s = s[:max_len]
    return s


def _normalize_status(value: Any) -> str:
    s = _norm(value)
    if s in {"solved", "resolved", "closed", "done"}:
        return Status.RESOLVED
    return Status.ONGOING


def _normalize_party(value: Any) -> str:
    mapping = {
        "supplier": CausingParty.SUPPLIER,
        "carrier": CausingParty.CARRIER,
        "mixed": CausingParty.MIXED,
    }
    return mapping.get(_norm(value), CausingParty.UNKNOWN)


def _normalize_image(value: Any) -> str:
    s = _norm(value)
    if s in {"yes", "y", "true", "1"}:
        return ImageAvailable.YES
    if s in {"no", "n", "false", "0"}:
        return ImageAvailable.NO
    return ImageAvailable.NA


def _map_headers(raw_headers: Iterable[Any]) -> dict[int, str]:
    """Return {col_index: canonical_name} for headers we recognise."""
    return {
        idx: canonical
        for idx, raw in enumerate(raw_headers)
        if (canonical := _HEADER_ALIASES.get(_norm(raw)))
    }


class IncidentImporter:
    """Stateless importer. Pass a file-like object to :meth:`import_stream`."""

    def __init__(self, *, user=None, dry_run: bool = False):
        self.user = user
        self.dry_run = dry_run
        self.report = ImportReport(dry_run=dry_run)

    def import_path(self, path: str, *, sheet: str = "Incidents", header_row: int = 1) -> ImportReport:
        if path.lower().endswith(".csv"):
            with open(path, newline="", encoding="utf-8-sig") as fh:
                return self._import_csv(fh)
        return self._import_xlsx(path, sheet=sheet, header_row=header_row)

    def import_stream(
        self,
        stream,
        *,
        filename: str,
        sheet: str = "Incidents",
        header_row: int = 1,
    ) -> ImportReport:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        if ext == ".csv":
            text = io.TextIOWrapper(stream, encoding="utf-8-sig")
            return self._import_csv(text)
        return self._import_xlsx(stream, sheet=sheet, header_row=header_row)

    def _import_xlsx(self, source, *, sheet: str, header_row: int) -> ImportReport:
        wb = load_workbook(source, data_only=True, read_only=True, keep_vba=False)
        if sheet not in wb.sheetnames:
            sheet = wb.sheetnames[0]
        ws = wb[sheet]

        rows = ws.iter_rows(values_only=True)
        headers: dict[int, str] = {}
        for idx, row in enumerate(rows, start=1):
            if idx == header_row:
                headers = _map_headers(row)
                break
        if not headers or "primary_ref" not in headers.values():
            raise ValueError(
                "Could not locate a 'Primary Ref' / 'REF' column in the header row. "
                "Adjust the 'header row' setting and try again."
            )

        with transaction.atomic():
            sid = transaction.savepoint()
            for row_num, row in enumerate(rows, start=header_row + 1):
                if row_num - header_row > MAX_ROWS:
                    self.report.errors.append((row_num, "Row cap reached; aborting."))
                    break
                if row is None or all(c is None or c == "" for c in row):
                    continue
                record = {canonical: row[idx] for idx, canonical in headers.items() if idx < len(row)}
                self._ingest(record, row_num)
            if self.dry_run:
                transaction.savepoint_rollback(sid)
            else:
                transaction.savepoint_commit(sid)
        return self.report

    def _import_csv(self, fh) -> ImportReport:
        reader = csv.reader(fh)
        try:
            raw_headers = next(reader)
        except StopIteration as exc:
            raise ValueError("Empty CSV file.") from exc
        headers = _map_headers(raw_headers)
        if not headers or "primary_ref" not in headers.values():
            raise ValueError("CSV must contain a 'Primary Ref' / 'REF' column.")

        with transaction.atomic():
            sid = transaction.savepoint()
            for row_num, row in enumerate(reader, start=2):
                if row_num > MAX_ROWS + 1:
                    self.report.errors.append((row_num, "Row cap reached; aborting."))
                    break
                record = {canonical: row[idx] for idx, canonical in headers.items() if idx < len(row)}
                self._ingest(record, row_num)
            if self.dry_run:
                transaction.savepoint_rollback(sid)
            else:
                transaction.savepoint_commit(sid)
        return self.report

    def _ingest(self, record: dict[str, Any], row_num: int) -> None:
        try:
            primary_ref = _parse_str(record.get("primary_ref"), max_len=64)
            if not primary_ref:
                self.report.skipped += 1
                return

            issue_date = _parse_date(record.get("issue_date"))
            if not issue_date:
                self.report.errors.append((row_num, "Missing or unparseable date."))
                self.report.skipped += 1
                return

            issue_type_name = _parse_str(record.get("issue_type"), max_len=120)
            issue_type = IssueType.objects.get_or_create(name=issue_type_name)[0] if issue_type_name else None

            carrier_name = _parse_str(record.get("carrier"), max_len=100)
            carrier = Carrier.objects.get_or_create(name=carrier_name)[0] if carrier_name else None

            loc_code = _parse_str(record.get("location"), max_len=50)
            location = None
            if loc_code and loc_code.lower() not in {"no loc", "n/a", "na"}:
                location = Location.objects.get_or_create(code=loc_code)[0]

            defaults = {
                "ship_id": _parse_str(record.get("ship_id"), max_len=64),
                "transport_order_ref": _parse_str(record.get("transport_order_ref"), max_len=64),
                "supplier_name": _parse_str(record.get("supplier_name"), max_len=255),
                "country": _parse_str(record.get("country"), max_len=2).upper(),
                "location": location,
                "carrier": carrier,
                "issue_date": issue_date,
                "image_available": _normalize_image(record.get("image_available")),
                "causing_party": _normalize_party(record.get("causing_party")),
                "resolve_date": _parse_date(record.get("resolve_date")),
                "status": _normalize_status(record.get("status")),
                "note": _parse_str(record.get("note"), max_len=10_000),
                "updated_by": self.user,
            }

            obj, created = Incident.objects.update_or_create(
                primary_ref=primary_ref,
                issue_type=issue_type,
                defaults=defaults,
            )
            if created:
                obj.created_by = self.user
                obj.save(update_fields=["created_by"])
                self.report.created += 1
            else:
                self.report.updated += 1
        except Exception as exc:
            logger.warning("Import row %s failed: %s", row_num, exc, exc_info=True)
            self.report.errors.append((row_num, str(exc)[:300]))
            self.report.skipped += 1
