"""Streamlit layout for Map, Dossier, and Brief."""

from __future__ import annotations

import html
import textwrap

import streamlit as st
from streamlit_folium import st_folium

from hra.brief import brief_html, brief_markdown, brief_pdf, talk_track
from hra.charts import cohort_figure, compare_figure, decade_bins, decade_figure, waterfall_figure
from hra.data import (
    CatalogError,
    by_id,
    category_label,
    demo_species,
    display_name,
    iucn_badge_text,
    label_name,
    load_catalog,
    species_list,
)
from hra.methods import weights_html
from hra.mapping import build_map
from hra.theme import CSS, risk_color

STEPS = ("Map", "Dossier", "Brief")


def _header(title: str, lede: str) -> None:
    st.markdown(
        f"<p class='eyebrow'>EthnoHACK 2026 · Track 3</p>"
        f"<h1 class='page-title'>{html.escape(title)}</h1>"
        f"<p class='lede'>{html.escape(lede)}</p>",
        unsafe_allow_html=True,
    )


def _empty(title: str, body: str) -> None:
    st.markdown(
        f"<div class='empty'><strong>{html.escape(title)}</strong>"
        f"<p class='body'>{html.escape(body)}</p></div>",
        unsafe_allow_html=True,
    )


def _apply_pending() -> None:
    pending = st.session_state.pop("pending_species", None)
    if pending and by_id(pending):
        st.session_state.species = pending
    pending_step = st.session_state.pop("pending_step", None)
    if pending_step in STEPS:
        st.session_state.step = pending_step


def _ensure_state() -> None:
    catalog = species_list()
    demo = demo_species()
    compare = next((row for row in catalog if row["id"] == "boswellia-sacra"), catalog[-1])
    if "species" not in st.session_state:
        st.session_state.species = demo["id"]
    if "compare" not in st.session_state:
        st.session_state.compare = compare["id"]
    if "step" not in st.session_state:
        st.session_state.step = "Map"
    if "demo" not in st.session_state:
        st.session_state.demo = False
    if st.session_state.demo:
        st.session_state.species = demo["id"]
        if any(row["id"] == "boswellia-sacra" for row in catalog):
            st.session_state.compare = "boswellia-sacra"


def _on_demo() -> None:
    if st.session_state.get("demo"):
        demo = demo_species()
        st.session_state.species = demo["id"]
        st.session_state.compare = "boswellia-sacra"
        st.session_state.step = "Map"
        st.session_state.query = ""
        st.session_state.category = "All"


def _filtered(rows: list[dict]) -> list[dict]:
    query = (st.session_state.get("query") or "").strip().casefold()
    category = st.session_state.get("category") or "All"
    kept = []
    for row in rows:
        if category != "All" and category_label(row) != category:
            continue
        blob = " ".join(
            part
            for part in (row.get("common_name"), row["scientific_name"], row.get("family"), category_label(row))
            if part
        ).casefold()
        if query and query not in blob:
            continue
        kept.append(row)
    return kept


def _sidebar(rows: list[dict]) -> None:
    with st.sidebar:
        st.markdown("### Harvester Risk Atlas")
        st.caption("Wild-harvest risk from a cited listing and public occurrence records.")
        st.markdown("<p class='caption'>Workflow</p>", unsafe_allow_html=True)
        for name in STEPS:
            if st.button(
                name,
                key=f"go-{name}",
                type="primary" if st.session_state.step == name else "secondary",
                width="stretch",
            ):
                st.session_state.step = name
                st.rerun()
        st.toggle(
            "Demo mode",
            key="demo",
            on_change=_on_demo,
            help="Keeps the demo species selected and compares it with Boswellia sacra.",
        )
        if st.session_state.get("demo"):
            demo = next(row for row in rows if row.get("demo"))
            other = next(row for row in rows if row["id"] == "boswellia-sacra")
            st.caption(
                f"Demo path: Map, then Dossier, then Brief. {display_name(demo)} stays selected "
                f"and is compared with {display_name(other)}. Open the talk track on the page."
            )
        labels = {}
        for row in rows:
            short = label_name(row)
            labels[row["id"]] = (
                f"{short} · {row['scientific_name']}" if short else row["scientific_name"]
            )
        ids = [row["id"] for row in rows]
        st.selectbox(
            "Species",
            ids,
            format_func=lambda item: labels[item],
            key="species",
            disabled=bool(st.session_state.get("demo")),
        )
        if st.session_state.compare not in ids or st.session_state.compare == st.session_state.species:
            st.session_state.compare = next(item for item in ids if item != st.session_state.species)
        others = [item for item in ids if item != st.session_state.species]
        st.selectbox(
            "Compare with",
            others,
            format_func=lambda item: labels[item],
            key="compare",
            disabled=bool(st.session_state.get("demo")),
        )
        st.caption(
            "HPI is computed in this app. It is not an IUCN index, a trend, or a harvest volume."
        )


