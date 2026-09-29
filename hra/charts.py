"""Plotly charts. Risk colors are applied only to a scored HPI total."""

from __future__ import annotations

import plotly.graph_objects as go

from hra.data import display_name
from hra.theme import CAPTION, CATEGORY_ORDER, FOREST, INK, SANS, STONE, risk_color

LAYOUT = dict(
    font=dict(family=SANS, color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=8, r=12, t=28, b=8),
    showlegend=False,
    hoverlabel=dict(font_family=SANS, font_size=12),
)

# Paper y=0 is the bottom of the axes. A negative y with the top of the
# legend anchored there keeps the swatch under the plot. y>1 would sit
# beside the title, which is the overlap we are avoiding.
LEGEND_BELOW = dict(
    orientation="h",
    yanchor="top",
    y=-0.28,
    x=0,
    xanchor="left",
    xref="paper",
    yref="paper",
    font=dict(family=SANS, size=12, color=INK),
)


def _base(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(height=height, **LAYOUT, legend=dict(LEGEND_BELOW))
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#e6e6e8",
        tickfont=dict(size=12),
        automargin=True,
        ticklabeloverflow="allow",
    )
    fig.update_yaxes(
        gridcolor="#efeff1",
        zeroline=False,
        tickfont=dict(size=12),
        automargin=True,
        ticklabeloverflow="allow",
    )
    return fig


def _pin_legend(fig: go.Figure, *, show: bool, bottom: int = 36) -> go.Figure:
    """Lock the legend under the axes. Call this after every other layout update."""
    fig.update_layout(
        showlegend=show,
        legend=dict(LEGEND_BELOW),
        margin_b=bottom if show else max(bottom, 36),
    )
    return fig


def cohort_figure(species: list[dict]) -> go.Figure:
    counts = {label: 0 for label in CATEGORY_ORDER}
    for row in species:
        code = (row.get("iucn") or {}).get("code") or "Not recorded"
        counts[code] = counts.get(code, 0) + 1
    labels = [label for label in CATEGORY_ORDER if counts.get(label)]
    values = [counts[label] for label in labels]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=FOREST,
            text=values,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x} species<extra></extra>",
        )
    )
    fig = _base(fig, 280)
    fig.update_layout(margin=dict(l=120, r=36, t=12, b=48), xaxis_title="Species in this catalog")
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(labels)), title=None)
    fig.update_xaxes(range=[0, max(values + [1]) + 1.4], title_font=dict(size=12, color=CAPTION))
    return _pin_legend(fig, show=False, bottom=48)


def decade_bins(years: list[dict]) -> tuple[dict[int, int], int]:
    bins = {decade: 0 for decade in range(1950, 2030, 10)}
    before = 0
    for row in years:
        year = int(row["year"])
        count = int(row["count"])
        if year < 1950:
            before += count
            continue
        decade = min((year // 10) * 10, 2020)
        bins[decade] = bins.get(decade, 0) + count
    return bins, before


def decade_figure(species: dict) -> go.Figure | None:
    years = (species.get("occurrences") or {}).get("years") or []
    if not years:
        return None
    bins, _before = decade_bins(years)
    if sum(bins.values()) == 0:
        return None
    labels = [f"{decade}s" for decade in bins]
    values = list(bins.values())
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=FOREST,
            hovertemplate="%{x}: %{y} records<extra></extra>",
        )
    )
    fig = _base(fig, 300)
    fig.update_layout(margin=dict(l=56, r=16, t=12, b=56), yaxis_title="Records")
    fig.update_yaxes(title_font=dict(size=12, color=CAPTION), rangemode="tozero")
    return _pin_legend(fig, show=False, bottom=56)


def waterfall_figure(score: dict) -> go.Figure | None:
    listing = score.get("listing")
    concentration = score.get("concentration")
    if listing is None and concentration is None:
        return None
    if listing is None or concentration is None:
        value = listing if listing is not None else concentration
        label = "Listing" if listing is not None else "Concentration"
        color = FOREST if listing is not None else STONE
        fig = go.Figure(
            go.Bar(
                x=[label],
                y=[value],
                marker_color=color,
                text=[str(value)],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}: %{y} points<extra></extra>",
            )
        )
        fig = _base(fig, 300)
        fig.update_layout(margin=dict(l=72, r=20, t=16, b=56))
        fig.update_yaxes(range=[0, 62], title="Points (of 50)", title_font=dict(size=12, color=CAPTION))
        return _pin_legend(fig, show=False, bottom=56)

    hpi = score["hpi"]
    fig = go.Figure(
        go.Bar(
            x=["Listing", "Concentration", "HPI"],
            y=[listing, concentration, hpi],
            base=[0, listing, 0],
            marker_color=[FOREST, STONE, risk_color(score.get("band"))],
            text=[str(listing), str(concentration), str(hpi)],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}: %{y} points<extra></extra>",
        )
    )
    fig = _base(fig, 320)
    fig.update_layout(margin=dict(l=64, r=20, t=16, b=64))
    fig.update_yaxes(range=[0, 112], title="Points", title_font=dict(size=12, color=CAPTION), dtick=20)
    fig.add_shape(
        type="line",
        xref="x",
        yref="y",
        x0=0.35,
        x1=0.65,
        y0=listing,
        y1=listing,
        line=dict(color="#d2d2d7", width=1, dash="dot"),
    )
    return _pin_legend(fig, show=False, bottom=64)


def compare_figure(left: dict, right: dict) -> go.Figure | None:
    if left is None or right is None:
        return None
    # Categories sit on Y so the full words stay visible. The legend is not
    # a Plotly title: the page heading lives outside the figure.
    categories = ["Listing", "Concentration"]
    fig = go.Figure()
    for species, color in ((left, FOREST), (right, STONE)):
        score = species["score"]
        fig.add_bar(
            name=display_name(species),
            y=categories,
            x=[score.get("listing"), score.get("concentration")],
            orientation="h",
            marker_color=color,
            hovertemplate="%{fullData.name}<br>%{y}: %{x}<extra></extra>",
        )
    fig = _base(fig, 320)
    fig.update_layout(
        barmode="group",
        margin=dict(l=156, r=28, t=12, b=96),
        xaxis_title="Points",
    )
    fig.update_xaxes(range=[0, 62], title_font=dict(size=12, color=CAPTION))
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=["Concentration", "Listing"],
        title=None,
        tickfont=dict(size=13, color=INK),
    )
    return _pin_legend(fig, show=True, bottom=96)
