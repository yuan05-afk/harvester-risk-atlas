"""Harvester Risk Atlas — Streamlit demo (EthnoHACK 2026 Track 3)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harvester_risk_atlas.config import (  # noqa: E402
    HPI_CSV,
    OCCURRENCES_PARQUET,
    DATA_PROCESSED,
    HPI_WEIGHTS,
)
from harvester_risk_atlas.hpi import dossier_actions, hpi_formula_markdown  # noqa: E402
from harvester_risk_atlas.names import resolve_query  # noqa: E402
from harvester_risk_atlas.pdf_brief import render_field_brief_html  # noqa: E402
from harvester_risk_atlas.archetypes import (  # noqa: E402
    assign_archetypes,
    archetype_summary,
    pick_demo_species,
)
from harvester_risk_atlas.charts import (  # noqa: E402
    component_bar,
    component_waterfall,
    hpi_distribution,
    compare_components,
    decade_histogram,
    fig_to_png_bytes,
    fig_to_html_bytes,
)
from harvester_risk_atlas.suitability import suitability_sketch  # noqa: E402

st.set_page_config(
    page_title="Harvester Risk Atlas",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = (ROOT / "app" / "styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

RISK_COLORS = {
    "Lower relative pressure": "#40916c",
    "Moderate": "#b08968",
    "Higher relative pressure": "#9b2226",
}

WORKFLOW_PAGES = [
    "Map",
    "Species dossier",
    "Field brief",
    "Compare",
    "Methods",
]
STEP_META = [
    ("1", "Explore map"),
    ("2", "Species dossier"),
    ("3", "Field brief"),
]

DEMO_CAPTIONS = {
    "map": (
        "Demo · Step 1",
        "Markers show species centroids on Esri gray canvas, sized by HPI. "
        "Abutra (Arcangelisia flava) sits in the moderate band with a strong harvest-proxy signal — "
        "a clear judging example of wild-collection pressure.",
    ),
    "dossier": (
        "Demo · Step 2",
        "Open the dossier for component breakdown, data gaps (IUCN not_queried until token), "
        "risk archetype chip, and occurrence decade histogram from GBIF years.",
    ),
    "brief": (
        "Demo · Step 3",
        "Download the HTML field brief for stewardship talking points — research/education only, "
        "never a permit or medical claim.",
    ),
}


@st.cache_data
def load_hpi(_mtime: float = 0.0) -> pd.DataFrame:
    path = HPI_CSV
    if not path.exists():
        alt = DATA_PROCESSED / "hpi_scores.parquet"
        if alt.exists():
            return pd.read_parquet(alt)
        raise FileNotFoundError("Run scripts/compute_hpi.py first")
    return pd.read_csv(path)


@st.cache_data
def load_occurrences() -> pd.DataFrame:
    if OCCURRENCES_PARQUET.exists():
        return pd.read_parquet(OCCURRENCES_PARQUET)
    raw = ROOT / "data" / "raw" / "gbif_occurrences_sample.csv"
    if raw.exists():
        return pd.read_csv(raw)
    return pd.DataFrame()


@st.cache_data
def load_with_archetypes(_mtime: float = 0.0) -> pd.DataFrame:
    hpi = load_hpi(_mtime)
    return assign_archetypes(hpi)


def band_class(band: str) -> str:
    if not isinstance(band, str):
        return ""
    if band.startswith("Lower"):
        return "low"
    if band.startswith("Moderate"):
        return "mid"
    return "high"


def header():
    st.markdown(
        """
        <div class="hra-header">
          <div class="hra-kicker">EthnoHACK 2026 · Track 3 · Biodiversity &amp; Sustainability</div>
          <h1>Harvester Risk Atlas</h1>
          <p class="hra-sub">Map medicinal-plant harvest and climate pressure across the Philippines / SEA.
          Select a species for a risk dossier. Research and education only.</p>
        </div>
        <div class="hra-disclaimer">
          <strong>Disclaimer.</strong> Not medical advice. Not a harvest permit or Red List assessment.
          Ethnobotany notes describe cultural/traditional context only. IUCN categories are never invented;
          live Red List lookup requires an API token.
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_steps(active_page: str):
    """Subtle 1→2→3 indicator; Compare/Methods sit outside the primary path."""
    idx = {"Map": 0, "Species dossier": 1, "Field brief": 2}.get(active_page, -1)
    parts = []
    for i, (num, label) in enumerate(STEP_META):
        cls = "step"
        if i == idx:
            cls += " active"
        elif 0 <= i < idx:
            cls += " done"
        parts.append(f'<span class="{cls}"><span class="num">{num}</span>{label}</span>')
        if i < len(STEP_META) - 1:
            parts.append('<span class="sep">→</span>')
    st.markdown(f'<div class="hra-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def demo_caption(key: str, enabled: bool):
    if not enabled or key not in DEMO_CAPTIONS:
        return
    tag, body = DEMO_CAPTIONS[key]
    st.markdown(
        f'<div class="hra-demo-caption"><span class="tag">{tag}</span>{body}</div>',
        unsafe_allow_html=True,
    )


def map_color(band: str) -> str:
    return RISK_COLORS.get(band, "#86868b")


def build_map(
    hpi: pd.DataFrame,
    occ: pd.DataFrame,
    focus: str | None,
    color_by_archetype: bool = False,
) -> folium.Map:
    pts = hpi.dropna(subset=["lat_mean", "lon_mean"])
    center = [12.5, 122.0]
    if focus and focus in pts["scientific_name"].values:
        row = pts.loc[pts["scientific_name"] == focus].iloc[0]
        center = [float(row["lat_mean"]), float(row["lon_mean"])]
    m = folium.Map(
        location=center,
        zoom_start=6 if not focus else 8,
        tiles="Esri.WorldGrayCanvas",
        control_scale=True,
    )

    # Archetype palette (muted, not rainbow chrome)
    arch_palette = ["#2d6a4f", "#52796f", "#b08968", "#6e6e73", "#9b2226"]
    arch_labels = (
        sorted(pts["archetype_label"].dropna().unique())
        if color_by_archetype and "archetype_label" in pts.columns
        else []
    )
    arch_color = {lab: arch_palette[i % len(arch_palette)] for i, lab in enumerate(arch_labels)}

    cluster = MarkerCluster(name="Species centroids", showCoverageOnHover=False).add_to(m)
    for _, r in pts.iterrows():
        if color_by_archetype and arch_labels:
            col = arch_color.get(str(r.get("archetype_label")), "#86868b")
        else:
            col = map_color(str(r["hpi_band"]))
        arch = r.get("archetype_label", "")
        popup_html = (
            f"<b>{r['scientific_name']}</b><br/>"
            f"{r.get('vernacular_ph','')}<br/>"
            f"HPI <span style='font-family:monospace'>{float(r['hpi']):.3f}</span> · {r['hpi_band']}"
        )
        if arch:
            popup_html += f"<br/><span style='color:#6e6e73'>{arch}</span>"
        folium.CircleMarker(
            location=[r["lat_mean"], r["lon_mean"]],
            radius=7 + 8 * float(r["hpi"]),
            color=col,
            fill=True,
            fill_opacity=0.75,
            weight=1,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{r['scientific_name']} · {float(r['hpi']):.3f}",
        ).add_to(cluster)

    if focus and not occ.empty:
        sub = occ[occ["scientific_name"] == focus].dropna(subset=["lat", "lon"])
        haze = folium.FeatureGroup(name="Occurrence sample", show=True)
        for _, p in sub.head(120).iterrows():
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=2,
                color="#1d1d1f",
                fill=True,
                fill_opacity=0.25,
                weight=0,
            ).add_to(haze)
        haze.add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def chart_download(fig, stem: str):
    """HTML always; PNG if kaleido present."""
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download chart (HTML)",
            data=fig_to_html_bytes(fig),
            file_name=f"{stem}.html",
            mime="text/html",
            key=f"dl_html_{stem}",
        )
    png = fig_to_png_bytes(fig)
    with c2:
        if png:
            st.download_button(
                "Download chart (PNG)",
                data=png,
                file_name=f"{stem}.png",
                mime="image/png",
                key=f"dl_png_{stem}",
            )
        else:
            st.caption("PNG export needs kaleido (optional). HTML works offline.")


