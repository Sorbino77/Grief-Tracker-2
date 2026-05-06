"""Project-wide form helpers."""

from __future__ import annotations

from django import forms


class BootstrapFormMixin:
    """Auto-add Bootstrap 5 classes to every widget on the form.

    Apply by mixing this in to any Form/ModelForm. We map the widget type to
    the right Bootstrap class so that text inputs become ``form-control``,
    selects become ``form-select``, and checkboxes become ``form-check-input``.
    Existing class attrs are preserved (the injected class is appended).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():  # type: ignore[attr-defined]
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput | forms.RadioSelect):
                bs_class = "form-check-input"
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                bs_class = "form-select"
            else:
                bs_class = "form-control"
            if bs_class not in existing.split():
                widget.attrs["class"] = (existing + " " + bs_class).strip()
