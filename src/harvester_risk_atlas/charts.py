"""Plotly chart helpers — muted forest palette, Apple-minimal (DESIGN.md)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ACCENT = "#2d6a4f"
ACCENT_MID = "#52796f"
ACCENT_SOFT = "#74a892"
INK = "#1d1d1f"
INK_SEC = "#6e6e73"
HAIRLINE = "#e8e8ed"
PAPER = "#ffffff"

# Risk colors — HPI bands / histogram ONLY (never component fills)
RISK = {
    "Lower relative pressure": "#40916c",
    "Moderate": "#b08968",
    "Higher relative pressure": "#9b2226",
}

# Forest accent ramp for non-HPI component charts (no risk red/amber)
FOREST_RAMP = {
    "Rarity": ACCENT,
    "Climate": ACCENT_MID,
    "Harvest": "#6b8f71",
    "PA gap": ACCENT_SOFT,
}

WEIGHTS = {"Rarity": 0.30, "Climate": 0.25, "Harvest": 0.25, "PA gap": 0.20}

FONT = dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color=INK, size=12)
LAYOUT_BASE = dict(
    paper_bgcolor=PAPER,
    plot_bgcolor=PAPER,
    font=FONT,
    separators=".,",
    # Never inherit a template that parks legend beside the title.
    template="plotly_white",
)

# Canonical legend: horizontal UNDER the plot (never y>1 / never beside title).
LEGEND_BELOW = dict(
    orientation="h",
    yanchor="top",
    y=-0.22,
    x=0,
    xanchor="left",
    bgcolor="rgba(0,0,0,0)",
    borderwidth=0,
    font=dict(size=11, color=INK_SEC),
    title=dict(text=""),
    itemsizing="constant",
    traceorder="normal",
)

# Bottom margin must clear a horizontal legend under the axes.
MARGIN_WITH_LEGEND = dict(l=72, r=24, t=56, b=110)
MARGIN_NO_LEGEND = dict(l=72, r=24, t=52, b=56)


def _axis(title: str, **extra: Any) -> dict[str, Any]:
    base = dict(
        title=dict(text=title, font=dict(size=11, color=INK_SEC)),
        gridcolor=HAIRLINE,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color=INK_SEC),
        automargin=True,
    )
    base.update(extra)
    return base


def _title(text: str) -> dict[str, Any]:
    """Title anchored high in paper space with pad so it never meets a top legend."""
    return dict(
        text=text,
        font=dict(size=13, color=INK_SEC, family=FONT["family"]),
        x=0.0,
        xanchor="left",
        y=0.98,
        yanchor="top",
        pad=dict(t=4, b=12, l=0, r=0),
    )


def _legend_below(**overrides: Any) -> dict[str, Any]:
    """Horizontal legend under the plot — never beside / over the title."""
    leg = dict(LEGEND_BELOW)
    leg.update(overrides)
    return leg


def _short_name(name: str, max_len: int = 32) -> str:
    name = str(name)
    return name if len(name) <= max_len else name[: max_len - 1] + "…"


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


def component_bar(row: pd.Series | dict[str, Any], title: str = "HPI components (0–1)") -> go.Figure:
    """Horizontal bar of raw component scores [0,1] — forest accents only."""
    comp = _components_from_row(row)
    colors = [FOREST_RAMP[c] for c in comp["Component"]]
    fig = go.Figure(
        go.Bar(
            x=comp["Score"],
            y=comp["Component"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[f"{v:.3f}" for v in comp["Score"]],
            textposition="outside",
            textfont=dict(size=11, color=INK_SEC, family="JetBrains Mono, ui-monospace, monospace"),
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title(title),
        height=280,
        margin=dict(l=88, r=56, t=52, b=48),
        showlegend=False,
        xaxis=_axis("Component score", range=[0, 1.15]),
        yaxis=_axis(
            "",
            categoryorder="array",
            categoryarray=["PA gap", "Harvest", "Climate", "Rarity"],
        ),
    )
    return fig


def component_waterfall(row: pd.Series | dict[str, Any], title: str = "Weighted contribution to HPI") -> go.Figure:
    """Waterfall: weight × component → sum ≈ HPI. Forest accents; total in ink."""
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
            connector={"line": {"color": "#d2d2d7", "width": 1}},
            increasing={"marker": {"color": ACCENT}},
            totals={"marker": {"color": INK}},
            text=[f"{v:.3f}" for v in y],
            textposition="outside",
            textfont=dict(size=11, color=INK_SEC),
            cliponaxis=False,
            hovertemplate="%{x}: %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title(title),
        height=320,
        margin=dict(l=72, r=24, t=52, b=64),
        xaxis=_axis("Weighted term", tickangle=-20),
        yaxis=_axis("Contribution to HPI"),
        showlegend=False,
    )
    return fig


def hpi_distribution(hpi: pd.DataFrame, highlight: str | None = None) -> go.Figure:
    """Global HPI histogram colored by band (risk colors OK here); optional species marker."""
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
        labels={"hpi": "Harvest Pressure Index (HPI)", "hpi_band": "Band", "count": "Species"},
        template="plotly_white",
    )
    fig.update_traces(marker_line_width=0, opacity=0.88)
    if highlight and highlight in set(df["scientific_name"]):
        val = float(df.loc[df["scientific_name"] == highlight, "hpi"].iloc[0])
        short = _short_name(highlight, 28)
        fig.add_vline(
            x=val,
            line_dash="dot",
            line_color=ACCENT,
            line_width=1.5,
            annotation_text=short,
            annotation_position="top",
            annotation_font=dict(size=11, color=ACCENT),
        )
    # Force legend below AFTER px defaults (px parks legend at top-right).
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title("HPI distribution (atlas cohort)"),
        height=320,
        bargap=0.1,
        showlegend=True,
        legend=_legend_below(),
        xaxis=_axis("Harvest Pressure Index (HPI)", range=[0, 1]),
        yaxis=_axis("Number of species"),
        margin=dict(MARGIN_WITH_LEGEND),
    )
    fig.update_layout(legend=_legend_below())  # second pass beats px template merge
    return fig


def compare_components(row_a: pd.Series, row_b: pd.Series) -> go.Figure:
    """Grouped horizontal bars for two species — forest accent vs earth tone (identity, not risk)."""
    comps = ["Rarity", "Climate", "Harvest", "PA gap"]
    keys = ["component_rarity", "component_climate", "component_harvest", "component_pa_gap"]
    name_a = _short_name(row_a.get("scientific_name", "A"))
    name_b = _short_name(row_b.get("scientific_name", "B"))
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name=name_a,
            y=comps,
            x=[float(row_a[k]) for k in keys],
            orientation="h",
            marker_color=ACCENT,
            hovertemplate=f"{name_a} · %{{y}}: %{{x:.3f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name=name_b,
            y=comps,
            x=[float(row_b[k]) for k in keys],
            orientation="h",
            marker_color=ACCENT_MID,
            hovertemplate=f"{name_b} · %{{y}}: %{{x:.3f}}<extra></extra>",
        )
    )
    # Legend ALWAYS below plot (y<=-0.22). Never y>1 — that overlaps the title.
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title("Component comparison (0–1)"),
        height=400,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        showlegend=True,
        legend=_legend_below(y=-0.28),  # two long names → a bit lower + gap under axes
        xaxis=_axis("Component score", range=[0, 1.05]),
        # Category labels only (no axis title) so left ticks are fully visible.
        yaxis=_axis(
            "",
            categoryorder="array",
            categoryarray=["PA gap", "Harvest", "Climate", "Rarity"],
            ticklabelposition="outside",
        ),
        margin=dict(l=96, r=28, t=60, b=120),
    )
    fig.update_layout(legend=_legend_below(y=-0.28))
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
            hovertemplate="%{x}: %{y} records<extra></extra>",
        )
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title=_title(title),
        height=280,
        showlegend=False,
        xaxis=_axis("Decade", tickangle=-30),
        yaxis=_axis("GBIF sample records"),
        margin=dict(l=72, r=20, t=52, b=72),
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
