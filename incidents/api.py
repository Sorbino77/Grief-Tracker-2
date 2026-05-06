"""REST API viewsets."""

from rest_framework import viewsets

from accounts.permissions import ReadOnlyOrEditor

from .filters import IncidentFilter
from .models import Carrier, Incident, IssueType, Location
from .serializers import (
    CarrierSerializer,
    IncidentSerializer,
    IssueTypeSerializer,
    LocationSerializer,
)


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.select_related("carrier", "issue_type", "location")
    serializer_class = IncidentSerializer
    permission_classes = [ReadOnlyOrEditor]
    filterset_class = IncidentFilter
    ordering_fields = ["issue_date", "primary_ref", "status", "carrier__name"]
    search_fields = ["primary_ref", "ship_id", "supplier_name", "note"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [ReadOnlyOrEditor]


class IssueTypeViewSet(viewsets.ModelViewSet):
    queryset = IssueType.objects.all()
    serializer_class = IssueTypeSerializer
    permission_classes = [ReadOnlyOrEditor]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [ReadOnlyOrEditor]
