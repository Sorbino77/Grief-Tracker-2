"""CLI: ``python manage.py import_incidents <path> [--sheet=Incidents] [--header-row=1] [--dry-run]``."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from incidents.importers import IncidentImporter


class Command(BaseCommand):
    help = "Import incidents from an .xlsx/.xlsm/.csv file."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the spreadsheet to import")
        parser.add_argument("--sheet", default="Incidents")
        parser.add_argument("--header-row", type=int, default=1)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        importer = IncidentImporter(dry_run=opts["dry_run"])
        report = importer.import_path(str(path), sheet=opts["sheet"], header_row=opts["header_row"])
        self.stdout.write(
            self.style.SUCCESS(
                f"{'(dry-run) ' if report.dry_run else ''}"
                f"created={report.created} updated={report.updated} "
                f"skipped={report.skipped} errors={len(report.errors)}"
            )
        )
        for row, msg in report.errors[:25]:
            self.stdout.write(self.style.WARNING(f"  row {row}: {msg}"))
        if len(report.errors) > 25:
            self.stdout.write(self.style.WARNING(f"  ... and {len(report.errors) - 25} more."))
