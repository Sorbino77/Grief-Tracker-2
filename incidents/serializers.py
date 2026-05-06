"""DRF serializers."""

from rest_framework import serializers

from .models import Carrier, Incident, IssueType, Location


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name", "is_active"]


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ["id", "name", "description", "is_active"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "code", "facility_name", "city", "country", "is_active"]


class IncidentSerializer(serializers.ModelSerializer):
    carrier_name = serializers.CharField(source="carrier.name", read_only=True)
    issue_type_name = serializers.CharField(source="issue_type.name", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "primary_ref",
            "ship_id",
            "transport_order_ref",
            "supplier_name",
            "country",
            "location",
            "location_code",
            "carrier",
            "carrier_name",
            "issue_type",
            "issue_type_name",
            "issue_date",
            "image_available",
            "causing_party",
            "resolve_date",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
