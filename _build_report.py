# -*- coding: utf-8 -*-
"""Generate a polished Grief Tracker final report as .docx."""
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------------------------------------------------------------- palette ----
NAVY = "1B2A4A"
ACCENT = "2E86AB"
ROW_ALT = "EEF3F8"
LABEL = "DCE6F1"
LIGHT = "F4F6F9"
GREEN = "2E7D32"
AMBER = "B7791F"
GREY = "5B6675"
TEXT = "23262B"
MUTED = "6B7280"
LIGHTBORDER = "D6DCE5"
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def C(hexstr):
    return RGBColor.from_string(hexstr)


# ---------------------------------------------------------------- helpers ----
def set_run_font(run, name):
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    rfonts = rPr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rPr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), name)


def set_style_font(style, name):
    el = style.element
    rPr = el.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        el.append(rPr)
    rfonts = rPr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rPr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), name)


P_AFTER_PBDR = ("w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
                "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
                "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
                "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
                "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
                "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")


def _border_el(side, color, sz, space):
    e = OxmlElement("w:" + side)
    e.set(qn("w:val"), "single")
    e.set(qn("w:sz"), str(sz))
    e.set(qn("w:space"), str(space))
    e.set(qn("w:color"), color)
    return e


def para_border(p, side="bottom", color=ACCENT, sz=18, space=6):
    pPr = p._p.get_or_add_pPr()
    pbdr = pPr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr")
        pPr.insert_element_before(pbdr, *P_AFTER_PBDR)
    pbdr.append(_border_el(side, color, sz, space))


def para_shade(p, fill):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.insert_element_before(shd, *P_AFTER_PBDR[1:])


TC_SHD_SUCC = ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFit", "w:vAlign",
               "w:hideMark", "w:tcPrChange")


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    for existing in tcPr.findall(qn("w:shd")):
        tcPr.remove(existing)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.insert_element_before(shd, *TC_SHD_SUCC)


def cell_left_accent(cell, color=ACCENT, sz=28):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    borders.append(_border_el("left", color, sz, 0))
    tcPr.insert_element_before(borders, "w:shd", "w:noWrap", "w:tcMar",
                               "w:textDirection", "w:tcFit", "w:vAlign",
                               "w:hideMark", "w:tcPrChange")


def tbl_borders(table, color=LIGHTBORDER, sz=4):
    tblPr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b.append(_border_el(edge, color, sz, 0))
    tblPr.insert_element_before(b, "w:shd", "w:tblLayout", "w:tblCellMar",
                                "w:tblLook", "w:tblCaption", "w:tblDescription",
                                "w:tblPrChange")


def tbl_cell_margins(table, top=60, bottom=60, left=120, right=120):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement("w:" + side)
        e.set(qn("w:w"), str(val))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblPr.insert_element_before(mar, "w:tblLook", "w:tblCaption", "w:tblDescription",
                                "w:tblPrChange")


def tbl_fixed(table, total_mm):
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.insert_element_before(layout, "w:tblCellMar", "w:tblLook", "w:tblCaption",
                                "w:tblDescription", "w:tblPrChange")
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.insert_element_before(tblW, "w:jc", "w:tblCellSpacing", "w:tblInd",
                                    "w:tblBorders", "w:shd", "w:tblLayout",
                                    "w:tblCellMar", "w:tblLook", "w:tblCaption",
                                    "w:tblDescription", "w:tblPrChange")
    tblW.set(qn("w:w"), str(int(total_mm * 56.6929)))
    tblW.set(qn("w:type"), "dxa")


