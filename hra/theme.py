"""Visual tokens. Two families only: UI sans and metric mono."""

SANS = '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'

FOREST = "#1f4d3a"
STONE = "#8a8f98"
MIST = "#d8d8de"
INK = "#1d1d1f"
CAPTION = "#6e6e73"
PAPER = "#ffffff"
CANVAS = "#f5f5f7"
LINE = "#e6e6e8"

RISK_COLORS = {
    "Lower": "#4f6f5b",
    "Moderate": "#a6843d",
    "Higher": "#b85c38",
    "Severe": "#8e3a34",
}
PARTIAL = "#8e8e93"

CATEGORY_ORDER = ["CR", "EN", "VU", "NT", "LC", "Not recorded"]


def risk_color(band: str | None) -> str:
    if band is None:
        return PARTIAL
    return RISK_COLORS.get(band, PARTIAL)


CSS = f"""
<style>
  html, body, [class*="st-"], .stApp {{
    font-family: {SANS};
    color: {INK};
  }}
  .stApp {{
    background: {CANVAS};
  }}
  [data-testid="stHeader"] {{
    background: {CANVAS};
    border-bottom: 1px solid {LINE};
  }}
  [data-testid="stDecoration"] {{
    display: none;
  }}
  section.main > div.block-container {{
    max-width: 1080px;
    padding-top: 1.6rem;
    padding-bottom: 3rem;
  }}
  [data-testid="stSidebar"] {{
    background: #fbfbfd;
    border-right: 1px solid {LINE};
  }}
  [data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.15rem;
  }}
  [data-testid="stSidebar"] h1 {{
    font-size: 1.05rem;
    letter-spacing: -0.015em;
    font-weight: 600;
    margin-bottom: 0.15rem;
  }}
  [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {PAPER};
    border: 1px solid {LINE} !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    padding: 0.35rem 0.85rem 0.9rem;
  }}
  h1.page-title {{
    font-size: 2rem;
    line-height: 1.15;
    font-weight: 600;
    letter-spacing: -0.025em;
    margin: 0.15rem 0 0.4rem;
  }}
  h2.section-title {{
    font-size: 1.05rem;
    line-height: 1.3;
    font-weight: 600;
    letter-spacing: -0.012em;
    margin: 0 0 0.25rem;
  }}
  p.eyebrow, p.lede, p.caption, p.body {{
    margin: 0;
  }}
  p.eyebrow {{
    font-size: 0.75rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: {CAPTION};
    font-weight: 500;
  }}
  p.lede {{
    font-size: 0.98rem;
    line-height: 1.5;
    color: #3a3a3c;
    max-width: 42rem;
    margin-bottom: 0.35rem;
  }}
  p.body {{
    font-size: 0.95rem;
    line-height: 1.55;
    color: {INK};
  }}
  p.caption {{
    font-size: 0.78rem;
    line-height: 1.45;
    color: {CAPTION};
  }}
  .metric-row {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1.25rem;
    margin: 0.35rem 0 0.2rem;
  }}
  .metric-row.two {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
  @media (max-width: 720px) {{
    .metric-row, .metric-row.two {{
      grid-template-columns: 1fr;
    }}
  }}
  .metric-label {{
    font-size: 0.75rem;
    letter-spacing: 0.02em;
    color: {CAPTION};
    font-weight: 500;
  }}
  .metric-value {{
    font-family: {MONO};
    font-size: 1.7rem;
    font-weight: 500;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin-top: 0.15rem;
    font-variant-numeric: tabular-nums;
  }}
  .metric-note {{
    font-size: 0.78rem;
    color: {CAPTION};
    margin-top: 0.1rem;
    text-transform: none;
    letter-spacing: 0;
    line-height: 1.4;
    overflow-wrap: normal;
    word-break: normal;
  }}
  .compare-card {{
    min-width: 0;
  }}
  .compare-card .card-title,
  .compare-card .card-binomial {{
    text-transform: none;
    letter-spacing: 0;
    hyphens: manual;
    overflow-wrap: normal;
    word-break: keep-all;
    line-height: 1.3;
    margin: 0;
  }}
  .compare-card .card-title {{
    font-size: 1.05rem;
    font-weight: 600;
  }}
  .compare-card .card-binomial {{
    margin-top: 0.2rem;
    font-size: 0.95rem;
    font-style: italic;
    color: #3a3a3c;
  }}
  .compare-card .genus,
  .compare-card .epithet {{
    display: inline-block;
    white-space: nowrap;
  }}
  .compare-card .epithet {{
    margin-left: 0.28em;
  }}
  .swatch {{
    display: inline-block;
    width: 0.65rem;
    height: 0.65rem;
    border-radius: 999px;
    margin-right: 0.4rem;
    vertical-align: -1px;
  }}
  .legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.85rem 1.1rem;
    margin-top: 0.7rem;
  }}
  .legend span {{
    font-size: 0.78rem;
    color: #3a3a3c;
  }}
  table.hra {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
  }}
  table.hra th {{
    text-align: left;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: {CAPTION};
    padding: 0.45rem 0.5rem 0.45rem 0;
    border-bottom: 1px solid {LINE};
  }}
  table.hra td {{
    padding: 0.55rem 0.5rem 0.55rem 0;
    border-bottom: 1px solid #f0f0f2;
    vertical-align: baseline;
  }}
  table.hra tr.selected td {{
    background: #f3f7f4;
  }}
  table.hra td.num, .mono {{
    font-family: {MONO};
    font-variant-numeric: tabular-nums;
    font-size: 0.84rem;
  }}
  .empty {{
    padding: 1.1rem 0.2rem 0.4rem;
  }}
  .empty strong {{
    display: block;
    font-weight: 600;
    letter-spacing: -0.01em;
    margin-bottom: 0.25rem;
  }}
  a {{
    color: {FOREST};
    text-decoration-thickness: 1px;
    text-underline-offset: 2px;
  }}
  [data-testid="stPlotlyChart"] {{
    background: transparent;
  }}
  iframe {{
    border: 0 !important;
    border-radius: 8px;
  }}
  div[data-testid="stExpander"] {{
    border: 1px solid {LINE};
    border-radius: 12px;
    background: {PAPER};
  }}
  .stButton > button {{
    border-radius: 980px;
    border: 1px solid #d2d2d7;
    background: {PAPER};
    color: {INK};
    font-weight: 500;
  }}
  .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {{
    background: {FOREST};
    border-color: {FOREST};
    color: white;
  }}
</style>
"""
