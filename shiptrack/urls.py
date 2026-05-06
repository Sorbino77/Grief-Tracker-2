"""Top-level URL routes."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView


def healthz(_request):
    """Liveness probe used by Docker/K8s. Cheap and unauthenticated."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    # allauth handles login, signup, social, password reset
    path("accounts/", include("allauth.urls")),
    # local accounts views (profile, role mgmt)
    path("u/", include("accounts.urls", namespace="accounts")),
    # main app
    path("incidents/", include("incidents.urls", namespace="incidents")),
    path("api/", include("incidents.api_urls")),
    path("", RedirectView.as_view(pattern_name="incidents:list", permanent=False)),
]
