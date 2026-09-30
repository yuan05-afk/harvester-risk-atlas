"""Home page and first-visit preface. No Streamlit imports — markup only."""
from __future__ import annotations

import math

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


def should_play_intro(
    *, intro_played: bool, demo_requested: bool, replay: bool = False
) -> bool:
    """Preface plays once per session, and never on the judging deep link.

    ``replay`` is the quiet sidebar control. It plays one cinematic pass even
    after this session already showed the sheet, and even on ``?demo=1``.
    """
    if replay:
        return True
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
# Coasts are a simplified outline — recognizable Luzon, Visayas, Mindanao —
# not a basemap and not tied to GBIF or HPI.
_MARK_SCALE = 15.4
_MARK_LON0 = 116.3
_MARK_LAT0 = 19.15
_MARK_CURVE = 0.11
_MARK_CLAMP = 0.40
_MARK_ISLANDS = (
    # Luzon, including the Bicol peninsula. Stroke starts at the north tip.
    (
        "sil-n",
        (
            (121.10, 18.62),
            (121.95, 18.29),
            (122.15, 18.49),
            (122.32, 18.32),
            (122.15, 17.66),
            (122.52, 17.12),
            (122.14, 16.18),
            (121.60, 15.93),
            (121.39, 15.32),
            (121.70, 14.74),
            (121.80, 14.11),
            (122.14, 13.93),
            (122.49, 14.32),
            (122.86, 14.25),
            (123.23, 13.75),
            (123.32, 14.06),
            (123.82, 13.84),
            (123.55, 13.65),
            (123.79, 13.11),
            (124.14, 13.04),
            (124.06, 12.57),
            (123.95, 12.92),
            (123.31, 13.04),
            (123.16, 13.44),
            (122.60, 13.91),
            (122.60, 13.19),
            (122.38, 13.52),
            (121.78, 13.94),
            (121.20, 13.64),
            (120.73, 13.90),
            (120.62, 14.19),
            (120.92, 14.49),
            (120.58, 14.88),
            (120.44, 14.45),
            (120.08, 14.85),
            (119.83, 16.33),
            (120.12, 16.07),
            (120.39, 16.22),
            (120.30, 16.65),
            (120.41, 16.96),
            (120.36, 17.64),
            (120.60, 18.51),
        ),
    ),
    (
        "sil-w",
        (
            (120.40, 13.52),
            (120.76, 13.47),
            (120.92, 13.50),
            (121.12, 13.38),
            (121.20, 13.43),
            (121.52, 13.13),
            (121.48, 12.84),
            (121.54, 12.64),
            (121.39, 12.30),
            (121.24, 12.22),
            (121.11, 12.30),
            (120.92, 12.51),
            (120.80, 12.75),
            (120.76, 12.97),
            (120.65, 13.17),
            (120.51, 13.26),
        ),
    ),
    (
        "sil-w",
        (
            (119.50, 11.35),
            (119.53, 10.95),
            (119.69, 10.50),
            (119.37, 10.33),
            (119.19, 10.06),
            (118.83, 9.95),
            (118.57, 9.42),
            (118.13, 9.10),
            (117.99, 8.88),
            (117.22, 8.37),
            (117.35, 8.71),
            (117.88, 9.24),
            (118.11, 9.35),
            (119.02, 10.35),
            (119.29, 10.57),
            (119.26, 10.85),
        ),
    ),
    (
        "sil-c",
        (
            (124.22, 14.08),
            (124.31, 13.95),
            (124.42, 13.87),
            (124.40, 13.68),
            (124.33, 13.57),
            (124.25, 13.59),
            (124.18, 13.53),
            (124.04, 13.66),
            (124.12, 13.79),
            (124.12, 13.98),
        ),
    ),
    (
        "sil-c",
        (
            (123.24, 12.58),
            (123.46, 12.50),
            (123.72, 12.29),
            (123.91, 12.17),
            (124.04, 11.97),
            (124.05, 11.75),
            (123.74, 12.00),
            (123.61, 12.09),
            (123.53, 12.20),
            (123.42, 12.19),
            (123.16, 11.93),
            (123.27, 12.40),
        ),
    ),
    (
        "sil-c",
        (
            (124.29, 12.57),
            (124.84, 12.53),
            (125.15, 12.57),
            (125.32, 12.32),
            (125.54, 12.19),
            (125.46, 11.95),
            (125.49, 11.59),
            (125.70, 11.16),
            (125.43, 11.11),
            (125.23, 11.15),
            (125.03, 11.34),
            (124.92, 11.56),
            (125.00, 11.76),
            (124.88, 11.78),
            (124.68, 12.02),
            (124.38, 12.24),
        ),
    ),
    (
        "sil-c",
        (
            (122.03, 11.90),
            (122.61, 11.56),
            (122.84, 11.60),
            (122.89, 11.44),
            (123.16, 11.54),
            (123.02, 11.12),
            (122.80, 10.99),
            (122.77, 10.82),
            (122.20, 10.62),
            (121.95, 10.44),
            (121.96, 10.87),
            (122.05, 11.10),
            (122.10, 11.64),
            (121.89, 11.79),
        ),
    ),
    (
        "sil-c",
        (
            (124.33, 11.54),
            (124.72, 11.32),
            (124.93, 11.37),
            (125.03, 11.21),
            (125.01, 10.79),
            (125.19, 10.58),
            (125.25, 10.26),
            (125.14, 10.19),
            (124.99, 10.37),
            (125.03, 10.03),
            (124.78, 10.17),
            (124.79, 10.78),
            (124.66, 10.96),
            (124.45, 10.92),
        ),
    ),
    (
        "sil-c",
        (
            (124.04, 11.27),
            (124.05, 10.59),
            (123.95, 10.32),
            (123.79, 10.22),
            (123.64, 10.02),
            (123.63, 9.92),
            (123.49, 9.59),
            (123.33, 9.42),
            (123.39, 9.97),
            (123.71, 10.47),
            (123.93, 10.96),
            (123.97, 11.19),
        ),
    ),
    (
        "sil-c",
        (
            (123.22, 10.99),
            (123.51, 10.92),
            (123.57, 10.78),
            (123.34, 10.33),
            (123.16, 9.86),
            (123.15, 9.61),
            (123.31, 9.36),
            (123.23, 9.12),
            (122.99, 9.06),
            (122.87, 9.32),
            (122.56, 9.48),
            (122.41, 9.69),
            (122.47, 9.96),
            (122.86, 10.09),
            (122.82, 10.50),
            (122.98, 10.89),
        ),
    ),
    (
        "sil-c",
        (
            (124.34, 10.16),
            (124.58, 10.03),
            (124.58, 9.75),
            (124.48, 9.75),
            (124.36, 9.63),
            (124.12, 9.60),
            (123.94, 9.62),
            (123.87, 9.68),
            (123.82, 9.82),
            (123.91, 9.92),
            (124.06, 10.00),
            (124.17, 10.14),
        ),
    ),
    (
        "sil-s",
        (
            (125.41, 9.67),
            (125.88, 9.51),
            (126.32, 8.84),
            (126.14, 8.63),
            (126.37, 8.48),
            (126.59, 7.33),
            (126.19, 6.85),
            (126.19, 6.31),
            (125.82, 7.33),
            (125.40, 6.80),
            (125.67, 5.98),
            (125.29, 5.63),
            (125.27, 6.03),
            (125.04, 5.87),
            (124.21, 6.23),
            (123.99, 6.99),
            (124.21, 7.40),
            (123.97, 7.66),
            (123.49, 7.81),
            (123.39, 7.41),
            (123.10, 7.70),
            (122.47, 7.64),
            (122.18, 7.00),
            (121.96, 6.97),
            (122.13, 7.81),
            (122.39, 8.05),
            (122.91, 8.16),
            (123.43, 8.70),
            (123.85, 8.43),
            (123.75, 8.06),
            (124.16, 8.20),
            (124.45, 8.61),
            (124.73, 8.56),
            (124.87, 8.97),
            (125.14, 8.87),
            (125.50, 9.01),
        ),
    ),
)
# (lon, lat, r, ring) — decorative marks on the silhouette, not species centroids.
_MARK_DOTS = (
    (120.95, 17.50, 1.15, False),
    (121.10, 16.15, 1.70, True),
    (121.40, 14.70, 1.10, False),
    (123.40, 13.30, 1.05, False),
    (118.45, 9.55, 1.45, True),
    (122.40, 11.20, 1.05, False),
    (123.00, 10.10, 1.60, True),
    (125.10, 11.70, 1.05, False),
    (124.65, 8.40, 1.10, False),
    (125.30, 7.20, 1.65, True),
    (124.40, 7.30, 1.05, False),
)


