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


def preload_markup(weights: dict) -> str:
    """One-shot preface. Opacity only; the stylesheet owns timing."""
    formula = formula_line(weights)
    return f"""
<div class="hra-preload">
  <div class="hra-preload-stage" aria-hidden="true">
    <p class="beat b1"><span class="k">The pressure</span>Medicinal plants in the Philippines and Southeast Asia are still taken from the wild.</p>
    <p class="beat b2"><span class="k">The records</span>Occurrences, climate, harvest, and protected-area cover sit in different datasets. None of them is a field score.</p>
    <p class="beat b3"><span class="k">The wrong stand-in</span>A Red List category does not measure that pressure. This atlas never invents one.</p>
    <p class="beat b4"><span class="k">Harvester Risk Atlas</span>A relative score from four open inputs. Then the map, the dossier, and a field brief.</p>
    <p class="formula beat b4f">{formula}</p>
  </div>
  <div class="hra-preload-bar" aria-hidden="true"></div>
  <a class="hra-preload-skip" href="?intro=skip">Skip</a>
</div>
""".strip()


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
  <table class="hra-parts">
    <thead>
      <tr><th>Term</th><th>What goes in</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Rarity<span>weight {w['rarity']}</span></td>
        <td>Inverted GBIF count, plus an endemism cue from the seed notes.</td>
      </tr>
      <tr>
        <td>Climate stress<span>weight {w['climate_stress']}</span></td>
        <td>WorldClim 2.1 temperature, precipitation, and seasonality on a Southeast Asia clip.</td>
      </tr>
      <tr>
        <td>Harvest proxy<span>weight {w['harvest_proxy']}</span></td>
        <td>Local occurrence density, the share of recent records, and a literature harvest flag.</td>
      </tr>
      <tr>
        <td>Protected-area gap<span>weight {w['pa_gap']}</span></td>
        <td>Share of points outside WDPCA Philippines, with a small distance boost when the gap is large.</td>
      </tr>
    </tbody>
  </table>
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
