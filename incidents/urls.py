from django.urls import path

from . import views

app_name = "incidents"

urlpatterns = [
    path("", views.incident_list, name="list"),
    path("new/", views.incident_create, name="create"),
    path("import/", views.incident_import, name="import"),
    path("analytics/", views.analytics, name="analytics"),
    path("<int:pk>/", views.incident_detail, name="detail"),
    path("<int:pk>/edit/", views.incident_edit, name="edit"),
    path("<int:pk>/delete/", views.incident_delete, name="delete"),
    path("<int:pk>/resolve/", views.incident_resolve, name="resolve"),
    path("<int:pk>/attachments/upload/", views.attachment_upload, name="attachment_upload"),
    path("attachments/<int:pk>/delete/", views.attachment_delete, name="attachment_delete"),
]