def data_gaps_panel(row: pd.Series):
    flags = []
    for key, label in [
        ("climate_imputed", "Climate component imputed"),
        ("harvest_imputed", "Harvest component imputed"),
        ("pa_gap_imputed", "PA-gap component imputed"),
    ]:
        val = row.get(key)
        if bool(val) is True or str(val).lower() == "true":
            flags.append(f"<li><span class='gap-flag'>imputed</span> {label}</li>")

    n = int(row.get("n_occurrences") or 0)
    if n == 0:
        flags.append(
            "<li><span class='gap-flag'>missing</span> No GBIF sample points in demo extract "
            f"({row.get('data_source_note') or 'no_occurrences'})</li>"
        )
    elif n < 15:
        flags.append(
            f"<li><span class='gap-flag'>sparse</span> Low GBIF sample size (n={n})</li>"
        )

    iucn_status = str(row.get("iucn_status") or "not_queried")
    if iucn_status != "ok":
        flags.append(
            f"<li><span class='gap-flag'>{iucn_status}</span> IUCN Red List not queried — "
            "category never invented. Set IUCN_API_TOKEN later.</li>"
        )

    clim = row.get("climate_source") or row.get("climate_method") or "not documented"
    pa = row.get("pa_source") or row.get("pa_method") or "not documented"
    flags.append(f"<li><span class='gap-flag'>source</span> Climate: {clim}</li>")
    flags.append(f"<li><span class='gap-flag'>source</span> Protected areas: {pa}</li>")

    if not any("imputed" in f or "missing" in f or "sparse" in f or "not_queried" in f for f in flags[:4]):
        # still show sources; add clean note
        flags.insert(0, "<li><span class='gap-flag'>ok</span> No component imputations for this species</li>")

    st.markdown(
        f"<div class='hra-gaps'><h3>Data gaps</h3><ul>{''.join(flags)}</ul></div>",
        unsafe_allow_html=True,
    )


