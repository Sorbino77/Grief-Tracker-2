"""HTML views for browsing, editing, and importing incidents."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from accounts.models import Role
from accounts.permissions import role_required

from .filters import IncidentFilter
from .forms import ImportUploadForm, IncidentForm
from .importers import ALLOWED_EXTENSIONS, IncidentImporter
from .models import Incident, Status

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@login_required
def incident_list(request):
    qs = Incident.objects.select_related("carrier", "issue_type", "location")
    f = IncidentFilter(request.GET, queryset=qs)
    paginator = Paginator(f.qs, 50)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "incidents/incident_list.html",
        {"filter": f, "page_obj": page, "Status": Status},
    )


@login_required
def incident_detail(request, pk: int):
    obj = get_object_or_404(
        Incident.objects.select_related("carrier", "issue_type", "location", "created_by", "updated_by"),
        pk=pk,
    )
    return render(request, "incidents/incident_detail.html", {"obj": obj})


@role_required(Role.ADMIN, Role.EDITOR)
def incident_create(request):
    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            messages.success(request, "Incident created.")
            return redirect("incidents:detail", pk=obj.pk)
    else:
        form = IncidentForm()
    return render(request, "incidents/incident_form.html", {"form": form, "mode": "create"})


@role_required(Role.ADMIN, Role.EDITOR)
def incident_edit(request, pk: int):
    obj = get_object_or_404(Incident, pk=pk)
    if request.method == "POST":
        form = IncidentForm(request.POST, instance=obj)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.updated_by = request.user
            saved.save()
            messages.success(request, "Incident updated.")
            return redirect("incidents:detail", pk=saved.pk)
    else:
        form = IncidentForm(instance=obj)
    return render(request, "incidents/incident_form.html", {"form": form, "obj": obj, "mode": "edit"})


@role_required(Role.ADMIN)
@require_http_methods(["POST"])
def incident_delete(request, pk: int):
    obj = get_object_or_404(Incident, pk=pk)
    obj.delete()
    messages.success(request, "Incident deleted.")
    return redirect("incidents:list")


@role_required(Role.ADMIN, Role.EDITOR)
@require_http_methods(["POST"])
def incident_resolve(request, pk: int):
    obj = get_object_or_404(Incident, pk=pk)
    obj.mark_resolved(user=request.user)
    messages.success(request, "Marked as resolved.")
    return redirect("incidents:detail", pk=obj.pk)


@role_required(Role.ADMIN, Role.EDITOR)
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def incident_import(request):
    """Spreadsheet upload handler."""
    if request.method == "POST":
        form = ImportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data["file"]
            ext = "." + uploaded.name.rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return HttpResponseBadRequest("Unsupported file type.")
            if uploaded.size and uploaded.size > _MAX_UPLOAD_BYTES:
                return HttpResponseBadRequest("File too large (max 25 MB).")
            try:
                importer = IncidentImporter(
                    user=request.user,
                    dry_run=form.cleaned_data["dry_run"],
                )
                report = importer.import_stream(
                    uploaded.file,
                    filename=uploaded.name,
                    sheet=form.cleaned_data.get("sheet_name") or "Incidents",
                    header_row=form.cleaned_data.get("header_row") or 1,
                )
            except Exception as exc:
                logger.exception("Import failed")
                messages.error(request, f"Import failed: {exc}")
                return redirect("incidents:import")
            messages.success(
                request,
                f"Import {'(dry-run) ' if report.dry_run else ''}finished: "
                f"{report.created} created, {report.updated} updated, "
                f"{report.skipped} skipped, {len(report.errors)} errors.",
            )
            return render(
                request,
                "incidents/import.html",
                {"form": ImportUploadForm(), "report": report},
            )
    else:
        form = ImportUploadForm()
    return render(request, "incidents/import.html", {"form": form, "report": None})


@login_required
def analytics(request):
    """Pivot-table-style summary across the incidents."""
    qs = Incident.objects.all()
    f = IncidentFilter(request.GET, queryset=qs)
    base = f.qs

    by_carrier = base.values("carrier__name").annotate(n=Count("id")).order_by("-n")[:20]
    by_issue = base.values("issue_type__name").annotate(n=Count("id")).order_by("-n")[:20]
    by_party = base.values("causing_party").annotate(n=Count("id")).order_by("-n")
    by_status = base.values("status").annotate(n=Count("id")).order_by("-n")
    by_year = base.annotate(y=ExtractYear("issue_date")).values("y").annotate(n=Count("id")).order_by("y")

    return render(
        request,
        "incidents/analytics.html",
        {
            "filter": f,
            "by_carrier": list(by_carrier),
            "by_issue": list(by_issue),
            "by_party": list(by_party),
            "by_status": list(by_status),
            "by_year": list(by_year),
            "total": base.count(),
        },
    )
