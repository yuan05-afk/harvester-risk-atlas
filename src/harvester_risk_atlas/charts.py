"""Plotly chart helpers — muted forest palette, Apple-minimal (DESIGN.md)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ACCENT = "#2d6a4f"
INK = "#1d1d1f"
INK_SEC = "#6e6e73"
HAIRLINE = "#e8e8ed"
RISK = {
    "Lower relative pressure": "#40916c",
    "Moderate": "#b08968",
    "Higher relative pressure": "#9b2226",
}
COMP_COLORS = {
    "Rarity": "#2d6a4f",
    "Climate": "#52796f",
    "Harvest": "#b08968",
    "PA gap": "#9b2226",
}
WEIGHTS = {"Rarity": 0.30, "Climate": 0.25, "Harvest": 0.25, "PA gap": 0.20}

FONT = dict(family="Inter, -apple-system, sans-serif", color=INK, size=12)
LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=FONT,
)


def _legend_below() -> dict:
    """Horizontal legend under the axis so it does not share a band with the title."""
    return dict(
        orientation="h",
        yanchor="top",
        y=-0.28,
        x=0,
        xanchor="left",
        title_text="",
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color=INK),
    )


def _title_above(text: str) -> dict:
    return dict(
        text=text,
        x=0,
        xanchor="left",
        y=1,
        yanchor="top",
        pad=dict(b=18, t=0),
        font=dict(size=13, color=INK_SEC, family="Inter, -apple-system, sans-serif"),
    )


def _components_from_row(row: pd.Series | dict[str, Any]) -> pd.DataFrame:
    get = row.get if hasattr(row, "get") else lambda k, d=None: row[k] if k in row.index else d
    return pd.DataFrame(
        {
            "Component": ["Rarity", "Climate", "Harvest", "PA gap"],
            "Score": [
                float(get("component_rarity", 0) or 0),
                float(get("component_climate", 0) or 0),
                float(get("component_harvest", 0) or 0),
                float(get("component_pa_gap", 0) or 0),
            ],
        }
    )


def component_bar(row: pd.Series | dict[str, Any], title: str = "HPI components") -> go.Figure:
    """Horizontal bar of raw component scores [0,1]."""
    comp = _components_from_row(row)
    colors = [COMP_COLORS[c] for c in comp["Component"]]
    fig = go.Figure(
        go.Bar(
            x=comp["Score"],
            y=comp["Component"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=13, color=INK_SEC)),
        height=200,
        margin=dict(l=8, r=12, t=28, b=8),
        showlegend=False,
        xaxis=dict(range=[0, 1], gridcolor=HAIRLINE, zeroline=False, title=""),
        yaxis=dict(title="", categoryorder="array", categoryarray=["PA gap", "Harvest", "Climate", "Rarity"]),
    )
    return fig


def component_waterfall(row: pd.Series | dict[str, Any], title: str = "Weighted contribution to HPI") -> go.Figure:
    """Waterfall: weight × component → sum ≈ HPI."""
    get = row.get if hasattr(row, "get") else lambda k, d=None: row[k] if k in row.index else d
    raw = {
        "Rarity": float(get("component_rarity", 0) or 0),
        "Climate": float(get("component_climate", 0) or 0),
        "Harvest": float(get("component_harvest", 0) or 0),
        "PA gap": float(get("component_pa_gap", 0) or 0),
    }
    weighted = {k: WEIGHTS[k] * raw[k] for k in WEIGHTS}
    measures = ["relative", "relative", "relative", "relative", "total"]
    x = ["Rarity×0.30", "Climate×0.25", "Harvest×0.25", "PA gap×0.20", "HPI"]
    y = [
        weighted["Rarity"],
        weighted["Climate"],
        weighted["Harvest"],
        weighted["PA gap"],
        float(get("hpi", sum(weighted.values())) or 0),
    ]
    fig = go.Figure(
        go.Waterfall(
            measure=measures,
            x=x,
            y=y,
            connector={"line": {"color": "#d2d2d7"}},
            increasing={"marker": {"color": ACCENT}},
            totals={"marker": {"color": "#1d1d1f"}},
            text=[f"{v:.3f}" for v in y],
            textposition="outside",
            hovertemplate="%{x}: %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=13, color=INK_SEC)),
        height=240,
        margin=dict(l=8, r=12, t=28, b=40),
        yaxis=dict(gridcolor=HAIRLINE, zeroline=False, title=""),
        showlegend=False,
    )
    return fig


def hpi_distribution(hpi: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    """Global HPI histogram colored by band; optional species marker."""
    df = hpi.dropna(subset=["hpi"]).copy()
    fig = px.histogram(
        df,
        x="hpi",
        color="hpi_band",
        nbins=12,
        color_discrete_map=RISK,
        category_orders={
            "hpi_band": [
                "Lower relative pressure",
                "Moderate",
                "Higher relative pressure",
            ]
        },
    )
    fig.update_traces(marker_line_width=0, opacity=0.85)
    if highlight and highlight in set(df["scientific_name"]):
        val = float(df.loc[df["scientific_name"] == highlight, "hpi"].iloc[0])
        fig.add_vline(x=val, line_dash="dot", line_color=ACCENT, annotation_text=highlight, annotation_position="top")
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title_above("HPI distribution (atlas cohort)"),
        height=300,
        bargap=0.08,
        showlegend=True,
        legend=_legend_below(),
        xaxis=dict(title="HPI", range=[0, 1], gridcolor=HAIRLINE),
        yaxis=dict(title="Species", gridcolor=HAIRLINE),
        margin=dict(l=48, r=16, t=72, b=108),
    )
    return fig


def compare_components(row_a: pd.Series, row_b: pd.Series) -> go.Figure:
    """Grouped horizontal bars for two species."""
    comps = ["Rarity", "Climate", "Harvest", "PA gap"]
    keys = ["component_rarity", "component_climate", "component_harvest", "component_pa_gap"]
    name_a = str(row_a.get("scientific_name", "A"))
    name_b = str(row_b.get("scientific_name", "B"))
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=name_a,
            y=comps,
            x=[float(row_a[k]) for k in keys],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name=name_b,
            y=comps,
            x=[float(row_b[k]) for k in keys],
            orientation="h",
            marker_color="#b08968",
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title_above("Component comparison"),
        height=360,
        barmode="group",
        showlegend=True,
        legend=_legend_below(),
        xaxis=dict(range=[0, 1], gridcolor=HAIRLINE, title=""),
        yaxis=dict(title=""),
        margin=dict(l=56, r=24, t=72, b=96),
    )
    return fig


def decade_histogram(occ_sub: pd.DataFrame, title: str = "Occurrences by decade") -> go.Figure | None:
    """Decade counts from year (or eventDate). Returns None if no usable dates."""
    if occ_sub is None or occ_sub.empty:
        return None
    years = None
    if "year" in occ_sub.columns and occ_sub["year"].notna().any():
        years = pd.to_numeric(occ_sub["year"], errors="coerce")
    elif "eventDate" in occ_sub.columns and occ_sub["eventDate"].notna().any():
        years = pd.to_datetime(occ_sub["eventDate"], errors="coerce").dt.year
    if years is None or years.dropna().empty:
        return None
    decades = ((years.dropna() // 10) * 10).astype(int)
    counts = decades.value_counts().sort_index()
    fig = go.Figure(
        go.Bar(
            x=[f"{int(d)}s" for d in counts.index],
            y=counts.values,
            marker_color=ACCENT,
            marker_line_width=0,
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, font=dict(size=13, color=INK_SEC)),
        height=200,
        xaxis=dict(title="", tickangle=-30),
        yaxis=dict(title="Records", gridcolor=HAIRLINE),
        margin=dict(l=8, r=12, t=28, b=48),
    )
    return fig


def fig_to_png_bytes(fig: go.Figure) -> bytes | None:
    """Static PNG for slides when kaleido is available; else None."""
    try:
        return fig.to_image(format="png", scale=2, width=900, height=420)
    except Exception:
        return None


def fig_to_html_bytes(fig: go.Figure) -> bytes:
    """Always-available interactive HTML export for slides / judging packet."""
    return fig.to_html(include_plotlyjs="cdn", full_html=True).encode("utf-8")