def add_field_runs(paragraph, instr, placeholder=None, size=9, color=MUTED, italic=False):
    r1 = paragraph.add_run()
    fb = OxmlElement("w:fldChar")
    fb.set(qn("w:fldCharType"), "begin")
    r1._r.append(fb)
    r2 = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r2._r.append(it)
    r3 = paragraph.add_run()
    fs = OxmlElement("w:fldChar")
    fs.set(qn("w:fldCharType"), "separate")
    r3._r.append(fs)
    if placeholder is not None:
        rp = paragraph.add_run(placeholder)
        rp.italic = italic
        rp.font.size = Pt(size)
        rp.font.color.rgb = C(color)
        set_run_font(rp, "Arial")
    r4 = paragraph.add_run()
    fe = OxmlElement("w:fldChar")
    fe.set(qn("w:fldCharType"), "end")
    r4._r.append(fe)
    for rr in (r1, r2, r3, r4):
        rr.font.size = Pt(size)
        rr.font.color.rgb = C(color)
        set_run_font(rr, "Arial")


# ---------------------------------------------------------------- document ----
doc = Document()

# update TOC field on open (insert in schema-correct position within CT_Settings)
settings = doc.settings.element
uf = OxmlElement("w:updateFields")
uf.set(qn("w:val"), "true")
settings.insert_element_before(
    uf, "w:hdrShapeDefaults", "w:footnotePr", "w:endnotePr", "w:compat", "w:docVars",
    "w:rsids", "w:attachedSchema", "w:themeFontLang", "w:clrSchemeMapping",
    "w:doNotIncludeSubdocsInStats", "w:doNotAutoCompressPictures", "w:forceUpgrade",
    "w:captions", "w:readModeInkLockDown", "w:smartTagType", "w:shapeDefaults",
    "w:doNotEmbedSmartTags", "w:decimalSymbol", "w:listSeparator",
)

# python-docx's default settings.xml ships a <w:zoom/> without the required
# percent attribute; set it so the file validates cleanly.
_zoom = settings.find(qn("w:zoom"))
if _zoom is not None and _zoom.get(qn("w:percent")) is None:
    _zoom.set(qn("w:percent"), "100")

# Normal style
normal = doc.styles["Normal"]
normal.font.name = "Arial"
set_style_font(normal, "Arial")
normal.font.size = Pt(10.5)
normal.font.color.rgb = C(TEXT)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.18


def style_heading(name, size, color, before, after):
    st = doc.styles[name]
    st.font.name = "Arial"
    set_style_font(st, "Arial")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = C(color)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True


style_heading("Heading 1", 18, NAVY, 4, 6)
style_heading("Heading 2", 13.5, ACCENT, 12, 4)
style_heading("Heading 3", 11.5, NAVY, 8, 2)

# page geometry (A4)
sec = doc.sections[0]
sec.page_width = Mm(210)
sec.page_height = Mm(297)
sec.top_margin = Mm(22)
sec.bottom_margin = Mm(20)
sec.left_margin = Mm(22)
sec.right_margin = Mm(22)
CW = 166  # content width mm

# ---- header / footer (skip on cover) ----
sec.different_first_page_header_footer = True

hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hr = hp.add_run("ShipTrack  ·  Shipment Incident Tracker")
hr.font.size = Pt(8.5)
hr.font.color.rgb = C(MUTED)
set_run_font(hr, "Arial")
para_border(hp, "bottom", LIGHTBORDER, 6, 6)

fp = sec.footer.paragraphs[0]
fp.paragraph_format.tab_stops.add_tab_stop(Mm(CW), WD_TAB_ALIGNMENT.RIGHT)
para_border(fp, "top", LIGHTBORDER, 6, 6)
fr = fp.add_run("Grief Tracker  ·  Final Report")
fr.font.size = Pt(8.5)
fr.font.color.rgb = C(MUTED)
set_run_font(fr, "Arial")
tabrun = fp.add_run("\t")
tabrun.font.size = Pt(8.5)
add_field_runs(fp, "PAGE", placeholder="1")
mid = fp.add_run(" / ")
mid.font.size = Pt(8.5)
mid.font.color.rgb = C(MUTED)
set_run_font(mid, "Arial")
add_field_runs(fp, "NUMPAGES", placeholder="1")


