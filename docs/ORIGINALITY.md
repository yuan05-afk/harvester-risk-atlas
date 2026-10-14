# Originality and provenance ledger

EthnoHack 2026 asks for work "created during the hackathon or substantially developed during the hackathon". It also asks teams to identify which components they built and which were pre-existing. This file is that record. It is kept current as work lands.

Hackathon window: **2–8 November 2026 (CET)**.

## Timeline

| Period | Version | Git boundary | What it contains |
|---|---|---|---|
| 29 Sep – 1 Oct 2026 | HPI v1.1 Streamlit prototype | tag `v1.1-baseline` | Pre-existing. GBIF sample (60 records/species), HPI v1.1 formula, Streamlit app (map, dossier, field brief, compare, methods), PDF brief, weight-sensitivity explorer. |
| 14 Oct – 1 Nov 2026 | v2 rebuild | branch `v2-rebuild` → tag `v2.0-pre-hackathon` | Pre-existing. A v1 audit, data pipeline v2, Harvest Priority Index v2 with uncertainty, static web app. See the v2 log below. |
| 2 – 8 Nov 2026 | Hackathon work | commits after `v2.0-pre-hackathon` | Built during the hackathon. See the hack-week log below. |

Anyone can check the boundaries with `git log v1.1-baseline..v2.0-pre-hackathon` and `git log v2.0-pre-hackathon..`.

## Why v1 was rebuilt

An audit on 14 Oct 2026 found that most of v1's variation came from sampling artifacts:
- The 60-record GBIF cap made rarity almost constant.
- The "decline" cue tracked the share of citizen-science records (Spearman ρ = 0.76).
- A species with zero records ranked first.
- The RandomForest "suitability sketch" scored 1.00 cross-validation accuracy for every species because of leakage.

v1 data are archived unchanged in `data/archive/v1.1/`, with checksums. The full audit is in `docs/METHODS.md`.

## v2 log (pre-hackathon)

| Date | Change |
|---|---|
| 2026-10-14 | v1 audit; baseline tag; v1 data archived; this ledger started. |
| 2026-10-14 | Data pipeline v2: GBIF exact counts and full PH records, cleaning, WCVP nativity, H3 grid, survey-effort layer, cell-based PA cover, GFW forest loss, CMIP6 clips, DENR DAO 2026-20 parser. |
| 2026-10-14 | HPI v2 (Harvest Priority Index): anchored components R/H/E/C, gates, Monte Carlo rank intervals, priority tiers, validation suite; cohort expanded to 51 with 16 cited native candidates; METHODS v2; static-data export for the web app. |
| 2026-10-14 | Web app (Vite + React + TypeScript + MapLibre), Field Atlas design system, land-clipped H3 map layers, iNaturalist plant photos (CC0 / CC BY, CC BY-NC fallback). |
| 2026-10-14 | Usability redesign after team review: plain-language tiers and components, rubber-stamp priority badge, photo plant cards, Atlas browse / plant / area panels with map hover previews, plain-sentence "why it ranks here", How it works page, one-page A4 field brief, new intro animation. |
| 2026-10-14 | Visual identity rework: natural-dye palette (tayum, atsuete, bakawan, sibukaw, dilaw) validated for colour-vision deficiency, Fraunces display type, hand-drawn explanatory figures replacing stock icons, robustness ledger with data figures, error boundary, lazy search palette. |
| 2026-10-14 | Tests: golden `parity.json` from the pipeline checked against the web score maths, unit tests for plain-language text and map tooltip, Playwright end-to-end plus axe accessibility checks on every route; fixed bad plant links showing a data error instead of "not in the atlas" on hosts with an SPA fallback. Weight explorer settings now live in the URL (?w=R,H,E,C) so a ranking can be shared. |
| 2026-10-14 | QA and cut-over: zod validation moved to development and a schema test (first load 176 to ~132 KB gzip), no layout shift, Lighthouse desktop 86-100 performance and 100 accessibility, responsive and keyboard e2e, CI (pytest, typecheck, vitest, build, Playwright + axe), README rewrite, Vercel project linked to the GitHub repo (root `web`), `main` branch protection; v2 merged to `main` and deployed to https://harvester-risk-atlas.vercel.app. |
| 2026-10-14 | Streamlit v1 retired (its address shows a "moved" page; v1 code stays in git history); build-time pre-render and hydration of the Overview; intro animation moved to CSS and made phone-safe; real-throttle mobile Lighthouse 60 → 84. Tagged `v2.0-pre-hackathon`: the pre-hackathon boundary. |

## Hack-week log (2–8 Nov 2026)

| 2026-10-14 | Device fit and look pass (done before the week, logged here because it follows the tag). Page ground moved from cream to a neutral cool grey with white sheets, paper grain removed, harvest orange darkened to keep 4.5:1 text contrast; the turmeric marker under the active tab is gone (ink and a 2 px rule on the top bar, heavier glyph on the bottom tabs). Responsive fixes: the "How sure is this order?" chart and the evidence table no longer push the page sideways on phones, previous/next plant cards stack, tablet portrait gets a two-column plant hero and a compact home hero, phones in landscape get a side-by-side Atlas and compact tab bar, 44 px touch targets on touch screens, small-phone and large-monitor tweaks. e2e now opens every disclosure and checks 11 widths from 320 to 1920. |
| 2026-10-14 | Every plant now has a picture. Abutra and Dudoa had no open field photo, so each uses a botanist-identified herbarium specimen scan from GBIF (Naturalis Biodiversity Center, Smithsonian NMNH; both CC0), cropped to the leafy part and captioned "Herbarium specimen, cropped". `photos.csv` gained `kind`, `source` and `crop` columns; `sources/photos.py` gained `crop_box`, crop support in `download` and a `fetch_chosen` command; a test fails if any plant loses its photo. |

_Hack-week work proper starts 2 Nov._

## Third-party code, data and tools

| Kind | Item | Licence / terms |
|---|---|---|
| Data | GBIF occurrence records | Per-dataset licences (CC0 / CC BY / CC BY-NC); GBIF citation guidelines |
| Data | WorldClim 2.1 (Fick & Hijmans 2017) | Free for research and education |
| Data | WDPCA Philippines, UNEP-WCMC via HDX | Protected Planet / WDPA terms, non-commercial |
| Data | Natural Earth land | Public domain |
| Data | IUCN Red List API v4 (optional) | IUCN terms of use; categories never invented |
| Libraries | See `requirements.txt` / `pyproject.toml` and `web/package.json` | Each under its own licence |
| Data | iNaturalist research-grade photos via GBIF | CC0, CC BY 4.0 or CC BY-NC 4.0; creator credited on each plant |
| Fonts | Atkinson Hyperlegible Next (Braille Institute), Fraunces (Undercase Type) via Fontsource | SIL Open Font License 1.1 |

## AI assistance

| Tool | Period | Use |
|---|---|---|
| Grok, Cursor agent | Sep – Oct 2026 | Drafted v1 code and docs, reviewed by the team |
| Claude Code (Anthropic) | Oct 2026 onward | v1 audit, v2 plan, and drafting v2 code, data pipeline and docs, reviewed by the team |

The team is responsible for the accuracy, licensing and appropriateness of everything submitted. Scientific claims and curated values carry citations, and curated values are human-verified before release.