def _mark_xy(lon: float, lat: float) -> tuple[float, float]:
    x = (lon - _MARK_LON0) * _MARK_SCALE
    y = (_MARK_LAT0 - lat) * _MARK_SCALE
    return (x, y)


def _clamp_handle(
    vx: float, vy: float, ax: float, ay: float, bx: float, by: float
) -> tuple[float, float]:
    """Keep a cubic handle from swallowing a narrow isthmus (Bicol, Zamboanga)."""
    length = math.hypot(vx, vy)
    limit = _MARK_CLAMP * math.hypot(bx - ax, by - ay)
    if length > limit and length > 1e-9:
        scale = limit / length
        return (vx * scale, vy * scale)
    return (vx, vy)


def _smooth_ring(pts: list[tuple[float, float]]) -> str:
    """Closed coast as one cubic path. pathLength on the element normalizes the draw."""
    n = len(pts)
    k = _MARK_CURVE
    parts = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        h1 = _clamp_handle(
            (p2[0] - p0[0]) * k, (p2[1] - p0[1]) * k, p1[0], p1[1], p2[0], p2[1]
        )
        h2 = _clamp_handle(
            (p1[0] - p3[0]) * k, (p1[1] - p3[1]) * k, p2[0], p2[1], p1[0], p1[1]
        )
        c1 = (p1[0] + h1[0], p1[1] + h1[1])
        c2 = (p2[0] + h2[0], p2[1] + h2[1])
        parts.append(
            f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )
    return " ".join(parts) + " Z"


