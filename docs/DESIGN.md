# Design system: Field Atlas

Harvester Risk Atlas tells people which wild medicinal plants of the Philippines need attention first, where, why, and how sure we are. It should feel like a **field guide that was printed for the Philippines**: plates of pen drawings with numbered figures, herbarium sheets with a determination stamp, ruled ledgers of results, inks made from Philippine dye plants on a quiet neutral ground. It must never look like a template.

Five principles decide every screen.

1. **Plain words first.** Readers are rangers, harvesters, LGU staff and students, not data scientists. Tiers are named ("Needs attention now", "Keep watch", "Lower concern", "Not ranked"). Components are named by what they mean ("Rarity", "Harvest harm", "Habitat pressure"). Numbers come second, behind a disclosure.
2. **The hexagon is the unit of truth.** Places are H3 cells clipped to land: res 4 (about 1,770 km²) when zoomed out, res 5 (about 250 km²) when zoomed in. There are no points, so plants at risk stay hard to find.
3. **No rank without its range.** A rank is always said with how far it could move ("Ranked 2nd of 29. It could be anywhere from 1st to 3rd").
4. **Draw, don't decorate.** Every illustration explains something: the rarity plate shows searched cells against found cells, and the harvest plate inks the roots that harvest takes. No stock icons sit in tinted squares.
5. **Calm chrome, loud data.** Chrome is near-black ink on a quiet cool-grey ground with hairline rules. Colour is kept for data; the turmeric highlighter marks emphasis inside content, never navigation.

## Banned patterns (generic "AI" UI)
- **Coloured left-stripe boxes or callouts.** Banned everywhere.
- **Icon in a pastel rounded square above a title** (the "feature card").
- **Pill badges for status** ("Holds up" in a green pill). Use a drawn verdict mark and small caps instead.
- **Grids of identical white rounded cards for prose.** Use ruled plates, ledgers or footnotes.
- **Lucide or other stock icons for meaning.** They are allowed only for UI affordances: search, close, back, arrows, print, download.
- **Fully rounded buttons and fields; 14 px+ card radii.**
- **Tableau-like blue, orange and green; red-to-green risk ramps.**
- **Cream or beige "warm paper" backgrounds, and paper-grain textures.** Replaced 2026-10-14 at the owner's request: cream reads as a default AI-tool look. The ground is now a single neutral cool grey with white sheets; the colour belongs to the data.
- **A coloured marker or stripe under the active nav item.** The active page is ink and a 2 px straight rule (top bar) or a heavier glyph (bottom tabs).

## Colour

Palette: a neutral cool-grey ground and near-black ink, with inks from Philippine dye plants.

### Surfaces and ink
| Token | Hex | Use |
|---|---|---|
| `--paper` | `#EFF1F3` | Page ground |
| `--sheet` | `#FCFCFD` | Cards, panels, the brief |
| `--ink` | `#15181C` | Text (17.4:1 on sheet) |
| `--ink-2` | `#40454C` | Secondary text (8.5:1 on paper) |
| `--ink-3` | `#596069` | Tertiary text and ticks (5.6:1 on paper) |
| `--rule` / `--rule-strong` | `#D8DCE1` / `#AEB5BE` | Hairlines and ledger rules |
| `--highlight` | `#E2B33C` | **Dilaw** (turmeric): "Biggest reason" and step 4. Not used in navigation. Always behind ink, never as text. |
| `--sea` / `--land` | `#DCE4EA` / `#FCFCFD` | Map |

### Data inks (validated)
The script `scripts/check_palette.py` uses Machado 2009 simulation and CIEDE2000. Run it again whenever a value changes.

| Component | Ink | Hex | Text contrast on sheet |
|---|---|---|---|
| Rarity | **tayum** indigo | `#33408F` | 8.7:1 |
| Harvest harm | **atsuete** (annatto) | `#AD4E1A` | 5.3:1 (4.8:1 on paper) |
| Habitat pressure | **bakawan** (mangrove bark) | `#2E5F3E` | 7.0:1 |
| Climate (weight 0) | `--ink-3` | `#596069` | 6.2:1 |

