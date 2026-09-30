"""Home page and first-visit preface. No Streamlit imports — markup only."""
from __future__ import annotations

DISCLAIMER_HTML = """
<div class="hra-disclaimer">
  <strong>Disclaimer.</strong> Not medical advice, not a harvest permit, not a Red List assessment.
  Ethnobotany notes are cultural context only. IUCN categories are never invented —
  live lookup needs an API token.
</div>
""".strip()

_BANNED_PHRASES = (
    "unlock",
    "seamlessly",
    "revolutionize",
    "ai-powered",
    "empower",
    "cutting-edge",
    "supercharge",
    "next-gen",
)


def demo_query_requested(query) -> bool:
    """True when the URL asks for the judging path.

    Matches the long-standing app rule: ``?demo=1|true|yes`` or a bare ``demo`` key.
    """
    raw = query.get("demo", "")
    if raw is None:
        raw = ""
    if str(raw).lower() in {"1", "true", "yes"}:
        return True
    return "demo" in query


def should_play_intro(*, intro_played: bool, demo_requested: bool) -> bool:
    """Preface plays once per session, and never on the judging deep link."""
    return not intro_played and not demo_requested


def default_page(*, demo_requested: bool) -> str:
    return "Map" if demo_requested else "Home"


def format_weights(weights: dict) -> dict[str, str]:
    return {
        "rarity": f"{float(weights['rarity']):.2f}",
        "climate_stress": f"{float(weights['climate_stress']):.2f}",
        "harvest_proxy": f"{float(weights['harvest_proxy']):.2f}",
        "pa_gap": f"{float(weights['pa_gap']):.2f}",
    }


def formula_line(weights: dict) -> str:
    w = format_weights(weights)
    return (
        f"HPI = {w['rarity']} R + {w['climate_stress']} C"
        f" + {w['harvest_proxy']} H + {w['pa_gap']} P"
    )


def cohort_note(
    *,
    n_taxa: int,
    band_counts: dict,
    n_imputed: int,
    iucn_unlinked: bool,
) -> str:
    lower = int(band_counts.get("Lower relative pressure", 0))
    mid = int(band_counts.get("Moderate", 0))
    high = int(band_counts.get("Higher relative pressure", 0))
    sentences = [
        f"This build: {n_taxa} taxa. Bands — {lower} lower, {mid} moderate, {high} higher."
    ]
    if n_taxa and high == 0:
        sentences.append(
            "No taxon clears the higher band, so the color alone does not separate the cohort. The dossier does."
        )
    if n_imputed == 1:
        sentences.append("One taxon has imputed inputs, so its confidence is marked down.")
    elif n_imputed > 1:
        sentences.append(
            f"{n_imputed} taxa have imputed inputs, so their confidence is marked down."
        )
    if iucn_unlinked:
        sentences.append("IUCN is not linked in this build. Categories are blank, not guessed.")
    return " ".join(sentences)