def _metric_row(species: dict) -> None:
    score = species["score"]
    iucn = species.get("iucn")
    hpi = "—" if score["hpi"] is None else str(score["hpi"])
    band = "Not scored" if score["band"] is None else score["band"]
    category_note = "No P141 statement in this snapshot" if not iucn else iucn["label"]
    st.markdown(
        "<div class='metric-row'>"
        f"<div><div class='metric-label'>HPI</div>"
        f"<div class='metric-value' style='color:{risk_color(score['band'])}'>{html.escape(hpi)}</div>"
        f"<div class='metric-note'>0–100 when both parts exist</div></div>"
        f"<div><div class='metric-label'>Band</div>"
        f"<div class='metric-value' style='color:{risk_color(score['band'])}'>{html.escape(band)}</div>"
        f"<div class='metric-note'>Color is used for this band only</div></div>"
        f"<div><div class='metric-label'>IUCN</div>"
        f"<div style='margin-top:0.45rem'>{iucn_badge_html(species)}</div>"
        f"<div class='metric-note'>{html.escape(category_note)}</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _component_copy(species: dict) -> None:
    score = species["score"]
    iucn = species.get("iucn")
    occurrences = species.get("occurrences") or {}
    if score["listing"] is None:
        listing = "Unscored. No cited IUCN category in this snapshot."
    else:
        listing = (
            f"{score['listing']} / 50 · {iucn['label']}. "
            f"Source: {iucn.get('source_title') or 'IUCN Red List'}."
        )
    if score["concentration"] is None:
        count = occurrences.get("georeferenced_count") or 0
        concentration = f"Unscored. {count} georeferenced records; 30 are required."
    else:
        country = occurrences.get("top_country_name") or occurrences.get("top_country_code")
        percent = round(float(occurrences["top_country_share"]) * 100)
        concentration = f"{score['concentration']} / 50 · {percent}% of georeferenced records in {country}."
    st.markdown(f"<p class='caption'>Listing</p><p class='body'>{html.escape(listing)}</p>", unsafe_allow_html=True)
    st.markdown(
        f"<p class='caption'>Record concentration</p><p class='body'>{html.escape(concentration)}</p>",
        unsafe_allow_html=True,
    )
    for gap in score["gaps"]:
        st.markdown(f"<p class='caption'>{html.escape(gap)}</p>", unsafe_allow_html=True)


def _catalog_table(rows: list[dict], selected: str) -> None:
    header = (
        "<table class='hra'><thead><tr>"
        "<th>Name</th><th>Scientific name</th><th>IUCN</th><th>HPI</th><th>Band</th>"
        "</tr></thead><tbody>"
    )
    body = []
    for row in rows:
        score = row["score"]
        hpi = "—" if score["hpi"] is None else str(score["hpi"])
        band = "Not scored" if score["band"] is None else score["band"]
        klass = "selected" if row["id"] == selected else ""
        name = label_name(row) or "—"
        body.append(
            f"<tr class='{klass}'><td>{html.escape(name)}</td>"
            f"<td>{html.escape(row['scientific_name'])}</td>"
            f"<td>{iucn_badge_html(row)}</td>"
            f"<td class='num'>{html.escape(hpi)}</td>"
            f"<td>{html.escape(band)}</td></tr>"
        )
    st.markdown(header + "".join(body) + "</tbody></table>", unsafe_allow_html=True)


def iucn_badge_html(species: dict) -> str:
    text = iucn_badge_text(species)
    kind = "badge badge-muted" if text == "IUCN not linked" else "badge"
    return f'<span class="{kind}">{html.escape(text)}</span>'


def how_to_read_html() -> str:
    return (
        "<div class='read-strip'>"
        "<span><strong>Color</strong> HPI band for that species</span>"
        "<span><strong>Number</strong> Records in the cluster, not risk</span>"
        "<span><strong>Next</strong> Select a point, then open the dossier</span>"
        "</div>"
    )


def _weights_expander() -> None:
    with st.expander("Methods · HPI weights"):
        st.markdown(weights_html(), unsafe_allow_html=True)


def _demo_talk() -> None:
    if not st.session_state.get("demo"):
        return
    primary = by_id(st.session_state.get("species"))
    other = by_id(st.session_state.get("compare"))
    if primary is None or other is None or primary["id"] == other["id"]:
        return
    with st.expander("60-second talk track"):
        st.markdown(
            f"<p class='body talk'>{html.escape(talk_track(primary, other))}</p>",
            unsafe_allow_html=True,
        )
        st.caption("Read at a calm pace. About one minute. Every figure is taken from this snapshot.")


def _legend() -> None:
    items = [
        ("Lower", "Lower"),
        ("Moderate", "Moderate"),
        ("Higher", "Higher"),
        ("Severe", "Severe"),
        (None, "Not scored"),
    ]
    swatches = "".join(
        f"<span><i class='swatch' style='background:{risk_color(band)}'></i>{html.escape(label)}</span>"
        for band, label in items
    )
    st.markdown(
        f"<div class='legend'>{swatches}<span>Cluster numbers count records, not risk.</span></div>"
        "<p class='caption'>Esri Light Gray Canvas. Marker color is the species HPI band. "
        "Up to 120 recent georeferenced GBIF records, with duplicate coordinates collapsed.</p>",
        unsafe_allow_html=True,
    )


def _consume_map_click(payload: dict | None) -> None:
    if not payload:
        return
    tooltip = payload.get("tooltip")
    if isinstance(tooltip, dict):
        tooltip = tooltip.get("content") or tooltip.get("text")
    if not tooltip:
        return
    signature = (str(tooltip), payload.get("lat"), payload.get("lng"))
    if signature == st.session_state.get("handled_click"):
        return
    st.session_state.handled_click = signature
    if st.session_state.get("demo"):
        return
    for row in species_list():
        if row["scientific_name"] == str(tooltip) and row["id"] != st.session_state.get("species"):
            st.session_state.pending_species = row["id"]
            st.rerun()
            return


def page_map(rows: list[dict]) -> None:
    _header(
        "Atlas",
        "Find a species, then open its dossier. The map shows where GBIF holds coordinates, not where harvest is allowed.",
    )
    filters = st.columns([2, 1], gap="medium")
    with filters[0]:
        st.text_input("Search", key="query", placeholder="Name, family, or category")
    with filters[1]:
        st.selectbox("Category", ["All", "CR", "EN", "VU", "NT", "LC", "Not recorded"], key="category")
    shown = _filtered(rows)
    st.markdown(how_to_read_html(), unsafe_allow_html=True)
    with st.container(border=True):
        if not shown:
            _empty("No species match", "Clear the search or choose All categories. The catalog itself is unchanged.")
        else:
            atlas = build_map(shown)
            click = st_folium(
                atlas,
                height=480,
                use_container_width=True,
                returned_objects=["last_object_clicked"],
                key="atlas-map",
            )
            _legend()
            _consume_map_click((click or {}).get("last_object_clicked"))
    selected = by_id(st.session_state.species)
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("<h2 class='section-title'>Cohort</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p class='caption'>IUCN categories inside this demo catalog. One color, because category is not the HPI band.</p>",
            unsafe_allow_html=True,
        )
        if shown:
            st.plotly_chart(cohort_figure(shown), width="stretch", theme=None, config={"displayModeBar": False})
        else:
            with st.container(border=True):
                _empty("No cohort to draw", "The category chart appears again when the filter matches a species.")
    with right:
        st.markdown("<h2 class='section-title'>Selected</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            if selected is None:
                _empty("Nothing selected", "Choose a species in the sidebar.")
            elif not shown or selected["id"] not in {row["id"] for row in shown}:
                _empty(
                    f"{label_name(selected) or selected['scientific_name']} is hidden",
                    "It is still selected. Clear the filter to see it on the map.",
                )
            else:
                score = selected["score"]
                if score["complete"]:
                    summary = f"{score['hpi']} · {score['band']}"
                else:
                    summary = "Not scored"
                st.markdown(
                    f"<p class='body'><strong>{html.escape(label_name(selected) or selected['scientific_name'])}</strong></p>"
                    f"<p class='caption'>{html.escape(selected['scientific_name'])}</p>"
                    f"<p class='metric-value' style='color:{risk_color(score['band'])}'>{html.escape(summary)}</p>"
                    f"<p class='caption'>{iucn_badge_html(selected)}</p>",
                    unsafe_allow_html=True,
                )
                if st.button("Open dossier", type="primary"):
                    st.session_state.pending_step = "Dossier"
                    st.rerun()
    st.markdown("<h2 class='section-title'>Catalog</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        if shown:
            _catalog_table(shown, st.session_state.species)
        else:
            _empty("Empty catalog view", "No rows match the current search.")


def page_dossier(species: dict | None) -> None:
    _header(
        "Dossier",
        "Listing and record concentration, then the total. A missing input stays blank rather than becoming a low score.",
    )
    if species is None:
        with st.container(border=True):
            _empty("No species selected", "Choose one from the sidebar, or turn on Demo mode.")
        return
    title = label_name(species) or species["scientific_name"]
    details = species["scientific_name"]
    if title.casefold() == details.casefold():
        details = species.get("family") or ""
    elif species.get("family"):
        details = f"{details} · {species['family']}"
    st.markdown(
        f"<h2 class='section-title'>{html.escape(title)}</h2>"
        + (f"<p class='caption'>{html.escape(details)}</p>" if details else ""),
        unsafe_allow_html=True,
    )
    accepted = species.get("accepted_scientific_name") or ""
    if species.get("gbif_status") == "SYNONYM" and accepted:
        st.caption(f"GBIF treats this name as a synonym of {accepted}. Counts use the accepted taxon.")
    names = species.get("vernacular_names") or []
    if names:
        basis = species.get("common_name_basis")
        listed = ", ".join(names)
        if basis == "gbif-preferred" and species.get("common_name"):
            others = [name for name in names if name.casefold() != species["common_name"].casefold()]
            text = f"Preferred English name on GBIF: {species['common_name']}."
            if others:
                text += " Other recorded names: " + ", ".join(others) + "."
        elif basis == "gbif-most-recorded":
            text = f"English names on GBIF, most frequently recorded first: {listed}."
        else:
            text = f"English names on GBIF, with no single preferred name: {listed}."
        st.markdown(f"<p class='caption'>{html.escape(text)}</p>", unsafe_allow_html=True)
    with st.container(border=True):
        _metric_row(species)
    chart_col, copy_col = st.columns([1.35, 1], gap="large")
    with chart_col:
        st.markdown("<h2 class='section-title'>HPI components</h2>", unsafe_allow_html=True)
        figure = waterfall_figure(species["score"])
        if figure is None:
            with st.container(border=True):
                _empty("Nothing to chart", "Both components are unscored, so there is no bar and no HPI.")
        else:
            st.plotly_chart(figure, width="stretch", theme=None, config={"displayModeBar": False})
            st.markdown(
                "<p class='caption'>Listing is the forest bar. Record concentration is the gray bar, drawn on top of listing when both exist. "
                "Only the HPI total uses a risk color. An unscored part is left off the chart.</p>",
                unsafe_allow_html=True,
            )
    with copy_col:
        st.markdown("<h2 class='section-title'>How the points are built</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            _component_copy(species)
    st.markdown("<h2 class='section-title'>Records by decade</h2>", unsafe_allow_html=True)
    years = (species.get("occurrences") or {}).get("years") or []
    _bins, before = decade_bins(years)
    figure = decade_figure(species)
    if figure is None:
        with st.container(border=True):
            _empty("No dated records", "GBIF did not return a year facet for this species.")
    else:
        st.plotly_chart(figure, width="stretch", theme=None, config={"displayModeBar": False})
        note = "Counts of GBIF occurrence records that have a year. Not harvest volume."
        if before:
            note += f" {before} records dated before 1950 are omitted from the bars and mentioned here."
        if (species.get("occurrences") or {}).get("year_facet_truncated"):
            note += " The year facet hit its cap, so the bars may be incomplete."
        st.markdown(f"<p class='caption'>{html.escape(note)}</p>", unsafe_allow_html=True)
    _weights_expander()
    with st.container(border=True):
        st.markdown("<h2 class='section-title'>Sources</h2>", unsafe_allow_html=True)
        iucn = species.get("iucn")
        occurrences = species["occurrences"]
        if iucn:
            st.markdown(
                f"<p class='body'><a href='{html.escape(iucn['url'])}'>IUCN taxon {html.escape(iucn['iucn_taxon_id'])}</a>"
                f" · {html.escape(iucn.get('source_title') or '')}"
                + (f" · Wikidata reference retrieved {html.escape(iucn['retrieved'])}" if iucn.get("retrieved") else "")
                + "</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p class='body'>IUCN category: not recorded on the Wikidata statement used for this snapshot.</p>",
                unsafe_allow_html=True,
            )
        gbif_code = occurrences.get("gbif_occurrence_iucn_code")
        if gbif_code:
            st.markdown(
                f"<p class='caption'>A sampled GBIF occurrence carried the field iucnRedListCategory = {html.escape(str(gbif_code))}. "
                "That field is not used in HPI and is not treated as an assessment citation.</p>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<p class='body'><a href='{html.escape(occurrences['gbif_species_url'])}'>GBIF species record</a>"
            f" · <a href='{html.escape(species['wikidata_url'])}'>Wikidata {html.escape(species['qid'])}</a></p>"
            "<p class='caption'>The retrieval date on a Wikidata reference is when the statement was retrieved, not the IUCN assessment year.</p>",
            unsafe_allow_html=True,
        )


def markdown_html(fragment: str) -> str:
    """Drop leading spaces so Markdown does not turn the markup into a code fence."""
    cleaned = textwrap.dedent(fragment).strip()
    return "\n".join(line.lstrip() for line in cleaned.splitlines())


def _binomial_html(scientific_name: str) -> str:
    parts = scientific_name.split()
    if len(parts) < 2:
        return html.escape(scientific_name)
    genus = html.escape(parts[0])
    epithet = html.escape(" ".join(parts[1:]))
    return f'<span class="genus">{genus}</span><span class="epithet">{epithet}</span>'


def compare_card_html(species: dict) -> str:
    score = species["score"]
    if not score["complete"]:
        value = "Not scored"
    else:
        value = f"{score['hpi']} · {score['band']}"
    scientific = species["scientific_name"]
    short = label_name(species)
    title = ""
    if short and short.casefold() != scientific.casefold():
        title = f'<p class="card-title">{html.escape(short)}</p>'
    fragment = f"""
    <div class="compare-card">
        {title}
        <p class="card-binomial">{_binomial_html(scientific)}</p>
        <p class="metric-value" style="color:{risk_color(score['band'])}">{html.escape(value)}</p>
        <p class="metric-note">{iucn_badge_html(species)}</p>
    </div>
    """
    return markdown_html(fragment)


def page_brief(rows: list[dict]) -> None:
    _header(
        "Brief",
        "Read two species side by side. The note uses only the catalog fields, and you can download it.",
    )
    left = by_id(st.session_state.get("species"))
    right = by_id(st.session_state.get("compare"))
    if left is None or right is None or left["id"] == right["id"]:
        with st.container(border=True):
            _empty("Choose two species", "Set Species and Compare with in the sidebar. Demo mode fills both.")
        return
    left_col, right_col = st.columns(2, gap="large")
    for column, species in ((left_col, left), (right_col, right)):
        with column:
            with st.container(border=True):
                st.markdown(compare_card_html(species), unsafe_allow_html=True)
    figure = compare_figure(left, right)
    if figure is None:
        with st.container(border=True):
            _empty("No comparison", "Both species need to be in the catalog.")
    else:
        st.markdown("<h2 class='section-title'>Component comparison</h2>", unsafe_allow_html=True)
        st.plotly_chart(figure, width="stretch", theme=None, config={"displayModeBar": False})
        st.markdown(
            "<p class='caption'>Bars are listing and record concentration. Missing points are gaps, not zeros. "
            "Risk color stays on the HPI figures above, not on these bars.</p>",
            unsafe_allow_html=True,
        )
    text = brief_markdown(left, right)
    st.markdown("<h2 class='section-title'>Note</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        for paragraph in text.split("\n\n"):
            if paragraph.startswith("#"):
                continue
            st.markdown(f"<p class='body'>{html.escape(paragraph)}</p>", unsafe_allow_html=True)
        _weights_expander()
        stem = f"brief-{left['id']}-{right['id']}"
        html_col, pdf_col, note_col = st.columns(3)
        html_col.download_button(
            "Download HTML",
            data=brief_html(left, right),
            file_name=f"{stem}.html",
            mime="text/html",
        )
        pdf_col.download_button(
            "Download PDF",
            data=brief_pdf(left, right),
            file_name=f"{stem}.pdf",
            mime="application/pdf",
        )
        note_col.download_button(
            "Download note",
            data=text,
            file_name=f"{stem}.md",
            mime="text/markdown",
        )
    del rows


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        load_catalog()
        _ensure_state()
        _apply_pending()
        rows = species_list()
    except CatalogError as exc:
        st.markdown("<h1 class='page-title'>Catalog missing</h1>", unsafe_allow_html=True)
        _empty("Snapshot not built", str(exc))
        return
    _sidebar(rows)
    _demo_talk()
    step = st.session_state.get("step") or "Map"
    if step == "Dossier":
        page_dossier(by_id(st.session_state.get("species")))
    elif step == "Brief":
        page_brief(rows)
    else:
        page_map(rows)
