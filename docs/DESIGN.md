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
| `--surface` | `#ffffff` | Cards, panels |
| `--hairline` | `#d2d2d7` | Borders, dividers |
| `--accent` | `#2d6a4f` | Single muted forest accent (links, focus, primary actions) |
| `--accent-soft` | `#e8f0eb` | Soft accent wash (selected chips, table highlight) |
| `--risk-low` | `#40916c` | HPI lower band / map |
| `--risk-mid` | `#b08968` | HPI moderate (muted amber-earth, not neon) |
| `--risk-high` | `#9b2226` | HPI higher band |
| `--mono-bg` | `#f0f0f2` | Code / metric wells |

Semantic risk colors appear **only** on map markers, HPI bars, and band badges — never as page chrome or gradients.

### Type (max 2 families)
1. **UI:** `-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
2. **Metrics / code only:** `"JetBrains Mono", "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace`

No third display font. No Poppins, Geist-as-brand, or decorative serifs.

- Page title: 28–32px / 600 / tight tracking
- Section: 17–20px / 600
- Body: 14–15px / 400 / ~1.5 line-height
- Caption: 12–13px / `--ink-secondary`
- Metrics: mono, tabular-nums, 20–28px for HPI

### Spacing & shape
- Page padding: 24–40px
- Card gap: 16–24px
- Section rhythm: 32–48px
- Radius: **8px** default, **12px** max (panels)
- Borders: 1px `--hairline`; prefer hairlines over shadows
- Shadow (rare): `0 1px 2px rgba(0,0,0,0.04)` only

### Interaction
- Focus ring: 2px `--accent` at 40% opacity
- Buttons: flat fill `--accent` or ghost hairline; no glow
- Map controls: minimal Folium defaults; legend as small hairlined panel

## Banned (anti-slop)
- Purple / aurora / neon gradients, glassmorphism blobs
- Emoji as icons or section markers
- Hero pill + dual CTAs, three equal icon feature cards
- Glow borders, fade-up-everywhere motion
- Marketing fluff (“unlock”, “seamlessly”, “revolutionize”)
- Rainbow chrome outside HPI semantics

## Copy voice
Plain scientific English. Short dossier labels: **Where / Stress / Why it matters / What to do**. Disclaimer always visible, never cute.