# Schematic Philippines, lon/lat. North is small y, so the field draws downward.
_MARK_SCALE = 15.4
_MARK_LON0 = 116.3
_MARK_LAT0 = 19.15
_MARK_ISLANDS = (
    (
        "sil-n",
        (
            (120.45, 18.55),
            (121.15, 18.65),
            (122.05, 18.45),
            (122.45, 17.70),
            (122.25, 16.60),
            (121.85, 15.55),
            (121.45, 14.85),
            (122.15, 14.15),
            (123.25, 13.45),
            (123.95, 12.85),
            (124.15, 12.45),
            (123.35, 12.95),
            (122.35, 13.45),
            (121.35, 13.55),
            (120.75, 13.95),
            (120.35, 14.55),
            (120.15, 15.35),
            (119.85, 16.35),
            (120.15, 17.45),
            (120.45, 18.15),
        ),
    ),
    ("sil-w", ((120.85, 13.35), (121.25, 13.05), (121.15, 12.35), (120.70, 12.25), (120.45, 12.85))),
    (
        "sil-w",
        (
            (119.85, 11.15),
            (119.25, 10.15),
            (118.55, 9.15),
            (117.95, 8.45),
            (118.25, 8.35),
            (118.85, 9.05),
            (119.55, 10.05),
            (120.05, 11.00),
        ),
    ),
    ("sil-c", ((122.15, 11.55), (122.75, 11.25), (122.55, 10.55), (122.05, 10.75))),
    ("sil-c", ((122.85, 10.85), (123.25, 10.15), (123.05, 9.25), (122.65, 9.45), (122.55, 10.35))),
    ("sil-c", ((123.65, 11.15), (123.95, 10.45), (123.80, 9.65), (123.55, 10.15), (123.50, 10.85))),
    ("sil-c", ((123.85, 9.85), (124.25, 9.70), (124.15, 9.35), (123.80, 9.45))),
    ("sil-c", ((125.05, 12.35), (125.55, 11.75), (125.35, 11.05), (124.90, 11.35), (124.75, 12.00))),
    ("sil-c", ((124.55, 11.35), (124.95, 10.65), (124.70, 10.05), (124.40, 10.55), (124.35, 11.05))),
    (
        "sil-s",
        (
            (122.95, 8.15),
            (123.70, 8.55),
            (124.80, 8.75),
            (125.70, 8.35),
            (126.25, 7.55),
            (126.05, 6.85),
            (125.15, 6.35),
            (124.15, 6.55),
            (123.25, 7.15),
            (122.55, 7.55),
            (122.75, 8.00),
        ),
    ),
)
# (lon, lat, r, ring) — a few occurrence marks, not a cloud.
_MARK_DOTS = (
    (121.00, 17.60, 1.55, False),
    (120.60, 16.45, 2.15, True),
    (122.60, 16.00, 1.45, False),
    (121.00, 14.60, 2.05, True),
    (123.50, 13.25, 1.65, False),
    (118.75, 9.75, 1.70, True),
    (122.45, 10.70, 1.60, False),
    (123.90, 10.30, 2.00, True),
    (124.90, 11.15, 1.55, False),
    (124.65, 8.45, 1.80, False),
    (125.55, 7.15, 2.10, True),
    (122.20, 6.95, 1.60, False),
)


def _mark_xy(lon: float, lat: float) -> tuple[float, float]:
    x = (lon - _MARK_LON0) * _MARK_SCALE
    y = (_MARK_LAT0 - lat) * _MARK_SCALE
    return (round(x, 1), round(y, 1))


def _preface_mark() -> str:
    """Archipelago silhouette, occurrence dots, and one leaf. CSS draws them."""
    islands = []
    for klass, ring in _MARK_ISLANDS:
        pts = " L ".join(f"{x} {y}" for x, y in (_mark_xy(lon, lat) for lon, lat in ring))
        islands.append(f'<path class="hra-sil {klass}" pathLength="100" d="M {pts} Z"/>')
    dots = []
    for lon, lat, radius, ring in _MARK_DOTS:
        x, y = _mark_xy(lon, lat)
        kind = "dot ring" if ring else "dot"
        # Latitude bands, not inline styles — Streamlit's sanitizer may drop style.
        band = "d1" if lat > 15 else "d2" if lat > 12 else "d3" if lat > 9 else "d4"
        dots.append(f'<circle class="{kind} {band}" cx="{x}" cy="{y}" r="{radius}"/>')
    leaf = (
        '<g class="hra-leaf">'
        '<path class="draw d-stem" pathLength="100" d="M196 150C196 112 198 74 200 42"/>'
        '<path class="draw d-blade" pathLength="100" d="M200 46C214 62 226 92 218 124C214 142 206 154 198 156C188 152 178 136 182 108C186 80 192 58 200 46Z"/>'
        '<path class="draw d-vein" pathLength="100" d="M198 108C186 100 180 88 184 76"/>'
        '<path class="draw d-vein" pathLength="100" d="M200 92C212 84 218 72 216 60"/>'
        '<path class="draw d-vein" pathLength="100" d="M198 128C210 120 214 108 210 96"/>'
        "</g>"
    )
    return (
        '<svg class="hra-mark" viewBox="10 0 230 208" fill="none" aria-hidden="true">'
        f"{''.join(islands)}{''.join(dots)}{leaf}"
        "</svg>"
    )


