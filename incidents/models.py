"""Domain models for the incident tracker."""

from __future__ import annotations

import contextlib
import os
import re
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ----- reference data --------------------------------------------------------
class Carrier(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class IssueType(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Location(TimeStampedModel):
    """A facility / dock / warehouse code (e.g. ``DK-BM01``)."""

    code = models.CharField(max_length=50, unique=True)
    facility_name = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


# ----- main record -----------------------------------------------------------
class CausingParty(models.TextChoices):
    SUPPLIER = "SUPPLIER", "Supplier"
    CARRIER = "CARRIER", "Carrier"
    MIXED = "MIXED", "Mixed"
    UNKNOWN = "UNKNOWN", "Unknown"


class Status(models.TextChoices):
    ONGOING = "ONGOING", "Ongoing"
    RESOLVED = "RESOLVED", "Resolved"


class ImageAvailable(models.TextChoices):
    YES = "YES", "Yes"
    NO = "NO", "No"
    NA = "NA", "N/A"


class Incident(TimeStampedModel):
    """A single shipment incident (damage, missing labels, etc.)."""

    primary_ref = models.CharField("Primary reference", max_length=64, db_index=True)
    ship_id = models.CharField("Shipment ID", max_length=64, blank=True, db_index=True)
    transport_order_ref = models.CharField("Transport order reference", max_length=64, blank=True)

    supplier_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="ISO-2 country code")

    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, null=True, blank=True, related_name="incidents"
    )
    carrier = models.ForeignKey(
        Carrier, on_delete=models.PROTECT, null=True, blank=True, related_name="incidents"
    )
    issue_type = models.ForeignKey(
        IssueType, on_delete=models.PROTECT, null=True, blank=True, related_name="incidents"
    )

    issue_date = models.DateField(db_index=True)
    image_available = models.CharField(
        max_length=3, choices=ImageAvailable.choices, default=ImageAvailable.NA
    )

    causing_party = models.CharField(
        max_length=10, choices=CausingParty.choices, default=CausingParty.UNKNOWN
    )
    resolve_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ONGOING, db_index=True)
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_incidents",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_incidents",
    )

    class Meta:
        ordering = ["-issue_date", "-id"]
        indexes = [
            models.Index(fields=["status", "issue_date"]),
            models.Index(fields=["carrier", "issue_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["primary_ref", "issue_type"],
                name="uniq_primary_ref_issue_type",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.primary_ref} - {self.issue_type or '(no type)'}"

    @property
    def is_resolved(self) -> bool:
        return self.status == Status.RESOLVED

    def mark_resolved(self, user=None) -> None:
        self.status = Status.RESOLVED
        if not self.resolve_date:
            self.resolve_date = timezone.localdate()
        if user is not None:
            self.updated_by = user
        self.save()


# ----- attachments -----------------------------------------------------------
def _attachment_upload_path(instance: IncidentAttachment, filename: str) -> str:
    """Compute the on-disk path for an uploaded attachment.

    Layout: ``incident_attachments/<incident_pk>/<uuid-hex>_<safe-name>``.

    Why a UUID prefix: prevents collisions when two users upload files with
    the same name, and stops one user from guessing another's path. Why we
    still keep the (sanitised) original name: it makes the file recognisable
    when an admin browses MEDIA_ROOT directly.
    """
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(filename)).strip("._-")
    if not safe:
        safe = "file"
    safe = safe[:80]
    return f"incident_attachments/{instance.incident_id}/{uuid.uuid4().hex}_{safe}"


class IncidentAttachment(models.Model):
    """A file attached to an Incident (photo, PDF, supplier email, etc.).

    Files are written to ``MEDIA_ROOT`` under a per-incident folder with a
    UUID-prefixed filename (see ``_attachment_upload_path``). The view layer
    validates extension + size before the model ever sees the data.
    """

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=_attachment_upload_path, max_length=255)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_attachments",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]
        indexes = [models.Index(fields=["incident", "-uploaded_at"])]

    def __str__(self) -> str:  # pragma: no cover
        return self.original_name or self.file.name

    @property
    def human_size(self) -> str:
        """Human-readable size, e.g. ``"1.2 MB"`` / ``"680 KB"`` / ``"42 B"``."""
        n = float(self.size_bytes or 0)
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024 or unit == "GB":
                return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} GB"

    @property
    def extension(self) -> str:
        return os.path.splitext(self.original_name or self.file.name)[1].lower()

    def delete(self, *args, **kwargs):
        """Remove the on-disk file when the row is deleted.

        ``FileField`` does NOT auto-delete the file (intentional, to make
        rollbacks safer). We do here so an admin clicking "Delete attachment"
        actually frees the disk space."""
        storage, path = self.file.storage, self.file.name
        super().delete(*args, **kwargs)
        if path:
            # Best-effort cleanup: a missing file or a locked one on Windows
            # shouldn't prevent the DB-level delete from succeeding.
            with contextlib.suppress(Exception):
                storage.delete(path)