# ---------------------------------------------------------------- builders ----
def body(text, after=6, size=None, color=None, italic=False, align=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = C(color)
    r.italic = italic
    p.paragraph_format.space_after = Pt(after)
    if align:
        p.alignment = align
    return p


def rich(parts, style=None, after=6):
    p = doc.add_paragraph(style=style)
    for part in parts:
        if isinstance(part, str):
            p.add_run(part)
        else:
            txt, opt = part
            r = p.add_run(txt)
            if opt.get("b"):
                r.bold = True
            if opt.get("i"):
                r.italic = True
            if opt.get("color"):
                r.font.color.rgb = C(opt["color"])
            if opt.get("size"):
                r.font.size = Pt(opt["size"])
    p.paragraph_format.space_after = Pt(after)
    return p


def bullet(parts):
    return rich(parts, style="List Bullet", after=3)


def h1(text, status=None, status_color=None):
    p = doc.add_heading(text, level=1)
    p.paragraph_format.page_break_before = True
    para_border(p, "bottom", ACCENT, 16, 6)
    if status:
        sp = doc.add_paragraph()
        r = sp.add_run("STATUS  ")
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = C(MUTED)
        r2 = sp.add_run(status)
        r2.bold = True
        r2.font.size = Pt(10)
        r2.font.color.rgb = C(status_color)
        sp.paragraph_format.space_after = Pt(8)
    return p


def h2(text):
    return doc.add_heading(text, level=2)


def make_table(data, widths, header=True, font_size=9.5, header_fill=NAVY):
    rows, cols = len(data), len(widths)
    t = doc.add_table(rows=rows, cols=cols)
    t.allow_autofit = False
    tbl_fixed(t, sum(widths))
    tbl_borders(t)
    tbl_cell_margins(t)
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci)
            cell.width = Mm(widths[ci])
            para = cell.paragraphs[0]
            para.paragraph_format.space_after = Pt(2)
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.line_spacing = 1.05
            txt = val["text"] if isinstance(val, dict) else str(val)
            run = para.add_run(txt)
            run.font.size = Pt(font_size)
            set_run_font(run, "Arial")
            if header and ri == 0:
                run.bold = True
                run.font.color.rgb = WHITE
                shade_cell(cell, header_fill)
            else:
                if isinstance(val, dict):
                    if val.get("b"):
                        run.bold = True
                    if val.get("color"):
                        run.font.color.rgb = C(val["color"])
                if ri != 0 and ri % 2 == 0:
                    shade_cell(cell, ROW_ALT)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    return t


def code_block(lines):
    t = doc.add_table(rows=1, cols=1)
    t.allow_autofit = False
    tbl_fixed(t, CW)
    tbl_borders(t, LIGHTBORDER, 4)
    tbl_cell_margins(t, 100, 100, 160, 160)
    cell = t.cell(0, 0)
    cell.width = Mm(CW)
    shade_cell(cell, LIGHT)
    first = True
    for ln in lines:
        p = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(ln)
        r.font.size = Pt(8.5)
        r.font.color.rgb = C(TEXT)
        set_run_font(r, "Consolas")
    return t


