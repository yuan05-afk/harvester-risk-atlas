"""Plain-language brief built only from scored catalog fields."""

from __future__ import annotations

import html
from io import BytesIO
from xml.sax.saxutils import escape

from hra.data import category_label, display_name, iucn_badge_text
from hra.scoring import LISTING_POINTS, MIN_GEOREFERENCED


def _listing_sentence(species: dict) -> str:
    iucn = species.get("iucn")
    if not iucn:
        return (
            f"No IUCN category is stored for {species['scientific_name']} in this snapshot. "
            "That is not a statement that IUCN has left it unassessed."
        )
    return (
        f"{species['scientific_name']} is recorded as {iucn['label']} ({iucn['code']}) "
        f"from {iucn.get('source_title') or 'a cited IUCN Red List version'} "
        f"(taxon {iucn['iucn_taxon_id']})."
    )


def _concentration_sentence(species: dict) -> str:
    occurrences = species.get("occurrences") or {}
    share = occurrences.get("top_country_share")
    country = occurrences.get("top_country_name") or occurrences.get("top_country_code")
    count = occurrences.get("georeferenced_count") or 0
    if species["score"]["concentration"] is None or share is None or not country:
        return (
            f"GBIF returned {count} georeferenced records. "
            "Record concentration is left unscored below 30 records."
        )
    percent = round(float(share) * 100)
    return (
        f"{percent}% of georeferenced GBIF records in this snapshot fall in {country} "
        f"({count} georeferenced records). That share is a record pattern, not a harvest volume "
        "or a population estimate."
    )


def species_paragraph(species: dict) -> str:
    score = species["score"]
    name = display_name(species)
    lines = [f"{name} ({species['scientific_name']}).", _listing_sentence(species), _concentration_sentence(species)]
    if score["complete"]:
        lines.append(
            f"HPI is {score['hpi']} ({score['band']}), from listing {score['listing']} and "
            f"record concentration {score['concentration']} on a 0–50 scale each."
        )
    else:
        lines.append("HPI is not scored, because one of those inputs is missing.")
    return " ".join(lines)


def _closing(left: dict, right: dict) -> str:
    return (
        f"Catalog categories: {category_label(left)} and {category_label(right)}. "
        "HPI is an in-app sum. It is not an IUCN category, a trend, or a quota. "
        f"Listing points are CR {LISTING_POINTS['CR']}, EN {LISTING_POINTS['EN']}, "
        f"VU {LISTING_POINTS['VU']}, NT {LISTING_POINTS['NT']}, LC {LISTING_POINTS['LC']}. "
        f"Record concentration needs at least {MIN_GEOREFERENCED} georeferenced records."
    )


def brief_markdown(left: dict, right: dict) -> str:
    title = f"# Brief: {display_name(left)} and {display_name(right)}"
    body = [
        title,
        "",
        "Harvester Risk Atlas · EthnoHACK 2026 Track 3",
        "",
        species_paragraph(left),
        "",
        species_paragraph(right),
        "",
        _closing(left, right),
        "",
    ]
    return "\n".join(body)


def _field_sections(left: dict, right: dict) -> list[tuple[str, str]]:
    sections = []
    for species in (left, right):
        heading = f"{display_name(species)} · {iucn_badge_text(species)}"
        sections.append((heading, species_paragraph(species)))
    return sections


