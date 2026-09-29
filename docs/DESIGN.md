# Design system — Harvester Risk Atlas

Calm research tool: Apple Maps density + field-science clarity. Map and data are the hero; chrome stays invisible.

## Tokens

### Color
| Token | Value | Use |
|-------|-------|-----|
| `--ink` | `#1d1d1f` | Primary text |
| `--ink-secondary` | `#6e6e73` | Labels, captions |
| `--ink-tertiary` | `#86868b` | Hints, meta |
| `--paper` | `#f5f5f7` | App background (cool gray) |
| `--surface` | `#ffffff` | Cards, panels, chart wells |
| `--hairline` | `#d2d2d7` | Borders, dividers |
| `--accent` | `#2d6a4f` | Single muted forest accent (links, focus, primary actions, non-HPI charts) |
| `--accent-soft` | `#e8f0eb` | Soft accent wash (selected chips, step active) |
| `--risk-low` | `#40916c` | HPI lower band / map markers only |
| `--risk-mid` | `#b08968` | HPI moderate (muted amber-earth) |
| `--risk-high` | `#9b2226` | HPI higher band |
| `--mono-bg` | `#f0f0f2` | Code / metric wells |

**Semantic risk colors** (`--risk-*`) appear **only** on map markers, HPI histogram bars, and band badges — never as page chrome, component-bar fills, or gradients. Non-HPI charts use forest accent shades (`#2d6a4f` → `#52796f` → `#74a892`).

### Type (max 2 families)
1. **UI:** `-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
2. **Metrics / code only:** `"JetBrains Mono", "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace`

No third display font. No Poppins, Geist-as-brand, or decorative serifs.

| Role | Class / element | Size | Weight | Color |
|------|-----------------|------|--------|-------|
| **Title** | `h1` / `.hra-title` | 28–30px (`--fs-title`) | 600 | `--ink`, tracking −0.025em |
| **Section** | `h2` / `.hra-section` | 17–18px (`--fs-section`) | 600 | `--ink` |
| **Body** | `p` / `.hra-body` | 14–15px (`--fs-body`) | 400 | `--ink`, line-height ~1.55 |
| **Caption** | `.hra-caption` / `st.caption` | 12–13px (`--fs-caption`) | 400 | `--ink-secondary` |
| **Mono metrics** | `.hra-metric .value` / `.hra-mono` | 20–24px (`--fs-metric`) | 500 | `--ink`, tabular-nums |

Card section labels (Where / Stress / …) stay uppercase 13px tertiary — not a fifth type role; they are caption-weight labels inside cards.

### Spacing & shape
- Page padding: 24–40px (`.block-container`)
- Column gap: ≥20px (`stHorizontalBlock`)
- Card gap: 16–24px
- Section rhythm: 28–40px after header / steps
- Radius: **8px** default, **12px** max (panels, map iframe, chart wells)
- Borders: 1px `--hairline`; prefer hairlines over shadows
- Shadow (rare): `0 1px 2px rgba(0,0,0,0.04)` only

### Layout anti-overlap rules
- Hide Streamlit header/toolbar/deploy chrome (zero-height header).
- Sidebar `z-index` above main; main canvas `overflow-x: hidden`.
- Folium iframes and Plotly wells get hairline frames + internal padding so titles/legends never sit under map tiles or modebar.
- Step indicator: ≥12px padding, ≥8px between steps/separators; wrap cleanly on narrow widths.
- Map legend is a **panel above the map**, never overlaid on tiles; marker dots ≥10px with hairline stroke.

### Charts (Plotly)
- Paper/plot background: transparent inside a white chart well (CSS), or `#ffffff`.
- Grid: muted `#e8e8ed`; no heavy zerolines.
- Titles: 13px secondary ink; axis titles always set (not empty).
- Legends: horizontal, **below** plot (`y < 0`) or with ≥48px top margin if above — never colliding with title or bars.
- Heights: component bars ≥240px; waterfall ≥280px; HPI histogram ≥280px; compare ≥300px; decade ≥240px.

### Interaction
- Focus ring: 2px `--accent` at 40% opacity
- Buttons: flat fill `--accent` or ghost hairline; no glow
- Map controls: minimal Folium defaults; legend as hairlined panel above map
- Markers: white/ink stroke (`weight ≥ 1.5`) so centroids read on Esri gray canvas

## Banned (anti-slop)
- Purple / aurora / neon gradients, glassmorphism blobs
- Emoji as icons or section markers
- Hero pill + dual CTAs, three equal icon feature cards
- Glow borders, fade-up-everywhere motion
- Marketing fluff (“unlock”, “seamlessly”, “revolutionize”)
- Rainbow chrome outside HPI semantics
- Risk-red/amber on non-HPI component charts

## Copy voice
Plain scientific English. Short dossier labels: **Where / Stress / Why it matters / What to do**. Disclaimer always visible, never cute.

## Map & dossier microcopy

- **How to read this** — Map page only. 2–3 lines under the header strip: HPI color meaning + size cue. No emoji, no dual CTAs.
- **Weights transparency** — Methods expander table (R/C/H/P + weights + one plain sentence why). Match METHODS.md numbers.
- **Demo talk track** — Sidebar under Demo mode only. Numbered 60-sec script; plain scientific English.
- **IUCN badge** — Dossier chip: linked category when `iucn_status=ok`; otherwise muted `IUCN not linked`. Never show a fake LC/VU.
- **Field brief** — HTML + PDF; same structure (Where / Stress / Why / What to do). Typography follows tokens above.

