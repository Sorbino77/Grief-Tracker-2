"""Filter set used by both HTML list view and REST API."""

import django_filters
from django import forms
from django.db.models import Q

from shiptrack.formhelpers import BootstrapFormMixin

from .models import CausingParty, Incident, Status


class _BootstrapFilterForm(BootstrapFormMixin, forms.Form):
    """Empty form; the FilterSet adds the actual fields. Just here to layer
    BootstrapFormMixin onto django-filter's auto-generated form."""


class IncidentFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "ref, supplier, note…"}),
    )
    issue_date_from = django_filters.DateFilter(
        field_name="issue_date",
        lookup_expr="gte",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    issue_date_to = django_filters.DateFilter(
        field_name="issue_date",
        lookup_expr="lte",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    status = django_filters.ChoiceFilter(choices=Status.choices, empty_label="All")
    causing_party = django_filters.ChoiceFilter(choices=CausingParty.choices, empty_label="All")

    class Meta:
        model = Incident
        form = _BootstrapFilterForm
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
