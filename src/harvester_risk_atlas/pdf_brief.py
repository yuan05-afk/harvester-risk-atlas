"""Field brief exporters — HTML + real PDF. No medical claims; IUCN never invented."""
from __future__ import annotations

import io
from typing import Any


def _safe_float(v: Any, fmt: str = ".3f", default: str = "—") -> str:
    try:
        if v is None or (isinstance(v, float) and v != v):
            return default
        return format(float(v), fmt)
    except (TypeError, ValueError):
        return default


def _iucn_line(row: dict[str, Any]) -> str:
    """Honest IUCN line for briefs — never invent a category."""
    status = str(row.get("iucn_status") or "not_queried").strip()
    cat = row.get("iucn_category") or row.get("iucn_category_code")
    year = row.get("iucn_year")
    if status == "ok" and cat:
        line = f"IUCN Red List: {cat}"
        if year is not None and str(year) not in ("", "nan", "None"):
            line += f" ({year})"
        return line
    if status == "not_queried":
        return "IUCN not linked — API not queried; category never invented."
    if status in ("not_on_red_list", "no_assessment", "skipped"):
        return f"IUCN: {status.replace('_', ' ')} — no category shown."
    return f"IUCN: {status} — category not shown (never invented)."


def _centroid_line(row: dict[str, Any]) -> str:
    lat, lon = row.get("lat_mean"), row.get("lon_mean")
    n = row.get("n_occurrences", 0) or 0
    try:
        if lat is not None and lon is not None and lat == lat and lon == lon:
            return f"Centroid ≈ {float(lat):.3f}°N, {float(lon):.3f}°E · n={int(n)} GBIF sample pts"
    except (TypeError, ValueError):
        pass
    return f"No georeferenced sample · n={int(n) if n == n else 0} GBIF pts"