def brief_html(left: dict, right: dict) -> str:
    blocks = []
    for heading, paragraph in _field_sections(left, right):
        blocks.append(
            f"<h2>{html.escape(heading)}</h2><p>{html.escape(paragraph)}</p>"
        )
    title = html.escape(f"{display_name(left)} and {display_name(right)}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Field brief · {title}</title>
<style>
  body {{ margin: 2rem auto; max-width: 40rem; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; color: #1d1d1f; line-height: 1.5; }}
  h1 {{ font-size: 1.6rem; font-weight: 600; letter-spacing: -0.02em; }}
  h2 {{ font-size: 1.05rem; font-weight: 600; margin-top: 1.6rem; }}
  p {{ font-size: 0.95rem; }}
  .meta {{ color: #6e6e73; font-size: 0.85rem; }}
</style>
</head>
<body>
<h1>Field brief</h1>
<p class="meta">Harvester Risk Atlas · EthnoHACK 2026 Track 3</p>
{''.join(blocks)}
<p class="meta">{html.escape(_closing(left, right))}</p>
</body>
</html>
"""


def brief_pdf(left: dict, right: dict) -> bytes:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Field brief: {display_name(left)} and {display_name(right)}",
        author="Harvester Risk Atlas",
    )
    ink = HexColor("#1d1d1f")
    caption = HexColor("#6e6e73")
    forest = HexColor("#1f4d3a")
    title = ParagraphStyle(
        "FieldTitle",
        fontName="Helvetica",
        fontSize=18,
        leading=22,
        textColor=ink,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    meta = ParagraphStyle("Meta", fontName="Helvetica", fontSize=9, leading=12, textColor=caption, spaceAfter=8)
    heading = ParagraphStyle("Heading", fontName="Helvetica", fontSize=12, leading=16, textColor=ink, spaceBefore=12, spaceAfter=4)
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10, leading=14, textColor=ink, spaceAfter=6)
    story = [
        Paragraph(escape("Field brief"), title),
        Paragraph(escape("Harvester Risk Atlas · EthnoHACK 2026 Track 3"), meta),
        HRFlowable(width="100%", thickness=0.4, color=forest, spaceAfter=6),
    ]
    for section_title, paragraph in _field_sections(left, right):
        story.append(Paragraph(escape(section_title), heading))
        story.append(Paragraph(escape(paragraph), body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(escape(_closing(left, right)), meta))
    document.build(story)
    return buffer.getvalue()


def talk_track(primary: dict, other: dict) -> str:
    """About one minute of speech. Figures come only from the two catalog records."""

    def beat(species: dict, lead: str) -> str:
        iucn = species.get("iucn")
        score = species["score"]
        occurrences = species.get("occurrences") or {}
        if not iucn or not iucn.get("code"):
            listed = (
                f"{lead} No IUCN category is cited for {species['scientific_name']} in this snapshot, "
                "so the badge says IUCN not linked and listing stays unscored."
            )
        else:
            listed = (
                f"{lead} {species['scientific_name']} is cited as {iucn['label']}, {iucn['code']}, "
                f"from {iucn.get('source_title') or 'a cited IUCN Red List version'}, "
                f"taxon {iucn['iucn_taxon_id']}. Listing is {score['listing']} of 50."
            )
        if score["concentration"] is None:
            count = occurrences.get("georeferenced_count") or 0
            concentration = f" Record concentration is unscored, with {count} georeferenced records."
        else:
            country = occurrences.get("top_country_name") or occurrences.get("top_country_code")
            percent = round(float(occurrences["top_country_share"]) * 100)
            count = occurrences.get("georeferenced_count")
            concentration = (
                f" {country} holds {percent} percent of {count} georeferenced records, "
                f"which is {score['concentration']} concentration points."
            )
        if score["complete"]:
            total = f" HPI is {score['hpi']}, {score['band']}."
        else:
            total = " HPI is not scored, because one of those inputs is missing."
        return listed + concentration + total

    other_name = display_name(other)
    compare_lead = f"On the brief, set it beside {other['scientific_name']}"
    if other_name.casefold() != other["scientific_name"].casefold():
        compare_lead += f", {other_name}"
    compare_lead += "."
    parts = [
        "Open the map. Marker color is the Harvester Pressure Index band. A cluster number counts GBIF records, not risk.",
        beat(primary, "The demo species is on screen."),
        "That total is an in-app sum. It is not an IUCN index, a harvest volume, or a population estimate.",
        beat(other, compare_lead),
        "When a record has no cited IUCN category, the badge says IUCN not linked. The atlas does not fill one in.",
    ]
    return " ".join(parts)
