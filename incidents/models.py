"""Domain models for the incident tracker."""

from __future__ import annotations

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