Worst all-pairs ΔE00, including tier High: normal 26, protan 11, deutan 10, tritan 11. The rejected rust and moss pair scored ΔE 5 under deutan.

**Priority tiers.** Ordinal, one hue, **sibukaw** (sappanwood):

| Tier | Hex |
|---|---|
| High attention | `#7C1A4B` |
| Watch | `#BB4E7F` |
| Lower | `#D496AD` |
| Not ranked | hatch on `#E2E5E9` |

**Hotspots.** 1 / 2 / 3 / 4+ species per cell: `#E39CB7` `#C86890` `#A4386A` `#731946`. Survey effort uses a neutral grey ramp.

Tiers always carry their name; colour is never the only cue.

## Type
| Family | Role |
|---|---|
| **Fraunces** (variable, opsz cut, OFL) | h1 and h2, the display headline, plate, ledger and reason titles, the brand, plant names in cards, step numerals, binomials in italic. `SOFT 30`. |
| **Atkinson Hyperlegible Next** (OFL) | Body, UI, tables, numbers. Chosen for legibility in daylight on phones. |

Figure numbers ("FIG. 1 · RARITY"), verdicts ("HOLDS UP") and "Biggest reason" are the only small-caps or uppercase text, as in a printed flora. Numbers use tabular lining figures.

## Shape and layout
- Radius: 3 px for controls, 4 px for cards and sheets, 6 px for map frames. Pills only for genuine toggles.
- Section heads sit on a 2 px ink rule; items are divided by 1 px hairlines (plates, steps, ledger).
- Maximum width 1,240 px. Spacing base 4 px.
- Atlas: full-bleed map with a 380 px right panel; on phones, a bottom sheet.

## Signature components
| Component | Notes |
|---|---|
| **Stamp** (`Stamp.tsx`) | A worn rubber stamp in the tier ink. The tier is written round the ring and the rank sits in the centre. It is pressed onto a paper disc so it reads over photos, and lands with a spring "thunk". It replaces tier chips and side stripes. |
| **Plates** (`Figures.tsx` `ComponentFigure`) | Annotated pen drawings for R, H, E and C. They draw themselves in once on scroll. |
| **Glyphs** (`ComponentGlyph`, `NavGlyph`) | The same hand at 24–34 px: reason tiles and the mobile tab bar (a compass, hexes, a leaf, a balance). |
| **Ledger** (`HowItWorks` `Checks`, `charts/CheckFigures.tsx`) | One row per robustness test: a drawn verdict mark, a serif title, plain text, and a small figure of the actual number (agreement scale, rank strip, interval). |
| **Plant card / row** | A photo mounted like a print, with the stamp on its corner, the common name in serif and the binomial in italic. Rows in a list already grouped by tier show only "No. n". |
| **Reason tile** | Glyph, level meter (four blocks), one plain sentence. The main driver gets a 3 px top rule in its ink and a turmeric "Biggest reason" marker. |
| **Footnotes** | "Read this first" caveats are marked * † ‡ § in sappan. |
| **Field brief** | One A4 page: all 51 briefs were verified at ≤ 297 mm in print emulation. |

## Motion
- **Intro (preloader).** On the first visit to `/`: the PH outline draws, hexes bloom north to south, then the sheet clips away (3.6 s). It has a Skip button and Esc, is skipped under reduced motion, and can be replayed from the footer.
- **Pages.** 220 ms fade/rise between pages. Plates and verdict marks draw in once. The stamp lands with a spring. Cards lift 4 px on hover.
- **Map.** Fly-to only on explicit selection.
- **Reduced motion.** `prefers-reduced-motion` removes all of the above (`MotionConfig reducedMotion="user"`, plus `useReducedMotion` in figures).

## Voice
- **Plain and specific.** No developer or curation text reaches readers.
- **Device-neutral.** "Point at", "Tap or click".
- **Errors and empty states.** Errors say what happened and what to do; empty states invite an action.

## Disclaimers
A persistent footer line: "For research and education. Not medical advice, not a harvest permit, and not a Red List assessment." Context notes appear where a claim is made.
