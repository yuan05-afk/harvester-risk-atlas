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
| **Mono metrics** | `.hra-metric .value` / `.hra-mono` | 20–22px (`--fs-metric`) | 500 | `--ink`, tabular-nums |

Card section labels (Where / Stress / …) stay uppercase 12–13px tertiary — not a fifth type role; they are caption-weight labels inside cards.

### Spacing & shape
- Page padding: 24–40px (`.block-container`)
- Column gap: ≥18px (`stHorizontalBlock`)
- Card gap: 14–20px; denser dossier metric grid (`minmax(118px)`, 0.6rem gap)
- Section rhythm: ~22–28px after header / steps; hairline dividers on header + continue row
- Radius: **8px** default, **12px** max (panels, map iframe, chart wells)
- Borders: 1px `--hairline`; prefer hairlines over shadows
- Shadow (rare): `0 1px 2px rgba(0,0,0,0.04)` on floating panels / chart wells only

### Layout anti-overlap rules
- Hide Streamlit header/toolbar/deploy chrome (zero-height header).
- Sidebar `z-index` above main; main canvas `overflow-x: hidden`.
- Folium iframes and Plotly wells get hairline frames + internal padding so titles/legends never sit under map tiles or modebar.
- Step indicator: ≥12px padding, ≥8px between steps/separators; wrap cleanly on narrow widths.
- Map legend: **floating hairline panel** above the map (`.hra-legend` + rare hair shadow) and compact on-map Folium panel; marker dots ≥10px with hairline stroke.

### Charts (Plotly)
- Paper/plot background: transparent inside a white chart well (CSS), or `#ffffff`.
- Grid: muted `#e8e8ed`; no heavy zerolines.
- Titles: 13px secondary ink; axis titles always set (not empty).
- Legends: horizontal, **below** plot (`y < 0`) or with ≥48px top margin if above — never colliding with title or bars.
- Heights: component bars ≥240px; waterfall ≥280px; HPI histogram ≥280px; compare ≥300px; decade ≥240px.
- Soft bar `cornerradius` (2–3) on forest-accent bars; risk histogram stays flat-fill.
- **Cohort HPI spark** (dossier): tiny SVG polyline under metrics — selected species as accent tick; no Plotly chrome.

### Interaction & motion
- Focus ring: 2px `--accent` at 40% opacity (`--focus-ring`)
- Buttons: flat fill `--accent` or ghost hairline; no glow; **150ms** hover ease
- Motion = **signal only** (`--dur: 150ms`, `--ease: cubic-bezier(0.25, 0.1, 0.25, 1)`):
  - Step chips (active / done wash)
  - Cards (border + hair shadow on hover)
  - Sidebar radio selected wash
  - Button / input hover + focus
  - Optional **one-shot** map focus pulse (`.hra-pulse`, ~0.9s, plays once)
- Honor `prefers-reduced-motion: reduce` (transitions/animations near-zero).
- **Banned motion:** bounce, spring, page-wide fade-up, staggered card entrances, aurora blobs.
- **Home preface (exception, one shot):** first session only, on Home. Four sentences, opacity crossfade, a 2px progress rule, a text Skip button (markdown links open a new tab here, so Skip is a real control). `?intro=skip` also dismisses it. No position shift, no bounce, no second call to action on the page itself. `prefers-reduced-motion` removes the sheet entirely (do not only crush the duration — the delay would leave a blank screen). `?demo=1` skips it and opens the map.
- Map controls: minimal Folium defaults; legend as hairlined floating panel
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

## Home
The app opens on **Home**, not the map. Home is one column: the problem, the index, a four-row term table, the map → dossier → brief path, and the cohort line computed from the loaded scores. One action: **Open the map**. No icon row, no stat cards, no chat, no model name helper. The optional LLM name stub stays off and off the page.

## Map & dossier microcopy

- **How to read this** — Map page only. 1–2 lines under the header strip: HPI color meaning + size cue. No emoji, no dual CTAs.
- **Weights transparency** — Methods expander table (R/C/H/P + weights + one plain sentence why). Match METHODS.md numbers.
- **Weight sensitivity** — Methods only, one collapsed expander under that table. Sliders reweight stored components for oral defense. Not a new nav page, not a new official index, and not shown on Map or Dossier.
- **Demo talk track** — Sidebar under Demo mode only. Numbered 60-sec script; plain scientific English.
- **IUCN badge** — Dossier chip: linked category when `iucn_status=ok`; otherwise muted `IUCN not linked`. Never show a fake LC/VU.
- **Field brief** — HTML + PDF; same structure (Where / Stress / Why / What to do). Typography follows tokens above.
- **Cohort spark** — Dossier only; “Cohort HPI · selected marked” with rank caption.
