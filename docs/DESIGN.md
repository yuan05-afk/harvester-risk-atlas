# Design system: Field Atlas

Harvester Risk Atlas v2 tells people which wild medicinal plants of the Philippines need attention first, where, why, and how sure we are. The interface borrows from two working documents of field botany: the **herbarium sheet** (a specimen on white, with a typed label that carries every fact and its source) and the **atlas grid** (one unit of area, repeated across the archipelago).

Four principles decide every screen.

1. **The hexagon is the unit of truth.** Every geographic statement is drawn as H3 cells (about 250 km²), never as points or averages. The method uses the same cell, so what you see is what was scored. It also generalises locations of plants at risk from collection.
2. **No rank without its interval.** A rank always appears with its 90% interval, and a tier is shown before a score. Three-decimal scores never appear on their own.
3. **Every fact carries its source.** Labels name the dataset and date, as a specimen label does. Missing evidence is shown as missing, never as a filler value.
4. **Calm chrome, loud data.** Interface chrome is ink on paper. Colour is reserved for data: priority tiers and the three score components. One highlighter yellow marks what the reader has selected.

## Colour

### Surfaces and ink

| Token | Hex | Use |
|---|---|---|
| `--paper` | `#F4F6F2` | Page. A cool, faintly green herbarium grey, not cream. |
| `--sheet` | `#FFFFFF` | Charts, maps, species labels. Every chart sits on a sheet. |
| `--ink` | `#18231D` | Primary text (14.9:1 on paper) |
| `--ink-2` | `#46524B` | Secondary text (7.5:1) |
| `--ink-3` | `#5D6962` | Tertiary text, axis labels (5.3:1) |
| `--rule` | `#D5DBD4` | Hairlines between sections and table rows |
| `--highlight` | `#EAC33F` | Selection and the brand mark. Berberine yellow, the colour of abutra's "yellow root". Always behind ink (10.2:1), never as text. |

### Data colours (validated)

All values were checked with the dataviz validator (`validate_palette.js`): OKLab ΔE under Machado protan and deutan simulation, the normal-vision floor, and contrast on `--sheet`.

**Score components.** These are categorical, in this fixed order everywhere: map, bars, strip plots, briefs and Methods.

| Component | Hex | Why this hue |
|---|---|---|
| R. Range restriction | `#3664BE` | blue: space, extent |
| H. Harvest sensitivity | `#C97F14` | turmeric ochre: roots, bark, the harvested part |
| E. Habitat exposure | `#006E3B` | forest green: habitat |
| C. Climate exposure (weight 0) | `--ink-3` | grey, because it is reported but not weighted |

The set passes all checks **all-pairs**, so it is safe for small multiples:
- worst CVD ΔE 13.0 (protan)
- worst normal-vision ΔE 22.4
- contrast on sheet ≥ 3.2:1

Ochre falls to 2.96:1 on paper, which is why charts sit on sheets.

**Priority tiers.** An ordinal ramp in one hue: plum, OKLCH hue 355.

| Tier | Hex |
|---|---|
| High attention | `#7C1A4B` |
| Watch | `#BB4E7F` |
| Lower | `#D496AD` |
| Not scored | 45° hatch in `--ink-3` on `#E6E9E5` |

The ramp passes the ordinal checks: monotone lightness, ΔL ≥ 0.06 per step, light end 2.4:1, a single hue. Tiers always carry their name as text. The colour is never the only cue.

**Sequential maps.** The hotspot map counts High and Watch species per cell in four plum steps:

| Species in cell | Hex |
|---|---|
| 1 | `#E39CB7` |
| 2 | `#C86890` |
| 3 | `#A4386A` |
| 4 or more | `#731946` |

The ramp passes the ordinal checks, with its light end at 2.2:1. Survey effort uses a neutral grey ramp (`#EDEFED` → `#59605A`), so effort is never confused with priority.

Avoided on purpose: green-to-red "risk" ramps (they fail colour-vision deficiency, and they imply "green is fine"), and rainbow scales.

## Type

One family: **Atkinson Hyperlegible Next** (Braille Institute, OFL), variable weight 200–800, self-hosted with `@fontsource-variable`.
- It was drawn for legibility: distinct letterforms for I/l/1 and O/0, and open apertures. That suits field staff reading on phones in daylight, and readers with low vision.
- Its true italic carries binomials (*Cinnamomum mercadoi*).