def spacer(pt=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run("")
    r.font.size = Pt(pt)
    return p


# ============================================================== COVER PAGE ====
spacer(18)
eb = doc.add_paragraph()
ebr = eb.add_run("F I N A L   R E P O R T")
ebr.bold = True
ebr.font.size = Pt(11)
ebr.font.color.rgb = C(ACCENT)
eb.paragraph_format.space_after = Pt(6)

# banner
bt = doc.add_table(rows=1, cols=1)
bt.allow_autofit = False
tbl_fixed(bt, CW)
tbl_cell_margins(bt, 220, 240, 240, 200)
bcell = bt.cell(0, 0)
bcell.width = Mm(CW)
shade_cell(bcell, NAVY)
bp = bcell.paragraphs[0]
bp.paragraph_format.space_after = Pt(2)
tr = bp.add_run("Grief Tracker")
tr.bold = True
tr.font.size = Pt(34)
tr.font.color.rgb = WHITE
set_run_font(tr, "Arial")
sp1 = bcell.add_paragraph()
sp1.paragraph_format.space_after = Pt(0)
sr = sp1.add_run("Shipment Incident Tracking Platform")
sr.font.size = Pt(15)
sr.font.color.rgb = WHITE
set_run_font(sr, "Arial")
sp2 = bcell.add_paragraph()
sp2.paragraph_format.space_before = Pt(4)
sp2.paragraph_format.space_after = Pt(0)
sr2 = sp2.add_run("Application codename: ShipTrack   ·   Django + Django REST Framework")
sr2.italic = True
sr2.font.size = Pt(10)
sr2.font.color.rgb = C("Bcd0e6") if False else C("C7D6EA")
set_run_font(sr2, "Arial")

spacer(14)

# metadata
meta = [
    ["Field", "Detail"],
    ["Author", "Koen Janssens"],
    ["Student number / class", "—  [to be completed]"],
    ["Course / module", "—  [to be completed]"],
    ["Institution", "—  [to be completed]"],
    ["Supervisor / assessor", "—  [to be completed]"],
    ["Version", "1.0"],
    ["Date", "28 May 2026"],
    ["Deadline", "31 March 2026"],
    ["Repository", "Git (branch master) · CI/CD via GitHub Actions"],
]
mt = make_table(meta, [46, 120], header=True, font_size=10)
# shade label column
for ri in range(1, len(meta)):
    c0 = mt.cell(ri, 0)
    shade_cell(c0, LABEL)
    c0.paragraphs[0].runs[0].bold = True

spacer(12)

# summary callout
sumt = doc.add_table(rows=1, cols=1)
sumt.allow_autofit = False
tbl_fixed(sumt, CW)
tbl_cell_margins(sumt, 120, 120, 160, 140)
scell = sumt.cell(0, 0)
scell.width = Mm(CW)
shade_cell(scell, LIGHT)
cell_left_accent(scell, ACCENT, 30)
sttl = scell.paragraphs[0]
sttl.paragraph_format.space_after = Pt(3)
sr3 = sttl.add_run("Summary")
sr3.bold = True
sr3.font.size = Pt(11)
sr3.font.color.rgb = C(NAVY)
set_run_font(sr3, "Arial")
sbody = scell.add_paragraph()
sbody.paragraph_format.space_after = Pt(0)
sbr = sbody.add_run(
    "Grief Tracker replaces a legacy Excel workflow with a secure, multi-user web "
    "application and REST API for logging and analysing shipment incidents. Stage 1 "
    "(foundation) and the bulk of Stage 2 (visibility) are implemented and deployable; "
    "predictive Stage 3 features are designed as follow-up work."
)
sbr.font.size = Pt(10)
sbr.font.color.rgb = C(TEXT)
set_run_font(sbr, "Arial")

# ================================================================ TOC PAGE ====
toc_title = doc.add_paragraph()
toc_title.paragraph_format.page_break_before = True
toc_title.paragraph_format.space_after = Pt(10)
ttr = toc_title.add_run("Contents")
ttr.bold = True
ttr.font.size = Pt(20)
ttr.font.color.rgb = C(NAVY)
set_run_font(ttr, "Arial")
para_border(toc_title, "bottom", ACCENT, 16, 6)

tocp = doc.add_paragraph()
add_field_runs(tocp, 'TOC \\o "1-3" \\h \\z \\u',
               placeholder="Right-click here and choose “Update Field” to build the table of contents.",
               size=10, color=MUTED, italic=True)

# ============================================================== 1. INTRO ======
h1("1. Introduction")
body("The Grief Tracker application was developed to replace an Excel-based workflow with a "
     "structured, multi-user, and scalable system. In logistics operations, shipment incidents "
     "(“grief”) — damage, missing or wrong labels, mis-routed deliveries, supplier or "
     "carrier faults — were historically logged in a shared spreadsheet (the legacy "
     "Kuehne+Nagel “Grief” workbook). That approach did not scale: it offered no access "
     "control, no audit trail, no validation, poor concurrent editing, and no reliable way to "
     "analyse or integrate the data.")
body("The goal is to centralise logistics-incident data and make it accessible through both a "
     "server-rendered web application and a REST API, while preserving a smooth migration path: "
     "the importer still accepts the legacy spreadsheet column headers, so existing data flows in "
     "unchanged.")
rich([("On the name. ", {"b": True, "color": NAVY}),
      ("“Grief Tracker” is the project title; the application and codebase are named "
       "ShipTrack. The word “grief” is inherited from the legacy K&N workbook, where it "
       "is the in-house term for shipment claims/incidents. Both names refer to the same system "
       "throughout this report.")])
h2("Target users")
body("Operational staff who log and resolve incidents (Editors), managers who review and analyse "
     "them (Viewers), and administrators who manage users and reference data (Admins).")

# ============================================================ 2. OBJECTIVE ====
h1("2. Project Objective")
body("The objective is to build a Django-based backend that imports Excel data, stores it in a "
     "relational database, and exposes it via a REST API and a web UI. The system must be "
     "reliable, secure, and easy to extend toward analytics and, later, intelligent features.")
h2("2.1 Functional requirements (MoSCoW)")
bullet([("Must have — ", {"b": True}),
        ("incident CRUD; reference data (carrier, issue type, location); spreadsheet import "
         "(.xlsx/.xlsm/.csv) incl. legacy headers; REST API with filter/search/order; multi-user "
         "authentication with role-based access; admin interface.")])
bullet([("Should have — ", {"b": True}),
        ("analytics/pivot views mirroring the old Excel “Analysis” sheet; file "
         "attachments per incident; idempotent re-import; dry-run validation.")])
bullet([("Could have — ", {"b": True}),
        ("KPI/statistics JSON endpoints; richer charting dashboard; alerts/notifications; "
         "single sign-on (Google/Microsoft).")])
bullet([("Won’t have (this phase) — ", {"b": True}),
        ("predictive/ML features (deferred to Stage 3).")])
h2("2.2 Non-functional requirements")
body("Reliability (idempotent import, atomic transactions), security (OWASP Top 10 hardening), "
     "maintainability (typed code, linting, automated tests, CI), portability (Docker, one-command "
     "launch), and performance adequate for the expected data volume (tens of thousands of rows; "
     "the importer is capped at 200,000 rows per run).")

# ====================================================== 3. ARCHITECTURE =======
h1("3. System Architecture & Data Model")
h2("3.1 Architecture")
body("The system is a server-rendered Django application with a REST API layer, built from two "
     "domain apps inside one project:")
code_block([
    "shiptrack/     Django project (settings, URLs, WSGI/ASGI)",
    "accounts/      Custom user model, roles, permission helpers, auth views",
    "incidents/     Domain models, HTML views, forms, REST API, importer, pivot",
    "templates/     Server-rendered HTML (Bootstrap 5, no CDN dependency)",
    "static/        Vendored Bootstrap + small custom CSS / JS",
    "tests/         pytest suite",
    "nginx/         Reverse-proxy config",
    "scripts/       Operator helpers and launchers",
])
spacer(4)
body("Runtime components: Django 5.0 and Django REST Framework 3.15, PostgreSQL (16 in the "
     "reference deployment; SQLite for tests/dev), Redis (cache; future Celery broker), gunicorn "
     "behind nginx, WhiteNoise for static files — all containerised with Docker. Dependencies "
     "are managed with uv (pyproject.toml + uv.lock).")
h2("3.2 Data model")
bullet([("Incident — ", {"b": True}),
        ("primary reference, shipment ID, transport-order ref, supplier, ISO-2 country, FK to "
         "location/carrier/issue type, issue date, image-available flag, causing party "
         "(Supplier/Carrier/Mixed/Unknown), resolve date, status (Ongoing/Resolved), free-text "
         "note, plus audit fields. A unique constraint on (primary_ref, issue_type) keeps "
         "re-imports idempotent; DB indexes support status/carrier/issue-date queries.")])
bullet([("Reference data — ", {"b": True}),
        ("Carrier, IssueType, Location (each with active flags), created on demand during import.")])
bullet([("IncidentAttachment — ", {"b": True}),
        ("files (photos, PDFs, supplier emails) stored under a per-incident, UUID-prefixed path "
         "with original name, content type, and size captured.")])
bullet([("User — ", {"b": True}),
        ("custom AbstractUser with a role field (Admin/Editor/Viewer) and a unique, required email "
         "(for SSO).")])

# ====================================================== 4. STAGE 1 ============
h1("4. Development Stage 1 — Foundation", status="Implemented", status_color=GREEN)
body("Stage 1 replaces Excel with a functional system. All five deliverables are complete, plus "
     "two additions (custom user roles and file attachments).")
make_table([
    ["#", "Deliverable", "Status"],
    ["1", "Django backend and database models (audit fields, indexes, idempotency constraint)",
     {"text": "Done", "color": GREEN, "b": True}],
    ["2", "Spreadsheet import — .xlsx/.xlsm/.csv, CLI + UI, forgiving headers (incl. legacy "
          "K&N), atomic, idempotent update_or_create, dry-run, per-row errors, row cap",
     {"text": "Done", "color": GREEN, "b": True}],
    ["3", "REST API — /api/v1/, filter/search/order, pagination, throttling, role enforcement, "
          "session + token auth",
     {"text": "Done", "color": GREEN, "b": True}],
    ["4", "Admin interface (incidents + accounts registered)",
     {"text": "Done", "color": GREEN, "b": True}],
    ["5", "Code-quality tooling — ruff, mypy (django/drf stubs), bandit, pytest + coverage",
     {"text": "Done", "color": GREEN, "b": True}],
], [10, 122, 34], font_size=9.5)

# ====================================================== 5. STAGE 2 ============
h1("5. Development Stage 2 — Visibility", status="Partially implemented", status_color=AMBER)
body("Stage 2 introduces dashboards and operational insight. Authentication and the analytics "
     "pivot are implemented; dedicated KPI endpoints and alerts remain planned.")
make_table([
    ["#", "Deliverable", "Status"],
    ["1", "KPI and statistics endpoints — breakdowns computed on the analytics page; "
          "machine-readable JSON KPI endpoints still to do",
     {"text": "Partial", "color": AMBER, "b": True}],
    ["2", "Dashboard / analytics — interactive pivot (8 dimensions, totals, heatmap shading) "
          "mirroring the Excel “Analysis” sheet; richer charting to follow",
     {"text": "Implemented", "color": GREEN, "b": True}],
    ["3", "Alerts and notifications",
     {"text": "Planned", "color": GREY, "b": True}],
    ["4", "Authentication — allauth login, RBAC (Admin/Editor/Viewer), axes lockout, Argon2, "
          "12-char policy, optional Google/Microsoft SSO",
     {"text": "Implemented", "color": GREEN, "b": True}],
], [10, 122, 34], font_size=9.5)

# ====================================================== 6. STAGE 3 ============
h1("6. Development Stage 3 — Smart System", status="Planned (design only)", status_color=GREY)
body("Stage 3 focuses on predictive and intelligent features. The data already captured supports "
     "these directly.")
make_table([
    ["#", "Feature", "Basis in existing data"],
    ["1", "Delay prediction", "issue_date → resolve_date duration; carrier/issue/location features"],
    ["2", "Anomaly detection", "spikes per carrier / issue type / location over time"],
    ["3", "AI-based classification", "auto-suggest issue_type / causing_party from the free-text note"],
    ["4", "Recommendations", "suggested resolution actions from historical resolutions"],
], [10, 50, 106], font_size=9.5)
spacer(4)
body("Intended stack: Celery + Redis for asynchronous jobs and scikit-learn for the initial "
     "models. Redis is already wired in as the cache backend, so adding a broker is incremental.")

# ====================================================== 7. SECURITY ===========
h1("7. Security (OWASP Top 10, 2021)")
body("Security is treated as a first-class requirement. Coverage of the OWASP Top 10:")
make_table([
    ["Category", "Mitigation in Grief Tracker"],
    ["A01 Broken Access Control", "@role_required, DRF permission classes, login required everywhere except /healthz/"],
    ["A02 Cryptographic Failures", "Argon2 hashing, HSTS, secure/HttpOnly cookies, secrets via environment"],
    ["A03 Injection", "ORM-only queries, parameterised search, Django auto-escaping"],
    ["A04 Insecure Design", "deny-by-default permissions, atomic + dry-run importer"],
    ["A05 Security Misconfiguration", "DEBUG off by default, no default secret in prod, CSP, Permissions-Policy, X-Frame-Options DENY, non-root container, internal-only DB network"],
    ["A06 Vulnerable Components", "pinned pyproject.toml / uv.lock, Dependabot, slim base image"],
    ["A07 Identification & Auth Failures", "django-axes lockout, 12-char password policy, allauth rate limits"],
    ["A08 Data Integrity Failures", "CSRF middleware, signed sessions, idempotent importer"],
    ["A09 Logging & Monitoring", "structured stdout logging; axes records lockouts"],
    ["A10 SSRF", "no user-supplied outbound URLs"],
], [54, 112], font_size=9)
spacer(4)
body("Uploads (attachments and import files) are constrained by extension, content-type, and a "
     "25 MB size limit, and the relevant views are rate-limited.")

# ====================================================== 8. TESTING ============
h1("8. Testing & Quality Assurance")
body("A pytest suite covers models, HTML views, RBAC, the REST API, the importer, the "
     "pivot/analytics logic, attachments, user creation, and security behaviour (security headers, "
     "CSRF, password validators). Tests run against an in-memory SQLite database, so no Postgres "
     "is required locally. Static quality is enforced by ruff, mypy (typed with django/drf stubs), "
     "and bandit — all run in CI on every push and pull request.")

# ====================================================== 9. DEPLOYMENT =========
h1("9. Deployment & DevOps (CI/CD)")
bullet([("ci.yml ", {"b": True}),
        ("(every push/PR): ruff check + format check, bandit, mypy, pytest --cov, "
         "manage.py check --deploy against a prod-like environment, and a Docker build that "
         "verifies /healthz/ returns 200.")])
bullet([("release.yml ", {"b": True}),
        ("(push to main and v*.*.* tags): builds multi-arch images (amd64 + arm64), pushes to "
         "GHCR, and generates SBOM + provenance attestations.")])
bullet([("Dependabot — ", {"b": True}),
        ("weekly dependency, GitHub Actions, and Docker base-image updates (grouped to reduce PR "
         "noise).")])
bullet([("Deployment options — ", {"b": True}),
        ("one-click Render (render.yaml), Fly.io (fly.toml), a prebuilt GHCR image, or self-hosted "
         "docker compose up (Postgres + Redis + Django + nginx). A Windows start.bat / make up "
         "gives a one-command local launch.")])

# ====================================================== 10. ROADMAP ===========
h1("10. Technical Roadmap")
body("The system is built on Django, Django REST Framework, PostgreSQL, and Redis. Planned "
     "improvements: dedicated KPI/statistics JSON endpoints and a richer charting dashboard "
     "(Stage 2 completion); alerts/notifications; Celery workers (Redis broker) for asynchronous "
     "import and scheduled jobs; and machine-learning integration for the Stage 3 features. A "
     "production checklist (TLS termination, DEBUG=False, HSTS, restricted hosts, regular pg_dump "
     "backups) governs public exposure.")

# ====================================================== 11. PLANNING ==========
h1("11. Planning and Deadline")
body("Development followed a structured, stage-based weekly plan toward the 31 March 2026 deadline.")
make_table([
    ["Phase", "Scope", "Status"],
    ["Weeks 1–4", "Stage 1 — models, importer, REST API, admin, tooling",
     {"text": "Done", "color": GREEN, "b": True}],
    ["Weeks 5–8", "Stage 2 — authentication, RBAC, analytics/pivot, attachments",
     {"text": "Largely done", "color": GREEN, "b": True}],
    ["Weeks 9–10", "Security hardening, testing, CI/CD, deployment",
     {"text": "Done", "color": GREEN, "b": True}],
    ["Post-deadline", "Remaining Stage 2 (KPI endpoints, alerts) and Stage 3 (ML)",
     {"text": "Planned", "color": GREY, "b": True}],
], [30, 102, 34], font_size=9.5)
spacer(4)
body("The core (Stage 1 and the bulk of Stage 2) was prioritised to guarantee a working, "
     "deployable system by the deadline; intelligent features were deliberately scheduled as "
     "follow-up work.")

# ====================================================== 12. RISK ==============
h1("12. Risk Analysis")
make_table([
    ["Risk", "Likelihood", "Impact", "Mitigation"],
    ["Data-import issues (messy/legacy spreadsheets)", "High", "Medium",
     "Forgiving header aliases, dry-run, per-row error reporting, idempotent update_or_create, atomic transaction"],
    ["Time constraints / scope creep", "Medium", "High",
     "Stage-based plan, MoSCoW prioritisation, core before “smart” features"],
    ["Security vulnerabilities", "Medium", "High",
     "OWASP Top 10 hardening, bandit + check --deploy in CI, pinned deps + Dependabot"],
    ["Single-developer bus factor", "Medium", "Medium",
     "Documented README, tests, reproducible Docker setup, CI gates"],
    ["Deployment / config errors", "Medium", "Medium",
     "check --deploy, healthcheck, production checklist, one-click platform configs"],
    ["Insufficient data for ML (Stage 3)", "Medium", "Medium",
     "Defer ML until enough labelled history exists; start with simple, explainable models"],
], [50, 24, 22, 70], font_size=9)

# ====================================================== 13. CONCLUSION ========
h1("13. Conclusion")
body("The Grief Tracker (ShipTrack) application provides a solid, secure, and deployable "
     "foundation for modern logistics-incident management. It replaces the legacy Excel workflow "
     "with a structured multi-user system, ingests the existing data unchanged, improves "
     "visibility through an interactive analytics/pivot view, and is hardened against the OWASP "
     "Top 10 with automated testing and CI/CD. Stage 1 and the majority of Stage 2 are implemented "
     "and running; the remaining Stage 2 items (KPI endpoints, alerts) and the Stage 3 intelligent "
     "features are designed and scheduled as follow-up work on top of the architecture already in "
     "place.")

# ====================================================== 14. GLOSSARY ==========
h1("14. Glossary")
make_table([
    ["Term", "Meaning"],
    ["Grief", "In-house term (from the legacy K&N workbook) for a shipment incident / claim."],
    ["K&N / Kuehne+Nagel", "Origin of the legacy Grief spreadsheet; its column names are still accepted by the importer."],
    ["RBAC", "Role-Based Access Control (Admin / Editor / Viewer)."],
    ["DRF", "Django REST Framework."],
    ["Idempotent", "Re-running the import produces the same result instead of duplicating rows."],
    ["SSO", "Single Sign-On (Google / Microsoft)."],
    ["OWASP / CSP / HSTS / SBOM", "Web-security standards and artefacts referenced in sections 7 and 9."],
], [46, 120], font_size=9.5)

# ====================================================== 15. REFERENCES ========
h1("15. References")
bullet(["Django 5.0 documentation — djangoproject.com"])
bullet(["Django REST Framework — django-rest-framework.org"])
bullet(["OWASP Top 10 (2021) — owasp.org/Top10"])
bullet(["django-allauth, django-axes, django-csp documentation"])
bullet(["Internal README.md (deployment, OWASP cheat-sheet, architecture)"])

OUT = r"C:\Users\koenj\Python Projecten J2\Grief Tracker 2\Grief Tracker - Final Report.docx"
doc.save(OUT)
print("saved:", OUT)
