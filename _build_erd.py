# -*- coding: utf-8 -*-
"""Render an ER diagram of the Grief Tracker (ShipTrack) data model to PNG."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

NAVY = "#1B2A4A"
ACCENT = "#2E86AB"
GOLD = "#B7791F"
GREEN = "#2E7D32"
RED = "#C0392B"
MUTED = "#6B7280"
TEXT = "#23262B"
BORDER = "#C7D0DA"
SEP = "#EDF1F5"

H = 4.2     # header height
R = 2.55    # row height

fig = plt.figure(figsize=(18.8, 12.2))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 188)
ax.set_ylim(0, 122)
ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor("white")

# ---- title ----
ax.text(5, 118.5, "Grief Tracker — Data Model", color=NAVY, fontsize=25,
        fontweight="bold", ha="left", va="center")
ax.text(5, 114.3, "Entity–relationship diagram  ·  Django models (accounts + incidents apps)",
        color=MUTED, fontsize=12, ha="left", va="center")
ax.plot([5, 183], [112.2, 112.2], color=ACCENT, lw=1.6)


def entity(x, top, w, title, rows, note=None):
    n = len(rows)
    h = H + n * R
    bottom = top - h
    ax.add_patch(Rectangle((x + 0.6, bottom - 0.6), w, h, facecolor="#00000014",
                            edgecolor="none", zorder=1))
    ax.add_patch(Rectangle((x, bottom), w, h, facecolor="white", edgecolor=BORDER,
                           lw=1.1, zorder=2))
    ax.add_patch(Rectangle((x, top - H), w, H, facecolor=NAVY, edgecolor=NAVY,
                           lw=0, zorder=3))
    ax.text(x + w / 2, top - H / 2, title, color="white", fontsize=12.5,
            fontweight="bold", ha="center", va="center", zorder=4)
    ax.plot([x, x + w], [top - H, top - H], color=ACCENT, lw=1.4, zorder=4)
    anchors = {"_left": x, "_right": x + w, "_top": top, "_bottom": bottom,
               "_cy": (top - H + bottom) / 2, "rows": {}}
    y = top - H
    for i, (fname, ftype, tag) in enumerate(rows):
        yc = y - R / 2
        anchors["rows"][fname] = yc
        if i > 0:
            ax.plot([x + 0.4, x + w - 0.4], [y, y], color=SEP, lw=0.6, zorder=3)
        if tag:
            tagcolor = {"PK": GOLD, "FK": ACCENT, "U": GREEN}[tag]
            ax.text(x + 1.8, yc, tag, color=tagcolor, fontsize=7.0,
                    fontweight="bold", ha="left", va="center", zorder=4)
        ax.text(x + 9.0, yc, fname, color=TEXT, fontsize=8.7, ha="left", va="center",
                fontweight=("bold" if tag == "PK" else "normal"), zorder=4)
        ax.text(x + w - 1.8, yc, ftype, color=MUTED, fontsize=7.3, ha="right",
                va="center", style="italic", zorder=4)
        y -= R
    if note:
        ax.text(x + w / 2, bottom - 1.5, note, color=ACCENT, fontsize=7.4,
                ha="center", va="top", style="italic", fontweight="bold", zorder=4)
    return anchors


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def connect(child, parent, color, dashed=False, rad=0.0, c_card="*", p_card="1"):
    ls = (0, (5, 3)) if dashed else "-"
    ax.add_patch(FancyArrowPatch(child, parent, arrowstyle="-|>", mutation_scale=13,
                 connectionstyle=f"arc3,rad={rad}", color=color, lw=1.7,
                 linestyle=ls, zorder=1.6, shrinkA=2, shrinkB=3))
    bb = dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9)
    pc = lerp(child, parent, 0.11)
    pp = lerp(child, parent, 0.89)
    ax.text(pc[0], pc[1], c_card, color=color, fontsize=8.5, fontweight="bold",
            ha="center", va="center", zorder=5, bbox=bb)
    ax.text(pp[0], pp[1], p_card, color=color, fontsize=8.5, fontweight="bold",
            ha="center", va="center", zorder=5, bbox=bb)


# ---- reference data (left column) ----
carrier = entity(5, 108, 42, "Carrier", [
    ("id", "bigint", "PK"),
    ("name", "varchar(100)", "U"),
    ("is_active", "bool", ""),
    ("created_at", "datetime", ""),
    ("updated_at", "datetime", ""),
])
issuetype = entity(5, 87, 42, "IssueType", [
    ("id", "bigint", "PK"),
    ("name", "varchar(120)", "U"),
    ("description", "varchar(255)", ""),
    ("is_active", "bool", ""),
    ("created_at", "datetime", ""),
    ("updated_at", "datetime", ""),
])
location = entity(5, 63.5, 42, "Location", [
    ("id", "bigint", "PK"),
    ("code", "varchar(50)", "U"),
    ("facility_name", "varchar(200)", ""),
    ("city", "varchar(100)", ""),
    ("country", "char(2)", ""),
    ("is_active", "bool", ""),
    ("created_at", "datetime", ""),
    ("updated_at", "datetime", ""),
])

# ---- central hub ----
incident = entity(68, 95.5, 50, "Incident", [
    ("id", "bigint", "PK"),
    ("primary_ref", "varchar(64)", ""),
    ("ship_id", "varchar(64)", ""),
    ("transport_order_ref", "varchar(64)", ""),
    ("supplier_name", "varchar(255)", ""),
    ("country", "char(2)", ""),
    ("location_id", "→ Location", "FK"),
    ("carrier_id", "→ Carrier", "FK"),
    ("issue_type_id", "→ IssueType", "FK"),
    ("issue_date", "date", ""),
    ("image_available", "enum", ""),
    ("causing_party", "enum", ""),
    ("resolve_date", "date null", ""),
    ("status", "enum", ""),
    ("note", "text", ""),
    ("created_by_id", "→ User", "FK"),
    ("updated_by_id", "→ User", "FK"),
    ("created_at", "datetime", ""),
    ("updated_at", "datetime", ""),
], note="UNIQUE (primary_ref, issue_type)")

# ---- right column ----
user = entity(135, 108, 46, "User", [
    ("id", "bigint", "PK"),
    ("username", "varchar(150)", "U"),
    ("email", "varchar(254)", "U"),
    ("role", "enum", ""),
    ("is_staff", "bool", ""),
    ("is_active", "bool", ""),
    ("is_superuser", "bool", ""),
    ("last_login", "datetime", ""),
    ("date_joined", "datetime", ""),
    ("password", "varchar(128)", ""),
], note="extends Django AbstractUser")
attach = entity(135, 71, 46, "IncidentAttachment", [
    ("id", "bigint", "PK"),
    ("incident_id", "→ Incident", "FK"),
    ("file", "varchar(255)", ""),
    ("original_name", "varchar(255)", ""),
    ("content_type", "varchar(120)", ""),
    ("size_bytes", "int", ""),
    ("uploaded_by_id", "→ User", "FK"),
    ("uploaded_at", "datetime", ""),
])

# ---- relationships (colour = on_delete) ----
# Incident -> reference data : PROTECT (navy solid) — fanned out to avoid a knot
connect((incident["_left"], incident["rows"]["carrier_id"]),
        (carrier["_right"], carrier["_cy"]), NAVY, rad=-0.22)
connect((incident["_left"], incident["rows"]["issue_type_id"]),
        (issuetype["_right"], issuetype["_cy"]), NAVY, rad=-0.06)
connect((incident["_left"], incident["rows"]["location_id"]),
        (location["_right"], location["_cy"]), NAVY, rad=0.22)
# Incident -> User : SET NULL (grey dashed)
connect((incident["_right"], incident["rows"]["created_by_id"]),
        (user["_left"], user["_bottom"] + 6), MUTED, dashed=True, rad=0.12)
connect((incident["_right"], incident["rows"]["updated_by_id"]),
        (user["_left"], user["_bottom"] + 2.5), MUTED, dashed=True, rad=0.18)
# Attachment -> Incident : CASCADE (red solid)
connect((attach["_left"], attach["rows"]["incident_id"]),
        (incident["_right"], incident["rows"]["note"]), RED, rad=-0.05)
# Attachment -> User : SET NULL (grey dashed)
connect((attach["_right"], attach["rows"]["uploaded_by_id"]),
        (user["_right"], user["_bottom"]), MUTED, dashed=True, rad=-0.45)


# ---- legend box ----
def textbox(x, y, w, h, title):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="#F7F9FC", edgecolor=BORDER,
                           lw=1.0, zorder=2))
    ax.add_patch(Rectangle((x, y + h - 3.6), w, 3.6, facecolor=NAVY, edgecolor=NAVY,
                           zorder=3))
    ax.text(x + 2, y + h - 1.8, title, color="white", fontsize=9.5,
            fontweight="bold", ha="left", va="center", zorder=4)


# Legend (below the central hub)
lx, ly, lw, lh = 68, 8.5, 60, 31
textbox(lx, ly, lw, lh, "Legend")
yy = ly + lh - 7
for tag, col, lab in [("PK", GOLD, "primary key"), ("FK", ACCENT, "foreign key"),
                      ("U", GREEN, "unique")]:
    ax.text(lx + 3, yy, tag, color=col, fontsize=8.5, fontweight="bold",
            ha="left", va="center", zorder=4)
    ax.text(lx + 9, yy, lab, color=TEXT, fontsize=8.5, ha="left", va="center", zorder=4)
    yy -= 3.1
yy -= 0.6
for col, dashed, lab in [(NAVY, False, "on_delete = PROTECT"),
                         (RED, False, "on_delete = CASCADE"),
                         (MUTED, True, "on_delete = SET NULL")]:
    ls = (0, (5, 3)) if dashed else "-"
    ax.plot([lx + 3, lx + 13], [yy, yy], color=col, lw=2.0, linestyle=ls, zorder=4)
    ax.text(lx + 15, yy, lab, color=TEXT, fontsize=8.5, ha="left", va="center", zorder=4)
    yy -= 3.1
ax.text(lx + 3, yy - 0.2, "Cardinality:  1 —— *  (one-to-many)", color=TEXT,
        fontsize=8.5, ha="left", va="center", zorder=4)

# Enumerations box (below the reference tables)
ex, ey, ew, eh = 5, 6.5, 56, 31
textbox(ex, ey, ew, eh, "Enumerations (choices)")
enums = [
    ("Role", "admin · editor · viewer"),
    ("Status", "ONGOING · RESOLVED"),
    ("CausingParty", "SUPPLIER · CARRIER · MIXED · UNKNOWN"),
    ("ImageAvailable", "YES · NO · NA"),
]
yy = ey + eh - 7.5
for name, vals in enums:
    ax.text(ex + 3, yy, name, color=NAVY, fontsize=8.6, fontweight="bold",
            ha="left", va="center", zorder=4)
    ax.text(ex + 3, yy - 2.5, vals, color=MUTED, fontsize=8.0, ha="left",
            va="center", zorder=4)
    yy -= 6.0

OUT = r"C:\Users\koenj\Python Projecten J2\Grief Tracker 2\Grief Tracker - Data Model.png"
fig.savefig(OUT, dpi=200, facecolor="white")
print("saved:", OUT)
