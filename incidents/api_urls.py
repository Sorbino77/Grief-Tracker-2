from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import CarrierViewSet, IncidentViewSet, IssueTypeViewSet, LocationViewSet

router = DefaultRouter()
router.register(r"incidents", IncidentViewSet, basename="incident")
router.register(r"carriers", CarrierViewSet, basename="carrier")
router.register(r"issue-types", IssueTypeViewSet, basename="issuetype")
router.register(r"locations", LocationViewSet, basename="location")

urlpatterns = [
    path("v1/", include(router.urls)),
    path("v1/auth/", include("rest_framework.urls")),  # Browsable API login
]
