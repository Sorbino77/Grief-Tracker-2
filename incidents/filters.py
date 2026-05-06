"""Filter set used by both HTML list view and REST API."""

import django_filters
from django.db.models import Q

from .models import CausingParty, Incident, Status


class IncidentFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    issue_date_from = django_filters.DateFilter(field_name="issue_date", lookup_expr="gte")
    issue_date_to = django_filters.DateFilter(field_name="issue_date", lookup_expr="lte")
    status = django_filters.ChoiceFilter(choices=Status.choices)
    causing_party = django_filters.ChoiceFilter(choices=CausingParty.choices)

    class Meta:
        model = Incident
        fields = [
            "status",
            "causing_party",
            "carrier",
            "issue_type",
            "location",
            "country",
            "issue_date_from",
            "issue_date_to",
            "q",
        ]

    def search(self, queryset, name, value: str):
        # ORM `__icontains` parameterises bind values; no SQL injection risk.
        return queryset.filter(
            Q(primary_ref__icontains=value)
            | Q(ship_id__icontains=value)
            | Q(transport_order_ref__icontains=value)
            | Q(supplier_name__icontains=value)
            | Q(note__icontains=value)
        )
