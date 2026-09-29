"""HTML fragments for the Streamlit atlas.

Compare cards are dedented so Markdown does not turn them into code fences.
A binomial stays italic, wraps between genus and epithet, and is never uppercased.
IUCN badges show a cited code or “Not recorded”. They do not invent a category.
"""
from __future__ import annotations

import html
import textwrap
from typing import Any, Mapping

IUCN_LABELS = {
    "EX": "Extinct",
    "EW": "Extinct in the Wild",
    "CR": "Critically Endangered",
    "EN": "Endangered",
    "VU": "Vulnerable",
    "NT": "Near Threatened",
    "LC": "Least Concern",
    "DD": "Data Deficient",
    "NE": "Not Evaluated",
}


def markdown_html(fragment: str) -> str:
    """Drop leading spaces so Markdown does not turn the markup into a code fence."""
    cleaned = textwrap.dedent(fragment).strip()
    return "\n".join(line.lstrip() for line in cleaned.splitlines())


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:  # NaN
            return ""
    except Exception:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat", "<na>"}:
        return ""
    return text


def iucn_code(row: Mapping[str, Any]) -> str:
    """Return a cited category code, or empty when the snapshot has none."""
    status = _clean(row.get("iucn_status")) or "not_queried"
    if status != "ok":
        return ""
    code = _clean(row.get("iucn_category_code") or row.get("iucn_category")).upper()
    if code in IUCN_LABELS:
        return code
    return ""


def iucn_plain_label(row: Mapping[str, Any]) -> str:
    code = iucn_code(row)
    if not code:
        return "Not recorded"
    year = _clean(row.get("iucn_year"))
    label = IUCN_LABELS[code]
    if year:
        return f"{code} — {label} ({year})"
    return f"{code} — {label}"


def iucn_badge_html(row: Mapping[str, Any]) -> str:
    """Class-based badge. Styles live in app/styles.css."""
    code = iucn_code(row)
    if not code:
        return (
            '<span class="iucn-badge unknown" title="No IUCN category in this snapshot. Not an assessment.">'
            '<span class="code">—</span>'
            '<span class="name">Not recorded</span>'
            "</span>"
        )
    label = IUCN_LABELS[code]
    year = _clean(row.get("iucn_year"))
    year_html = f'<span class="year">{html.escape(year)}</span>' if year else ""
    return (
        f'<span class="iucn-badge {code.lower()}" title="Cited IUCN category. Not an HPI input.">'
        f'<span class="code">{html.escape(code)}</span>'
        f'<span class="name">{html.escape(label)}</span>'
        f"{year_html}"
        "</span>"
    )


def binomial_html(scientific_name: str) -> str:
    parts = str(scientific_name).split()
    if len(parts) < 2:
        return html.escape(str(scientific_name))
    genus = html.escape(parts[0])
    epithet = html.escape(" ".join(parts[1:]))
    return f'<span class="genus">{genus}</span><span class="epithet">{epithet}</span>'


def compare_card_html(row: Mapping[str, Any]) -> str:
    scientific = str(row.get("scientific_name") or "")
    vernacular = _clean(row.get("vernacular_ph"))
    title = ""
    if vernacular and vernacular.casefold() != scientific.casefold():
        title = f'<p class="card-title">{html.escape(vernacular)}</p>'
    hpi = float(row.get("hpi") or 0)
    band = html.escape(_clean(row.get("hpi_band")) or "—")
    arch = html.escape(_clean(row.get("archetype_label")) or "—")
    conf = float(row.get("hpi_confidence") or 0)
    n = int(float(row.get("n_occurrences") or 0))
    fragment = f"""
    <div class="hra-card hra-compare-card">
    {title}
    <p class="card-binomial">{binomial_html(scientific)}</p>
    <p class="metric-line"><span class="hra-mono">{hpi:.3f}</span> · {band}</p>
    <p class="metric-line">Confidence <span class="hra-mono">{conf:.2f}</span> · n={n}</p>
    <p class="metric-line"><span class="hra-chip">{arch}</span></p>
    <p class="components">R {float(row.get('component_rarity') or 0):.3f} · C {float(row.get('component_climate') or 0):.3f} · H {float(row.get('component_harvest') or 0):.3f} · P {float(row.get('component_pa_gap') or 0):.3f}</p>
    <p class="metric-line">{iucn_badge_html(row)}</p>
    </div>
    """
    return markdown_html(fragment)


def compare_grid_html(row_a: Mapping[str, Any], row_b: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            '<div class="hra-compare-grid">',
            compare_card_html(row_a),
            compare_card_html(row_b),
            "</div>",
        ]
    )


def map_howto_html() -> str:
    return markdown_html(
        """
        <div class="hra-howto">
        <span class="kicker">How to read this map</span>
        <span>Circle size follows HPI. Color is the pressure band only.</span>
        <span>Cluster numbers count records in view, not risk.</span>
        <span>Points are sample centroids, not harvest sites or permits.</span>
        </div>
        """
    )


def demo_talk_track_html(page: str, lines: list[str]) -> str:
    items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
    return markdown_html(
        f"""
        <div class="hra-talk">
        <span class="kicker">Demo talk track · {html.escape(page)}</span>
        <ol>{items}</ol>
        </div>
        """
    )