| Role | Size / line-height | Weight | Notes |
|---|---|---|---|
| Display | 49 / 1.05 | 750 | Overview headline only; tracking −0.02em |
| H1 | 39 / 1.1 | 700 | Page and species titles |
| H2 | 25 / 1.2 | 650 | Section titles |
| H3 | 20 / 1.3 | 650 | Figure titles |
| Body | 16 / 1.55 | 400 | Measure ≤ 68ch |
| Small | 14 / 1.45 | 450 | Captions, table cells, sources |
| Micro | 13 / 1.35 | 500 | Axis ticks, chip text. Sentence case, never all caps. |

Numbers in tables and labels use tabular figures. Scale ratio is 1.25 on 16 px.

## Layout

- Content grid: 12 columns, maximum 1,240 px, 24 px gutters, 16 px side margins on phones.
- Atlas: a full-bleed map. On desktop a 380 px panel sits on the right; on phones it becomes a bottom sheet with three detents.
- Spacing base: 4 px. Steps 4, 8, 12, 16, 24, 32, 48, 72.
- Radius: 4 px for chips and controls, 8 px for sheets. Nothing pill-shaped except toggles.
- Elevation: none by default. Sheets sit on paper by tone alone. Only the floating map panel and popovers take a single soft shadow.

### Page skeletons

```
Overview
┌───────────────────────────────────────────────────────────────┐
│ [mark] Harvester Risk Atlas    Overview Atlas Rankings Methods [Search] │
├──────────────────────────────┬────────────────────────────────┤
│ Which wild medicinal plants  │  hex archipelago: cells shaded   │
│ need attention first?        │  by priority species recorded;   │
│ two-line lede                │  top five pinned as labels       │
│ [Open the atlas] [Rankings]  │                                  │
├──────────────────────────────┴────────────────────────────────┤
│ Top of the list: five specimen labels with rank intervals     │
│ How a species is scored: R  H  E  (one sheet, three columns)  │
│ What the atlas cannot tell you                                │
└───────────────────────────────────────────────────────────────┘

Species profile
┌──────────────────┬────────────────────────────────────────────┐
│ Specimen label   │ Why it ranks here: contribution bar and    │
│ (sticky)         │   strip plots against the cohort           │
│ name, family     │ Where it was recorded: hex mini-map with PAs │
│ native status    │ Record history: decades by record type     │
│ tier, rank + CI  │ Climate outlook (reported, not scored)     │
│ [Field brief]    │ Evidence: every input with source and date │
└──────────────────┴────────────────────────────────────────────┘
```

## Components

| Component | Notes |
|---|---|
| Specimen label | Bordered sheet with labelled fields (family, native status, records, tier, rank). It mirrors a herbarium label, and every field is real data. |
| Tier chip | Tier colour swatch plus the tier name. "Not scored" uses the hatch and names its reason. |
| Rank interval | Dot (median) plus line (90% interval) on a shared rank axis. The same glyph appears in tables, labels and the caterpillar chart. |
| Contribution bar | Stacked R, H and E segments with 2 px sheet gaps and direct labels. |
| Figure frame | Title, one-line takeaway, the chart, then a source line and a "Show as table" toggle. |
| Highlighter | `--highlight` fill behind the selected row, cell or label. |

## Interaction and motion
- Every chart has a hover or focus tooltip and a table view. Every map action has a list equivalent.
- Motion answers actions only: panel open, sheet drag, map fly-to on explicit selection (300 ms). One moment on load: the Overview mark draws once, in at most 1.2 s.
- `prefers-reduced-motion` removes fly-to and drawing.
- Focus: a 2 px `--ink` outline, offset 2 px, on every interactive element.
- The URL holds state: species, layer, filters and weights are all deep-linkable.

## Voice
Plain, specific, sentence case. Name things by what readers know: "native to the Philippines", not "WCVP status = native".
- Errors say what happened and what to do next.
- Empty states invite an action.
- No developer instructions reach readers.

Not used:
- all-caps eyebrows
- middle-dot meta strings
- arrows appended to buttons
- monospace data labels
- emoji
- "unlock" or "seamless"

## Disclaimers
One persistent footer line on every page: "Research and education only. Not medical advice, not a harvest permit, not a Red List assessment." Context-specific notes appear where a claim is made.
