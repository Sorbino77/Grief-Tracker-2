"""Forms with strict whitelist-based validation."""

from __future__ import annotations

import re
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from shiptrack.formhelpers import BootstrapFormMixin

from .models import Incident

_SAFE_REF = re.compile(r"^[A-Za-z0-9 _\-./]{1,64}$")
_ISO2 = re.compile(r"^[A-Z]{2}$")


class IncidentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "primary_ref",
            "ship_id",
            "transport_order_ref",
            "supplier_name",
            "country",
            "location",
            "carrier",
            "issue_type",
            "issue_date",
            "image_available",
            "causing_party",
            "resolve_date",
            "status",
            "note",
        ]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "resolve_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3, "maxlength": 2000}),
        }

    def clean_primary_ref(self) -> str:
        value = (self.cleaned_data.get("primary_ref") or "").strip()
        if not _SAFE_REF.match(value):
            raise ValidationError(
                "Primary reference must contain only letters, numbers, spaces, _, -, ., or /."
            )
        return value

    def clean_ship_id(self) -> str:
        value = (self.cleaned_data.get("ship_id") or "").strip()
        if value and not _SAFE_REF.match(value):
            raise ValidationError("Shipment ID contains unsupported characters.")
        return value

    def clean_transport_order_ref(self) -> str:
        value = (self.cleaned_data.get("transport_order_ref") or "").strip()
        if value and not _SAFE_REF.match(value):
            raise ValidationError("Transport order reference contains unsupported characters.")
        return value

    def clean_country(self) -> str:
        value = (self.cleaned_data.get("country") or "").strip().upper()
        if value and not _ISO2.match(value):
            raise ValidationError("Country must be a 2-letter ISO code.")
        return value

    def clean_issue_date(self) -> date:
        value = self.cleaned_data["issue_date"]
        if value > date.today():
            raise ValidationError("Issue date can't be in the future.")
        return value

    def clean(self):
        cleaned = super().clean() or {}
        issue = cleaned.get("issue_date")
        resolve = cleaned.get("resolve_date")
        if issue and resolve and resolve < issue:
            self.add_error("resolve_date", "Resolve date can't be before issue date.")
        return cleaned


# Conservative whitelist for incident attachments. We deliberately exclude
# executables, scripts, and HTML/SVG (which can carry script payloads) — any
# file extension not in this set is rejected by the form before it reaches
# the storage layer.
ALLOWED_ATTACHMENT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".txt",
        ".csv",
        ".xls",
        ".xlsx",
        ".xlsm",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".zip",
    }
)
MAX_ATTACHMENT_BYTES: int = 25 * 1024 * 1024  # 25 MB, matches the Excel import limit.


class AttachmentUploadForm(BootstrapFormMixin, forms.Form):
    """Upload a single file to attach to an Incident.

    Extension + size are validated here so the view doesn't have to repeat
    the rules; the view just calls ``form.is_valid()`` and reads the
    ``UploadedFile`` from ``cleaned_data["file"]``.
    """

    file = forms.FileField(
        label="Attachment",
        help_text=(
            "Allowed types: PDF, Office (xls/xlsx/xlsm/doc/docx/ppt/pptx), "
            "images (jpg/jpeg/png/gif/webp), text (txt/csv), or zip. "
            f"Max {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB."
        ),
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        ext = ("." + f.name.rsplit(".", 1)[-1].lower()) if "." in f.name else ""
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))
            raise ValidationError(f"Unsupported file type '{ext or '(none)'}'. Allowed: {allowed}.")
        if f.size and f.size > MAX_ATTACHMENT_BYTES:
            mb = MAX_ATTACHMENT_BYTES // (1024 * 1024)
            raise ValidationError(f"File too large. Maximum size is {mb} MB.")
        return f


class ImportUploadForm(BootstrapFormMixin, forms.Form):
    file = forms.FileField(help_text="Upload .xlsx / .xlsm / .csv. Max 25 MB.")
    sheet_name = forms.CharField(
        required=False,
        initial="Incidents",
        help_text="Sheet to read (xlsx/xlsm only). Defaults to 'Incidents'.",
    )
    header_row = forms.IntegerField(
        required=False,
        initial=1,
        min_value=1,
        max_value=100,
        help_text="1-based row number that contains column headers.",
    )
    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Validate only - don't write to the database.",
    )
