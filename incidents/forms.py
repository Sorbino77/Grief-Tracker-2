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