def preload_markup(weights: dict) -> str:
    """One-shot preface. The stylesheet owns timing, lift, and the mark."""
    formula = formula_line(weights)
    return (
        '<div class="hra-preload">'
        '<div class="hra-preload-top">EthnoHACK 2026</div>'
        '<div class="hra-preload-lockup">'
        f"{_preface_mark()}"
        '<div class="hra-preload-stage">'
        '<p class="beat b1"><span class="k">Wild harvest</span>'
        '<span class="line">Medicinal plants are still taken from the wild.</span></p>'
        '<p class="beat b2"><span class="k">The gap</span>'
        '<span class="line">No shared number shows that pressure.</span></p>'
        '<p class="beat b3"><span class="k">Not a Red List</span>'
        '<span class="line">This atlas never invents one.</span></p>'
        '<p class="beat b4"><span class="k">Harvester Risk Atlas</span>'
        '<span class="line">Four open inputs. One relative score.</span>'
        f'<span class="formula">{formula}</span></p>'
        "</div></div>"
        '<div class="hra-count" aria-hidden="true">'
        '<i class="c1">01</i><i class="c2">02</i><i class="c3">03</i><i class="c4">04</i>'
        "</div>"
        '<div class="hra-preload-bar" aria-hidden="true"></div>'
        "</div>"
    )


def home_markup(
    *,
    n_taxa: int,
    band_counts: dict,
    n_imputed: int,
    iucn_unlinked: bool,
    weights: dict,
) -> str:
    w = format_weights(weights)
    note = cohort_note(
        n_taxa=n_taxa,
        band_counts=band_counts,
        n_imputed=n_imputed,
        iucn_unlinked=iucn_unlinked,
    )
    return f"""
<div class="hra-home">
  <div class="hra-kicker">EthnoHACK 2026 · Track 3 · Biodiversity &amp; Sustainability</div>
  <h1>Harvester Risk Atlas</h1>
  <p class="hra-lead">Wild collection, climate stress, and thin protected-area cover overlap on medicinal plants in the Philippines and Southeast Asia. The people who watch those plants do not have one transparent score for that pressure. Red List status answers a different question.</p>
  {DISCLAIMER_HTML}
  <h2>The problem</h2>
  <p>GBIF points, WorldClim layers, a harvest proxy, and protected-area polygons do not arrive as one number. A field team either jumps between those files or borrows an IUCN category for a question it does not answer. Inventing the missing category is not allowed here.</p>
  <h2>What the atlas solves</h2>
  <p>It keeps those sources separate, scales each from 0 to 1, and adds them with fixed weights. The Harvest Pressure Index ranks relative concern inside this cohort. It does not permit a harvest, give medical advice, or assess extinction risk.</p>
  <div class="hra-formula">
    <div class="hra-kicker">HPI v1.1</div>
    <p class="eq">{w['rarity']} rarity + {w['climate_stress']} climate stress + {w['harvest_proxy']} harvest proxy + {w['pa_gap']} protected-area gap</p>
    <p class="note">Confidence falls when an input was imputed. IUCN sits beside the score, never inside it.</p>
  </div>
  <div class="hra-parts-wrap">
  <table class="hra-parts">
    <thead>
      <tr><th>Term</th><th>What goes in</th></tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="term">Rarity</span><span class="weight">weight {w['rarity']}</span></td>
        <td class="goes">Inverted GBIF count, plus an endemism cue from the seed notes.</td>
      </tr>
      <tr>
        <td><span class="term">Climate stress</span><span class="weight">weight {w['climate_stress']}</span></td>
        <td class="goes">WorldClim 2.1 temperature, precipitation, and seasonality on a Southeast Asia clip.</td>
      </tr>
      <tr>
        <td><span class="term">Harvest proxy</span><span class="weight">weight {w['harvest_proxy']}</span></td>
        <td class="goes">Local occurrence density, the share of recent records, and a literature harvest flag.</td>
      </tr>
      <tr>
        <td><span class="term">Protected-area gap</span><span class="weight">weight {w['pa_gap']}</span></td>
        <td class="goes">Share of points outside WDPCA Philippines, with a small distance boost when the gap is large.</td>
      </tr>
    </tbody>
  </table>
  </div>
  <h2>How it is used</h2>
  <ol class="hra-path">
    <li><strong>Map.</strong> One centroid per species. Color is the HPI band. Size follows the score.</li>
    <li><strong>Dossier.</strong> The four components, the gaps, and how far confidence fell.</li>
    <li><strong>Field brief.</strong> A stewardship sheet, HTML or PDF. Research and education only.</li>
  </ol>
  <p class="hra-cohort">{note}</p>
</div>
""".strip()


def assert_plain_voice(markup: str) -> None:
    lowered = markup.lower()
    for phrase in _BANNED_PHRASES:
        if phrase in lowered:
            raise ValueError(f"landing copy contains banned phrase: {phrase}")
