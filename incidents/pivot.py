"""Pivot-table builder used by the Analytics page.

Mirrors the original Excel "Analysis" sheet: pick a row dimension, optionally
a column dimension, and get a 2D grid of counts with row/column/grand totals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import Count, QuerySet
from django.db.models.functions import ExtractMonth, ExtractYear

# Available pivot dimensions. The first element of the tuple is either a
# field-path string (used directly in `.values()`) or a callable that returns
# a Django ORM expression to annotate before grouping.
DIMENSIONS: dict[str, tuple[str | Any, str]] = {
    "carrier": ("carrier__name", "Carrier"),
    "issue_type": ("issue_type__name", "Issue type"),
    "causing_party": ("causing_party", "Causing party"),
    "status": ("status", "Status"),
    "country": ("country", "Country"),
    "location": ("location__code", "Location"),
    "year": (lambda: ExtractYear("issue_date"), "Year"),
    "month": (lambda: ExtractMonth("issue_date"), "Month"),
}

# What we render when a value is missing/blank — Django returns None for FK
# joins to null and "" for blank CharFields.
UNKNOWN_LABEL = "(unknown)"

NONE_KEY = "(none)"


def dimension_choices() -> list[tuple[str, str]]:
    """For ``<select>`` widgets — `(value, label)` pairs of available dims."""
    return [(k, v[1]) for k, v in DIMENSIONS.items()]


def build_pivot(
    qs: QuerySet,
    row_key: str,
    col_key: str | None = None,
) -> dict[str, Any]:
    """Group ``qs`` by ``row_key`` (and optionally ``col_key``) and return a
    grid suitable for template rendering.

    Returned dict shape::

        {
          "row_label":    "Carrier",
          "col_label":    "Year",       # None if 1D
          "col_values":   [2024, 2025], # [] if 1D
          "rows": [
            {"label": "Arcese",   "cells": [123, 451], "total": 574},
            {"label": "DSV",      "cells": [200, 225], "total": 425},
            ...
          ],
          "col_totals":   [323, 676],
          "grand_total":  999,
          "max_cell":     451,          # for heatmap shading
          "has_columns":  True,
        }
    """
    if row_key not in DIMENSIONS:
        raise ValueError(f"Unknown row dimension: {row_key!r}")
    treat_as_one_dim = col_key in (None, "", NONE_KEY)
    effective_col_key: str | None = None if treat_as_one_dim else col_key
    if effective_col_key is not None and effective_col_key not in DIMENSIONS:
        raise ValueError(f"Unknown column dimension: {effective_col_key!r}")

    annotations: dict[str, Any] = {}
    row_field = _resolve_dim_field(row_key, "_row", annotations)
    col_field: str | None = None
    if effective_col_key is not None:
        col_field = _resolve_dim_field(effective_col_key, "_col", annotations)

    if annotations:
        qs = qs.annotate(**annotations)

    fields = [row_field] + ([col_field] if col_field else [])
    rows_iter = qs.values(*fields).annotate(n=Count("id"))

    grid: dict[Any, dict[Any, int]] = defaultdict(dict)
    row_set: set = set()
    col_set: set = set()
    for r in rows_iter:
        rv = _label(r[row_field])
        row_set.add(rv)
        if col_field:
            cv = _label(r[col_field])
            col_set.add(cv)
            grid[rv][cv] = r["n"]
        else:
            grid[rv]["__total"] = r["n"]

    row_values = sorted(row_set, key=str)
    col_values = sorted(col_set, key=str) if col_field else []

    out_rows = []
    col_totals: dict[Any, int] = defaultdict(int)
    grand_total = 0
    max_cell = 0
    for rv in row_values:
        cells = []
        if col_field:
            row_total = 0
            for cv in col_values:
                n = grid[rv].get(cv, 0)
                cells.append(n)
                row_total += n
                col_totals[cv] += n
                if n > max_cell:
                    max_cell = n
        else:
            row_total = grid[rv].get("__total", 0)
            if row_total > max_cell:
                max_cell = row_total
        out_rows.append({"label": rv, "cells": cells, "total": row_total})
        grand_total += row_total

    return {
        "row_label": DIMENSIONS[row_key][1],
        "col_label": DIMENSIONS[effective_col_key][1] if effective_col_key else None,
        "col_values": col_values,
        "rows": out_rows,
        "col_totals": [col_totals[cv] for cv in col_values] if col_field else [],
        "grand_total": grand_total,
        "max_cell": max_cell,
        "has_columns": col_field is not None,
        "row_key": row_key,
        "col_key": effective_col_key or NONE_KEY,
    }


def _resolve_dim_field(
    key: str,
    annotation_name: str,
    annotations: dict[str, Any],
) -> str:
    """Return the queryset field name to use for grouping. If the dimension
    requires an ORM expression (e.g. ExtractYear), register it under
    ``annotation_name`` and return that name."""
    src = DIMENSIONS[key][0]
    if isinstance(src, str):
        return src
    # Non-string entries are zero-arg callables returning ORM expressions.
    annotations[annotation_name] = src()
    return annotation_name


def _label(value: Any) -> Any:
    """Normalise None / empty string to a friendly UNKNOWN_LABEL so they
    cluster together in the grid instead of showing up as 'None'."""
    if value is None or value == "":
        return UNKNOWN_LABEL
    return value
