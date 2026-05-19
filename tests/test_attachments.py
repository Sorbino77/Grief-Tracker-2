"""Tests for the per-incident file attachment feature.

Covers:
- form-level validation (extension whitelist, size cap)
- RBAC (viewer denied, editor allowed)
- happy path: upload → file stored on disk → listed on detail page
- delete removes both the DB row AND the file on disk
- on-disk path includes the incident pk + a UUID prefix
"""

from __future__ import annotations

import os
import shutil

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from incidents.forms import (
    MAX_ATTACHMENT_BYTES,
    AttachmentUploadForm,
)
from incidents.models import IncidentAttachment

pytestmark = pytest.mark.django_db


@pytest.fixture
def media_root(tmp_path, settings):
    """Redirect MEDIA_ROOT to a tmp dir so tests don't pollute the project."""
    settings.MEDIA_ROOT = str(tmp_path)
    yield tmp_path
    # tmp_path is auto-cleaned, but be tidy if Windows holds locks.
    shutil.rmtree(tmp_path, ignore_errors=True)


def _file(name: str, content: bytes = b"hello", content_type: str = "text/plain"):
    return SimpleUploadedFile(name, content, content_type=content_type)


# ----- form validation -------------------------------------------------------


def test_form_accepts_whitelisted_extension():
    form = AttachmentUploadForm(data={}, files={"file": _file("notes.pdf", b"%PDF-1.4")})
    assert form.is_valid(), form.errors


def test_form_rejects_executable_extension():
    form = AttachmentUploadForm(data={}, files={"file": _file("nasty.exe", b"MZ")})
    assert not form.is_valid()
    assert "Unsupported file type" in str(form.errors["file"])


def test_form_rejects_html_extension():
    # HTML can carry script payloads when served from the same origin.
    form = AttachmentUploadForm(data={}, files={"file": _file("page.html", b"<script>x</script>")})
    assert not form.is_valid()


def test_form_rejects_file_without_extension():
    form = AttachmentUploadForm(data={}, files={"file": _file("README", b"data")})
    assert not form.is_valid()


def test_form_rejects_oversize_file():
    big = b"x" * (MAX_ATTACHMENT_BYTES + 1)
    form = AttachmentUploadForm(data={}, files={"file": _file("big.pdf", big)})
    assert not form.is_valid()
    assert "too large" in str(form.errors["file"]).lower()


# ----- RBAC -----------------------------------------------------------------


def test_viewer_cannot_upload(client, viewer_user, sample_record, media_root):
    client.force_login(viewer_user)
    resp = client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("ok.pdf")},
    )
    assert resp.status_code == 403
    assert IncidentAttachment.objects.count() == 0


def test_anonymous_redirected_from_upload(client, sample_record):
    resp = client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("ok.pdf")},
    )
    assert resp.status_code in (301, 302)
    assert "login" in resp["Location"].lower()


# ----- happy path ------------------------------------------------------------


def test_editor_can_upload_and_attachment_persists(client, editor_user, sample_record, media_root):
    client.force_login(editor_user)
    resp = client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("invoice.pdf", b"%PDF-1.4 hello", content_type="application/pdf")},
    )
    # Successful upload bounces back to the detail page.
    assert resp.status_code in (301, 302)
    assert reverse("incidents:detail", args=[sample_record.pk]) in resp["Location"]

    qs = IncidentAttachment.objects.filter(incident=sample_record)
    assert qs.count() == 1
    a = qs.get()
    assert a.original_name == "invoice.pdf"
    assert a.uploaded_by == editor_user
    assert a.size_bytes > 0
    # The file ended up under MEDIA_ROOT/incident_attachments/<pk>/<uuid>_invoice.pdf
    rel = a.file.name
    assert rel.startswith(f"incident_attachments/{sample_record.pk}/")
    assert rel.endswith("_invoice.pdf")
    assert os.path.exists(a.file.path)


def test_uploaded_path_contains_uuid_not_just_original_name(client, editor_user, sample_record, media_root):
    """Guard against path collisions and predictability — two uploads of the
    same filename must end up at different on-disk paths."""
    client.force_login(editor_user)
    for _ in range(2):
        client.post(
            reverse("incidents:attachment_upload", args=[sample_record.pk]),
            data={"file": _file("same.pdf", b"%PDF-1.4")},
        )
    paths = list(IncidentAttachment.objects.values_list("file", flat=True))
    assert len(paths) == 2
    assert paths[0] != paths[1]


def test_detail_page_lists_attachment(client, editor_user, sample_record, media_root):
    client.force_login(editor_user)
    client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("report.pdf", b"%PDF-1.4")},
    )
    resp = client.get(reverse("incidents:detail", args=[sample_record.pk]))
    assert resp.status_code == 200
    assert b"report.pdf" in resp.content


def test_invalid_upload_renders_error_on_detail_page(client, editor_user, sample_record, media_root):
    client.force_login(editor_user)
    resp = client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("malware.exe", b"MZ")},
    )
    assert resp.status_code == 400
    assert b"Unsupported file type" in resp.content
    assert IncidentAttachment.objects.count() == 0


# ----- delete ---------------------------------------------------------------


def test_editor_can_delete_attachment_and_file_is_removed(client, editor_user, sample_record, media_root):
    client.force_login(editor_user)
    client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("to_delete.pdf", b"%PDF-1.4")},
    )
    a = IncidentAttachment.objects.get()
    disk_path = a.file.path
    assert os.path.exists(disk_path)

    resp = client.post(reverse("incidents:attachment_delete", args=[a.pk]))
    assert resp.status_code in (301, 302)
    assert IncidentAttachment.objects.count() == 0
    assert not os.path.exists(disk_path), "delete() must remove the on-disk file"


def test_viewer_cannot_delete_attachment(client, editor_user, viewer_user, sample_record, media_root):
    # Editor uploads first.
    client.force_login(editor_user)
    client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("keep.pdf", b"%PDF-1.4")},
    )
    a = IncidentAttachment.objects.get()

    # Viewer tries to delete it.
    client.force_login(viewer_user)
    resp = client.post(reverse("incidents:attachment_delete", args=[a.pk]))
    assert resp.status_code == 403
    assert IncidentAttachment.objects.filter(pk=a.pk).exists()


def test_delete_only_accepts_post(client, editor_user, sample_record, media_root):
    client.force_login(editor_user)
    client.post(
        reverse("incidents:attachment_upload", args=[sample_record.pk]),
        data={"file": _file("a.pdf", b"%PDF-1.4")},
    )
    a = IncidentAttachment.objects.get()
    resp = client.get(reverse("incidents:attachment_delete", args=[a.pk]))
    assert resp.status_code == 405  # Method Not Allowed
