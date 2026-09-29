"""One-page field brief: standalone HTML and a reportlab PDF. No medical claims."""
from __future__ import annotations

import html
from io import BytesIO
from typing import Any

from .markup import iucn_plain_label


def _num(value: Any, fmt: str, missing: str = "—") -> str:
    if value is None:
        return missing
    try:
        number = float(value)
    except (TypeError, ValueError):
        return missing
    if number != number:
        return missing
    return format(number, fmt)


def _pdf_safe(text: Any) -> str:
    """WinAnsi-safe text for the standard PDF fonts."""
    raw = "" if text is None else str(text)
    return (
        raw.replace("×", "x")
        .replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def render_field_brief_html(row: dict[str, Any], actions: list[str]) -> str:
    hpi_s = _num(row.get("hpi"), ".3f")
    conf_s = _num(row.get("hpi_confidence"), ".2f")
    lat_s = _num(row.get("lat_mean"), ".3f")
    lon_s = _num(row.get("lon_mean"), ".3f")
    where = (
        f"Centroid ≈ {lat_s}°N, {lon_s}°E · n={int(float(row.get('n_occurrences') or 0))} GBIF sample pts"
        if lat_s != "—"
        else "No georeferenced sample points in this extract."
    )
    actions_li = "".join(f"<li>{html.escape(a)}</li>" for a in actions)
    iucn = html.escape(iucn_plain_label(row))
    note = html.escape(str(row.get("iucn_note") or row.get("demo_iucn_note") or ""))
    notes = html.escape(str(row.get("notes") or ""))
    name = html.escape(str(row.get("scientific_name") or ""))
    vernacular = html.escape(str(row.get("vernacular_ph") or ""))
    family = html.escape(str(row.get("family") or ""))
    band = html.escape(str(row.get("hpi_band") or "—"))
    climate = html.escape(str(row.get("climate_source") or "n/a"))
    pa = html.escape(str(row.get("pa_source") or "n/a"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Field brief — {name}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, Inter, Helvetica, Arial, sans-serif;
         color: #1d1d1f; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.35rem; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 0.15rem; font-style: italic; }}
  .sub {{ color: #6e6e73; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  .metric {{ font-family: "JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace;
             font-variant-numeric: tabular-nums; }}
  .box {{ border: 1px solid #d2d2d7; border-radius: 8px; padding: 0.85rem 1rem; margin: 0.75rem 0; }}
  .label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: #86868b; }}
  .badge {{ display: inline-block; border: 1px solid #d2d2d7; border-radius: 999px;
            padding: 0.12rem 0.55rem; font-size: 0.8rem; }}
  .disc {{ font-size: 0.75rem; color: #6e6e73; border-top: 1px solid #d2d2d7; padding-top: 0.75rem; margin-top: 1.5rem; }}
</style>
</head>
<body>
  <div class="label">Harvester Risk Atlas — field brief</div>
  <h1>{name}</h1>
  <div class="sub">{vernacular} · {family}</div>
  <div class="box"><div class="label">Stress (HPI v1)</div>
    <div class="metric" style="font-size:1.4rem">{hpi_s}</div>
    <div style="font-size:0.8rem;color:#6e6e73">Confidence {conf_s} · Band: {band}</div>
  </div>
  <div class="box"><div class="label">Where</div>
    <div>{where}</div>
  </div>
  <div class="box"><div class="label">Why it matters</div>
    <div>{notes}</div>
    <div style="margin-top:0.5rem"><span class="badge">IUCN {iucn}</span></div>
    <div style="margin-top:0.3rem;font-size:0.8rem;color:#6e6e73">{note}</div>
    <div style="margin-top:0.4rem;font-size:0.75rem;color:#86868b">Climate: {climate} · PA: {pa}</div>
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
    """One-page PDF field brief. Requires reportlab."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        ListFlowable,
        ListItem,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
    )

    name = _pdf_safe(row.get("scientific_name") or "Species")
    vernacular = _pdf_safe(row.get("vernacular_ph") or "")
    family = _pdf_safe(row.get("family") or "")
    hpi_s = _num(row.get("hpi"), ".3f")
    conf_s = _num(row.get("hpi_confidence"), ".2f")
    band = _pdf_safe(row.get("hpi_band") or "-")
    lat_s = _num(row.get("lat_mean"), ".3f")
    lon_s = _num(row.get("lon_mean"), ".3f")
    if lat_s == "—":
        where = "No georeferenced sample points in this extract."
    else:
        n = int(float(row.get("n_occurrences") or 0))
        where = f"Centroid approx. {lat_s} N, {lon_s} E. n={n} GBIF sample points."
    iucn = _pdf_safe(iucn_plain_label(row))
    notes = _pdf_safe(row.get("notes") or "")
    iucn_note = _pdf_safe(row.get("iucn_note") or row.get("demo_iucn_note") or "")
    climate = _pdf_safe(row.get("climate_source") or "n/a")
    pa = _pdf_safe(row.get("pa_source") or "n/a")

    styles = getSampleStyleSheet()
    kicker = ParagraphStyle(
        "Kicker",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=8,
        textColor=HexColor("#86868b"),
        tracking=0.4,
        spaceAfter=4,
    )
    title = ParagraphStyle(
        "Species",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=16,
        textColor=HexColor("#1d1d1f"),
        leading=20,
        spaceAfter=2,
    )
    sub = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        textColor=HexColor("#6e6e73"),
        spaceAfter=10,
    )
    label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=8,
        textColor=HexColor("#86868b"),
        spaceBefore=8,
        spaceAfter=2,
    )
    body = ParagraphStyle(
        "BodyCopy",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        textColor=HexColor("#1d1d1f"),
        leading=13,
        spaceAfter=2,
    )
    fine = ParagraphStyle(
        "Fine",
        parent=body,
        fontSize=8,
        textColor=HexColor("#6e6e73"),
        leading=11,
    )

    def p(text: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(html.escape(text).replace("\n", "<br/>"), style)

    story = [
        p("HARVESTER RISK ATLAS  -  FIELD BRIEF", kicker),
        p(name, title),
        p(f"{vernacular}  ·  {family}".strip(" ·"), sub),
        HRFlowable(width="100%", thickness=0.4, color=HexColor("#d2d2d7"), spaceAfter=6),
        p("STRESS (HPI v1)", label),
        p(f"{hpi_s}    confidence {conf_s}    band: {band}", body),
        p("WHERE", label),
        p(where, body),
        p("WHY IT MATTERS", label),
        p(notes or "No ethnobotany note on this row.", body),
        p(f"IUCN: {iucn}", body),
        p(iucn_note, fine),
        p(f"Climate: {climate}", fine),
        p(f"Protected areas: {pa}", fine),
        p("WHAT TO DO", label),
    ]
    if actions:
        story.append(
            ListFlowable(
                [ListItem(p(_pdf_safe(item), body), leftIndent=12) for item in actions],
                bulletType="bullet",
                start="•",
                leftIndent=16,
            )
        )
    story.extend(
        [
            Spacer(1, 8 * mm),
            HRFlowable(width="100%", thickness=0.4, color=HexColor("#d2d2d7"), spaceBefore=4, spaceAfter=6),
            p(
                "Not medical advice. Not a harvest permit. HPI is a transparent research index. "
                "IUCN categories are never invented. EthnoHACK 2026 Track 3.",
                fine,
            ),
        ]
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Field brief - {name}",
        author="Harvester Risk Atlas",
    )
    doc.build(story)
    return buf.getvalue()