def dossier(row: pd.Series, occ: pd.DataFrame, demo: bool):
    band = str(row.get("hpi_band", ""))
    bc = band_class(band)
    arch = row.get("archetype_label") or ""
    chip = f'<span class="hra-chip">{arch}</span>' if arch else ""
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem">
          <span class="hra-kicker">{row.get('family','')}</span>
          <h2 style="margin:0.15rem 0 0.15rem 0">{row['scientific_name']}</h2>
          <div style="color:#6e6e73">{row.get('vernacular_ph','')}</div>
          <div style="margin-top:0.5rem">
            <span class="hra-band {bc}">{band}</span>
            {chip}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    demo_caption("dossier", demo)

    hpi_v = float(row["hpi"])
    conf = float(row.get("hpi_confidence", 0))
    st.markdown(
        f"""
        <div class="hra-metrics">
          <div class="hra-metric"><div class="label">HPI</div>
            <div class="value">{hpi_v:.3f}</div>
            <div class="hint">confidence {conf:.2f}</div></div>
          <div class="hra-metric"><div class="label">Rarity</div>
            <div class="value">{float(row['component_rarity']):.3f}</div></div>
          <div class="hra-metric"><div class="label">Climate</div>
            <div class="value">{float(row['component_climate']):.3f}</div></div>
          <div class="hra-metric"><div class="label">Harvest</div>
            <div class="value">{float(row['component_harvest']):.3f}</div></div>
          <div class="hra-metric"><div class="label">PA gap</div>
            <div class="value">{float(row['component_pa_gap']):.3f}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_bar, tab_wf = st.tabs(["Component scores", "Weighted waterfall"])
    with tab_bar:
        fig_bar = component_bar(row)
        st.plotly_chart(fig_bar, use_container_width=True)
        chart_download(fig_bar, f"hpi_components_{row['scientific_name'].replace(' ', '_')}")
    with tab_wf:
        fig_wf = component_waterfall(row)
        st.plotly_chart(fig_wf, use_container_width=True)
        chart_download(fig_wf, f"hpi_waterfall_{row['scientific_name'].replace(' ', '_')}")

    data_gaps_panel(row)

    # Decade histogram from GBIF year
    if not occ.empty:
        sub = occ[occ["scientific_name"] == row["scientific_name"]]
        fig_dec = decade_histogram(sub, title=f"GBIF sample by decade — {row['scientific_name']}")
        if fig_dec is not None:
            st.plotly_chart(fig_dec, use_container_width=True)
            chart_download(fig_dec, f"decades_{row['scientific_name'].replace(' ', '_')}")
        else:
            st.caption("No eventDate/year on this species’ GBIF sample — decade histogram skipped.")

    c1, c2 = st.columns(2)
    with c1:
        lat, lon = row.get("lat_mean"), row.get("lon_mean")
        where = (
            f"Centroid ≈ {float(lat):.3f}°N, {float(lon):.3f}°E · "
            f"n={int(row.get('n_occurrences') or 0)} GBIF sample points"
            if pd.notna(lat)
            else "No georeferenced sample points in demo extract."
        )
        st.markdown(
            f'<div class="hra-card"><h3>Where</h3><p>{where}</p></div>',
            unsafe_allow_html=True,
        )
        clim_note = row.get("climate_method") or row.get("climate_source") or "climate method n/a"
        pa_note = row.get("pa_source") or row.get("pa_method") or "PA source n/a"
        dist = row.get("mean_dist_to_pa_km")
        dist_s = (
            f"{float(dist):.1f} km mean distance to PA"
            if dist == dist and dist is not None
            else "distance n/a"
        )
        frac = row.get("frac_in_protected", row.get("frac_in_protected_proxy"))
        frac_s = (
            f"{float(frac)*100:.0f}% points in PA"
            if frac == frac and frac is not None
            else "overlap n/a"
        )
        st.markdown(
            f'<div class="hra-card"><h3>Stress</h3><p>{hpi_formula_markdown()}</p>'
            f'<p style="margin-top:0.5rem;font-size:0.85rem;color:#6e6e73">'
            f'<strong>Climate:</strong> {clim_note}<br/>'
            f'<strong>PA:</strong> {frac_s} · {dist_s}<br/>'
            f'<span style="font-size:0.8rem">{pa_note}</span></p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        iucn_cat = row.get("iucn_category") or row.get("iucn_category_code")
        iucn_status = row.get("iucn_status") or "not_queried"
        if iucn_cat and str(iucn_status) == "ok":
            iucn_line = f"IUCN Red List: <strong>{iucn_cat}</strong>"
            if row.get("iucn_year"):
                iucn_line += f" ({row.get('iucn_year')})"
        else:
            iucn_line = (
                f"IUCN Red List: <em>{iucn_status}</em> — category not shown (never invented)"
            )
        iucn_note = row.get("iucn_note") or row.get("demo_iucn_note") or ""
        st.markdown(
            f'<div class="hra-card"><h3>Why it matters</h3><p>{row.get("notes","")}</p>'
            f'<p style="margin-top:0.65rem">{iucn_line}</p>'
            f'<p style="margin-top:0.35rem;color:#6e6e73;font-size:0.85rem">{iucn_note}</p></div>',
            unsafe_allow_html=True,
        )
        acts = dossier_actions(row.to_dict())
        lis = "".join(f"<li>{a}</li>" for a in acts)
        st.markdown(
            f'<div class="hra-card"><h3>What to do</h3><ul class="hra-actions">{lis}</ul></div>',
            unsafe_allow_html=True,
        )

    # Exploratory suitability (collapsed)
    with st.expander("Exploratory suitability sketch (not an SDM)", expanded=False):
        sketch = suitability_sketch(occ, str(row["scientific_name"]), row)
        st.caption(sketch["caveat"])
        if sketch["ok"]:
            st.markdown(
                f"Presence points used: **{sketch['n_presence']}** · "
                f"3-fold CV accuracy ≈ **{sketch['cv_score']:.2f}**"
            )
            imp = sketch.get("feature_importance") or {}
            if imp:
                imp_df = pd.DataFrame(
                    {"feature": list(imp.keys()), "importance": list(imp.values())}
                ).sort_values("importance", ascending=False)
                st.dataframe(imp_df, hide_index=True, use_container_width=True)
        else:
            st.caption(sketch["message"])


def field_brief_page(row: pd.Series, demo: bool):
    demo_caption("brief", demo)
    st.markdown(f"### Field brief — *{row['scientific_name']}*")
    st.caption(f"{row.get('vernacular_ph','')} · {row.get('hpi_band','')} · HPI {float(row['hpi']):.3f}")
    acts = dossier_actions(row.to_dict())
    html = render_field_brief_html(row.to_dict(), acts)
    components.html(html, height=520, scrolling=True)
    st.download_button(
        "Download field brief (HTML)",
        data=html.encode("utf-8"),
        file_name=f"field_brief_{row['scientific_name'].replace(' ', '_')}.html",
        mime="text/html",
        type="primary",
    )


def compare_page(hpi: pd.DataFrame):
    st.markdown("### Compare species")
    st.caption("Side-by-side HPI components and key metrics. Pick any two from the atlas cohort.")
    names = hpi.sort_values("hpi", ascending=False)["scientific_name"].tolist()
    default_a = names[0] if names else None
    default_b = names[1] if len(names) > 1 else names[0]
    # Prefer abutra vs banaba when present
    if "Arcangelisia flava" in names:
        default_a = "Arcangelisia flava"
    if "Lagerstroemia speciosa" in names:
        default_b = "Lagerstroemia speciosa"
    c1, c2 = st.columns(2)
    with c1:
        a = st.selectbox("Species A", names, index=names.index(default_a) if default_a in names else 0)
    with c2:
        b = st.selectbox(
            "Species B",
            names,
            index=names.index(default_b) if default_b in names else min(1, len(names) - 1),
        )
    if a == b:
        st.info("Select two different species.")
        return
    row_a = hpi.loc[hpi["scientific_name"] == a].iloc[0]
    row_b = hpi.loc[hpi["scientific_name"] == b].iloc[0]

    fig = compare_components(row_a, row_b)
    st.plotly_chart(fig, use_container_width=True)
    chart_download(fig, f"compare_{a.replace(' ','_')}_vs_{b.replace(' ','_')}")

    def _metric_block(r: pd.Series) -> str:
        arch = r.get("archetype_label") or "—"
        return f"""
        <div class="hra-card">
          <h3>{r['scientific_name']}</h3>
          <p style="color:#6e6e73;margin-bottom:0.5rem">{r.get('vernacular_ph','')}</p>
          <p><span class="hra-mono">{float(r['hpi']):.3f}</span> · {r.get('hpi_band','')}</p>
          <p style="margin-top:0.35rem">Confidence <span class="hra-mono">{float(r.get('hpi_confidence',0)):.2f}</span>
            · n={int(r.get('n_occurrences') or 0)}</p>
          <p style="margin-top:0.5rem"><span class="hra-chip">{arch}</span></p>
          <p style="margin-top:0.65rem;font-size:0.85rem;color:#6e6e73">
            R {float(r['component_rarity']):.3f} ·
            C {float(r['component_climate']):.3f} ·
            H {float(r['component_harvest']):.3f} ·
            P {float(r['component_pa_gap']):.3f}
          </p>
          <p style="margin-top:0.35rem;font-size:0.8rem;color:#86868b">
            IUCN: {r.get('iucn_status') or 'not_queried'}
          </p>
        </div>
        """

    st.markdown(
        f'<div class="hra-compare-grid">{_metric_block(row_a)}{_metric_block(row_b)}</div>',
        unsafe_allow_html=True,
    )


def methods_page(hpi: pd.DataFrame):
    st.markdown("## Methods & data sources")
    st.markdown(hpi_formula_markdown())
    st.markdown(
        f"""
**Weights (v1.1):** rarity `{HPI_WEIGHTS['rarity']}`, climate `{HPI_WEIGHTS['climate_stress']}`,
harvest `{HPI_WEIGHTS['harvest_proxy']}`, PA gap `{HPI_WEIGHTS['pa_gap']}`.

See `docs/METHODS.md` and `docs/DESIGN.md` for full formulas, licenses, and AI disclosure.
"""
    )
    st.markdown(
        """
| Source | Role | License / access |
|--------|------|------------------|
| GBIF occurrences | Presence points | GBIF terms; cite datasets |
| Seed vernacular list | PH common names | Curated for demo |
| IUCN Red List API v4 | Threat status (dossier only) | Free token; never invented; not in HPI |
| WorldClim 2.1 bio1/12/15 | Climate stress (SEA clip) | Research use; cite Fick & Hijmans 2017 |
| WDPCA Philippines (HDX) | PA overlap / distance | Protected Planet / WDPA terms |
"""
    )
    st.markdown("### HPI distribution")
    fig = hpi_distribution(hpi)
    st.plotly_chart(fig, use_container_width=True)
    chart_download(fig, "hpi_distribution_cohort")

    st.markdown("### Risk archetypes")
    st.caption(
        "KMeans on standardized HPI components (R, C, H, P). Labels describe which "
        "component sits above the cohort mean — not IUCN categories."
    )
    summary = archetype_summary(hpi)
    if not summary.empty:
        st.dataframe(
            summary.rename(
                columns={
                    "archetype": "Archetype",
                    "n": "n",
                    "mean_hpi": "Mean HPI",
                    "mean_rarity": "Mean R",
                    "mean_climate": "Mean C",
                    "mean_harvest": "Mean H",
                    "mean_pa_gap": "Mean P",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    st.markdown(
        """
### Exploratory suitability sketch
Optional RandomForest presence/background on lat/lon + species-level WorldClim means.
**Not an SDM** — uniform SEA background, no spatial CV, bioclim broadcast from species means.
See dossier expander per species.
"""
    )


def continue_to(label: str, target_page: str):
    st.markdown('<div class="hra-continue"></div>', unsafe_allow_html=True)
    if st.button(label, type="primary", key=f"continue_{target_page}"):
        st.session_state["page"] = target_page
        st.session_state["nav_radio"] = target_page
        st.rerun()


def main():
    header()
    try:
        mtime = HPI_CSV.stat().st_mtime if HPI_CSV.exists() else 0.0
        hpi = load_with_archetypes(mtime)
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    occ = load_occurrences()

    if "nav_radio" not in st.session_state:
        st.session_state["nav_radio"] = "Map"
    if "page" not in st.session_state:
        st.session_state["page"] = st.session_state["nav_radio"]
    if "selected" not in st.session_state:
        st.session_state["selected"] = None
    if "demo_mode" not in st.session_state:
        st.session_state["demo_mode"] = False

    with st.sidebar:
        st.markdown("**Navigate**")
        page = st.radio(
            "Page",
            WORKFLOW_PAGES,
            label_visibility="collapsed",
            key="nav_radio",
        )
        st.session_state["page"] = page

        st.markdown("---")
        demo = st.toggle(
            "Demo mode",
            value=st.session_state["demo_mode"],
            help="Jump to a strong example species with narrative captions for judging video.",
        )
        st.session_state["demo_mode"] = demo
        if demo:
            demo_sp = pick_demo_species(hpi)
            st.session_state["selected"] = demo_sp
            st.caption(f"Demo species: *{demo_sp}*")

        st.markdown("---")
        st.caption("Search scientific or PH vernacular name")
        q = st.text_input("Search", placeholder="e.g. lagundi, banaba, abutra", label_visibility="collapsed")
        selected = st.session_state.get("selected")
        if demo:
            selected = pick_demo_species(hpi)
        elif q.strip():
            hits = resolve_query(q, hpi)
            if hits:
                labels = [
                    f"{h['scientific_name']} ({h['vernacular_ph']})"
                    for h in hits
                    if h.get("scientific_name")
                ]
                choice = st.selectbox("Matches", labels)
                if choice:
                    selected = choice.split(" (")[0]
            else:
                st.caption("No match in seed list.")
        else:
            names = hpi.sort_values("hpi", ascending=False)["scientific_name"].tolist()
            idx = names.index(selected) if selected in names else 0
            selected = st.selectbox("Species", names, index=idx)
        st.session_state["selected"] = selected

        if "archetype_label" in hpi.columns and selected in set(hpi["scientific_name"]):
            arch = hpi.loc[hpi["scientific_name"] == selected, "archetype_label"].iloc[0]
            st.caption(f"Archetype: {arch}")

    workflow_steps(page)

    if page == "Methods":
        methods_page(hpi)
        return

    if page == "Compare":
        compare_page(hpi)
        return

    if page == "Map":
        demo_caption("map", demo)
        color_arch = st.checkbox("Color centroids by risk archetype", value=False)
        st.markdown(
            """<div class="hra-legend">
            <span class="l-low">Lower relative pressure</span>
            <span class="l-mid">Moderate</span>
            <span class="l-high">Higher relative pressure</span>
            </div>""",
            unsafe_allow_html=True,
        )
        m = build_map(hpi, occ, selected, color_by_archetype=color_arch)
        st_folium(m, width=None, height=480, returned_objects=[])

        st.markdown("#### HPI distribution")
        fig_dist = hpi_distribution(hpi, highlight=selected)
        st.plotly_chart(fig_dist, use_container_width=True)
        chart_download(fig_dist, "hpi_distribution_map")

        show_cols = [
            "scientific_name",
            "vernacular_ph",
            "hpi",
            "hpi_band",
            "hpi_confidence",
            "n_occurrences",
        ]
        if "archetype_label" in hpi.columns:
            show_cols.append("archetype_label")
        show = hpi[show_cols].sort_values("hpi", ascending=False)
        st.dataframe(show, use_container_width=True, hide_index=True, height=280)
        continue_to("Continue to species dossier →", "Species dossier")
        return

    if page == "Field brief":
        if selected and selected in set(hpi["scientific_name"]):
            row = hpi.loc[hpi["scientific_name"] == selected].iloc[0]
            field_brief_page(row, demo)
        else:
            st.info("Select a species from the sidebar.")
        return

    # Species dossier
    if selected and selected in set(hpi["scientific_name"]):
        row = hpi.loc[hpi["scientific_name"] == selected].iloc[0]
        dossier(row, occ, demo)
        m = build_map(hpi, occ, selected)
        st.markdown("#### Occurrence context")
        st_folium(m, width=None, height=360, returned_objects=[])
        continue_to("Continue to field brief →", "Field brief")
    else:
        st.info("Select a species from the sidebar.")


if __name__ == "__main__":
    main()