def _preface_mark() -> str:
    """Archipelago silhouette, decorative dots, and one leaf. CSS draws them."""
    islands = []
    for klass, ring in _MARK_ISLANDS:
        d = _smooth_ring([_mark_xy(lon, lat) for lon, lat in ring])
        islands.append(f'<path class="hra-sil {klass}" pathLength="100" d="{d}"/>')
    dots = []
    for lon, lat, radius, ring in _MARK_DOTS:
        x, y = _mark_xy(lon, lat)
        kind = "dot ring" if ring else "dot"
        # Latitude bands, not inline styles — Streamlit's sanitizer may drop style.
        band = "d1" if lat > 15 else "d2" if lat > 12 else "d3" if lat > 9 else "d4"
        dots.append(
            f'<circle class="{kind} {band}" cx="{x:.1f}" cy="{y:.1f}" r="{radius}"/>'
        )
    # Lanceolate leaf: petiole runs into the midrib, then the blade, then laterals.
    # Coordinates sit in the sea east of the archipelago.
    leaf = (
        '<g class="hra-leaf">'
        '<path class="draw d-stem" pathLength="100" d="M 197.5 165.1 C 196.9 157.1 196.5 151.1 196.7 145.1 C 196.9 125.1 196.7 99.1 196.3 73.1"/>'
        '<path class="draw d-blade" pathLength="100" d="M 196.5 147.1 C 187.5 143.1 179.5 129.1 178.5 113.1 C 177.5 97.1 183.5 79.1 191.5 63.1 C 194.5 57.1 196.5 53.1 197.5 51.1 C 199.5 57.1 204.5 69.1 209.5 87.1 C 215.5 107.1 216.5 127.1 209.5 141.1 C 204.5 151.1 199.5 151.1 196.5 147.1 Z"/>'
        '<path class="draw d-vein" pathLength="100" d="M 196.6 131.1 C 190.5 125.1 185.5 117.1 181.5 107.1"/>'
        '<path class="draw d-vein" pathLength="100" d="M 196.7 119.1 C 202.5 113.1 207.5 103.1 210.5 93.1"/>'
        '<path class="draw d-vein" pathLength="100" d="M 196.6 105.1 C 191.5 99.1 187.5 91.1 185.5 83.1"/>'
        '<path class="draw d-vein" pathLength="100" d="M 196.7 93.1 C 200.7 88.6 203.7 83.9 205.1 79.6"/>'
        "</g>"
    )
    return (
        '<svg class="hra-mark" viewBox="2 0 226 218" fill="none" aria-hidden="true">'
        f"{''.join(islands)}{''.join(dots)}{leaf}"
        "</svg>"
    )


def preload_markup(weights: dict, *, force_motion: bool = False) -> str:
    """One-shot preface. The stylesheet owns timing, lift, and the mark.

    ``force_motion`` is set only for Replay. The reduced-motion rule still
    removes an automatic sheet; this class opts that one pass back in.
    """
    formula = formula_line(weights)
    root = "hra-preload hra-force-motion" if force_motion else "hra-preload"
    return (
        f'<div class="{root}">'
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