def render_field_brief_html(row: dict[str, Any], actions: list[str]) -> str:
    hpi_s = _safe_float(row.get("hpi"))
    conf_s = _safe_float(row.get("hpi_confidence"), ".2f")
    actions_li = "".join(f"<li>{a}</li>" for a in actions)
    iucn = _iucn_line(row)
    note = row.get("iucn_note") or ""
    if str(row.get("iucn_status") or "") == "not_queried":
        # Prefer short mute note over token signup essay in the brief body
        note = "Set IUCN_API_TOKEN and re-run fetch_iucn.py for live categories."
    clim = row.get("climate_source") or row.get("climate_method") or "n/a"
    pa = row.get("pa_source") or row.get("pa_method") or "n/a"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Field brief — {row.get('scientific_name','')}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, Inter, Helvetica, Arial, sans-serif;
         color: #1d1d1f; max-width: 720px; margin: 2rem auto; padding: 0 1rem;
         line-height: 1.55; font-size: 15px; }}
  h1 {{ font-size: 1.5rem; font-weight: 600; letter-spacing: -0.02em; margin: 0.2rem 0 0.15rem 0; }}
  .kicker {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: #86868b; }}
  .sub {{ color: #6e6e73; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  .metric {{ font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
             font-variant-numeric: tabular-nums; }}
  .box {{ border: 1px solid #d2d2d7; border-radius: 8px; padding: 0.85rem 1rem; margin: 0.75rem 0; }}
  .label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: #86868b;
            margin-bottom: 0.35rem; }}
  .muted {{ color: #6e6e73; font-size: 0.85rem; }}
  .iucn-muted {{ color: #86868b; font-size: 0.9rem; }}
  ul {{ margin: 0.35rem 0 0 1.1rem; padding: 0; }}
  li {{ margin-bottom: 0.35rem; }}
  .disc {{ font-size: 0.75rem; color: #6e6e73; border-top: 1px solid #d2d2d7;
           padding-top: 0.75rem; margin-top: 1.5rem; }}
</style>
</head>
<body>
  <div class="kicker">Harvester Risk Atlas — field brief</div>
  <h1>{row.get('scientific_name','')}</h1>
  <div class="sub">{row.get('vernacular_ph','')} · {row.get('family','')}</div>
  <div class="box"><div class="label">Stress (HPI v1.1)</div>
    <div class="metric" style="font-size:1.4rem">{hpi_s}</div>
    <div class="muted">Confidence {conf_s} · Band: {row.get('hpi_band','—')}</div>
  </div>
  <div class="box"><div class="label">Where</div>
    <div>{_centroid_line(row)}</div>
  </div>
  <div class="box"><div class="label">Why it matters</div>
    <div>{row.get('notes','')}</div>
    <div class="iucn-muted" style="margin-top:0.5rem">{iucn}</div>
    <div class="muted" style="margin-top:0.3rem">{note}</div>
    <div style="margin-top:0.4rem;font-size:0.75rem;color:#86868b">Climate: {clim} · PA: {pa}</div>
  </div>
  <div class="box"><div class="label">What to do</div>
    <ul>{actions_li}</ul>
  </div>
  <p class="disc">Not medical advice. Not a harvest permit. HPI is a transparent research index;
  IUCN categories are never invented. EthnoHACK 2026 Track 3.</p>
</body>
</html>
"""


def render_field_brief_pdf(row: dict[str, Any], actions: list[str]) -> bytes:
    """Generate a one-page PDF brief. Prefers reportlab; falls back to fpdf2."""
    try:
        return _pdf_reportlab(row, actions)
    except ImportError:
        pass
    try:
        return _pdf_fpdf2(row, actions)
    except ImportError as e:
        raise ImportError(
            "PDF export needs reportlab or fpdf2. pip install reportlab"
        ) from e


def _pdf_reportlab(row: dict[str, Any], actions: list[str]) -> bytes:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    ink = HexColor("#1d1d1f")
    secondary = HexColor("#6e6e73")
    tertiary = HexColor("#86868b")
    hairline = HexColor("#d2d2d7")
    accent = HexColor("#2d6a4f")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Field brief — {row.get('scientific_name', '')}",
        author="Harvester Risk Atlas",
    )
    base = getSampleStyleSheet()
    styles = {
        "kicker": ParagraphStyle(
            "kicker",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=tertiary,
            spaceAfter=4,
            tracking=1,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=ink,
            leading=20,
            spaceAfter=2,
        ),
        "sub": ParagraphStyle(
            "sub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=secondary,
            spaceAfter=12,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=tertiary,
            spaceBefore=10,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=ink,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "metric": ParagraphStyle(
            "metric",
            parent=base["Normal"],
            fontName="Courier-Bold",
            fontSize=18,
            textColor=ink,
            spaceAfter=2,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=secondary,
            leading=12,
            spaceAfter=2,
        ),
        "action": ParagraphStyle(
            "action",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=ink,
            leading=13,
            leftIndent=12,
            spaceAfter=4,
        ),
        "disc": ParagraphStyle(
            "disc",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=secondary,
            leading=11,
            spaceBefore=16,
            borderPadding=6,
        ),
        "rule": ParagraphStyle(
            "rule",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=accent,
            spaceAfter=0,
        ),
    }

    def esc(s: Any) -> str:
        t = "" if s is None else str(s)
        return (
            t.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    hpi_s = _safe_float(row.get("hpi"))
    conf_s = _safe_float(row.get("hpi_confidence"), ".2f")
    iucn = _iucn_line(row)
    note = "Set IUCN_API_TOKEN and re-run fetch_iucn.py for live categories."
    if str(row.get("iucn_status") or "") == "ok":
        note = str(row.get("iucn_note") or "")
    clim = row.get("climate_source") or row.get("climate_method") or "n/a"
    pa = row.get("pa_source") or row.get("pa_method") or "n/a"

    story = [
        Paragraph("HARVESTER RISK ATLAS — FIELD BRIEF", styles["kicker"]),
        Paragraph(esc(row.get("scientific_name", "")), styles["title"]),
        Paragraph(
            f"{esc(row.get('vernacular_ph', ''))} · {esc(row.get('family', ''))}",
            styles["sub"],
        ),
        Paragraph("STRESS (HPI v1.1)", styles["label"]),
        Paragraph(hpi_s, styles["metric"]),
        Paragraph(
            f"Confidence {conf_s} · Band: {esc(row.get('hpi_band', '—'))}",
            styles["muted"],
        ),
        Paragraph("WHERE", styles["label"]),
        Paragraph(esc(_centroid_line(row)), styles["body"]),
        Paragraph("WHY IT MATTERS", styles["label"]),
        Paragraph(esc(row.get("notes", "")), styles["body"]),
        Paragraph(esc(iucn), styles["muted"]),
    ]
    if note:
        story.append(Paragraph(esc(note), styles["muted"]))
    story.append(
        Paragraph(f"Climate: {esc(clim)} · PA: {esc(pa)}", styles["muted"])
    )
    story.append(Paragraph("WHAT TO DO", styles["label"]))
    for a in actions:
        story.append(Paragraph(f"• {esc(a)}", styles["action"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Not medical advice. Not a harvest permit. HPI is a transparent research index; "
            "IUCN categories are never invented. EthnoHACK 2026 Track 3.",
            styles["disc"],
        )
    )
    # hairline is unused visually but keeps token parity with DESIGN.md
    _ = hairline
    doc.build(story)
    return buf.getvalue()


def _pdf_fpdf2(row: dict[str, Any], actions: list[str]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(22, 18, 22)

    def text(s: Any) -> str:
        # fpdf2 core fonts are latin-1; strip non-encodable chars
        raw = "" if s is None else str(s)
        return raw.encode("latin-1", "replace").decode("latin-1")

    hpi_s = _safe_float(row.get("hpi"))
    conf_s = _safe_float(row.get("hpi_confidence"), ".2f")
    iucn = _iucn_line(row)

    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x86, 0x86, 0x8B)
    pdf.cell(0, 5, "HARVESTER RISK ATLAS — FIELD BRIEF", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0x1D, 0x1D, 0x1F)
    pdf.multi_cell(0, 8, text(row.get("scientific_name", "")))

    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0x6E, 0x6E, 0x73)
    pdf.multi_cell(
        0,
        5,
        text(f"{row.get('vernacular_ph', '')} · {row.get('family', '')}"),
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x86, 0x86, 0x8B)
    pdf.cell(0, 5, "STRESS (HPI v1.1)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "B", 18)
    pdf.set_text_color(0x1D, 0x1D, 0x1F)
    pdf.cell(0, 9, hpi_s, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(0x6E, 0x6E, 0x73)
    pdf.multi_cell(
        0,
        5,
        text(f"Confidence {conf_s} · Band: {row.get('hpi_band', '—')}"),
    )

    pdf.ln(3)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x86, 0x86, 0x8B)
    pdf.cell(0, 5, "WHERE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0x1D, 0x1D, 0x1F)
    pdf.multi_cell(0, 5, text(_centroid_line(row)))

    pdf.ln(2)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x86, 0x86, 0x8B)
    pdf.cell(0, 5, "WHY IT MATTERS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0x1D, 0x1D, 0x1F)
    pdf.multi_cell(0, 5, text(row.get("notes", "")))
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(0x6E, 0x6E, 0x73)
    pdf.multi_cell(0, 5, text(iucn))

    pdf.ln(2)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x86, 0x86, 0x8B)
    pdf.cell(0, 5, "WHAT TO DO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0x1D, 0x1D, 0x1F)
    for a in actions:
        pdf.multi_cell(0, 5, text(f"- {a}"))

    pdf.ln(6)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(0x6E, 0x6E, 0x73)
    pdf.multi_cell(
        0,
        4,
        "Not medical advice. Not a harvest permit. HPI is a transparent research index; "
        "IUCN categories are never invented. EthnoHACK 2026 Track 3.",
    )
    out = pdf.output()
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
