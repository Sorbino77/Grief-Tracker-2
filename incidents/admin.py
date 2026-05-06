from django.contrib import admin

from .models import Carrier, Incident, IssueType, Location


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(IssueType)
class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "facility_name", "city", "country", "is_active")
    search_fields = ("code", "facility_name", "city")
    list_filter = ("country", "is_active")


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "primary_ref",
        "ship_id",
        "supplier_name",
        "carrier",
        "issue_type",
        "issue_date",
        "status",
        "causing_party",
    )
    list_filter = ("status", "causing_party", "carrier", "issue_type")
    search_fields = ("primary_ref", "ship_id", "supplier_name", "transport_order_ref", "note")
    date_hierarchy = "issue_date"
    autocomplete_fields = ("carrier", "issue_type", "location")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
