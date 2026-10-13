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

## Hack-week log (2–8 Nov 2026)

_Empty until 2 Nov._

## Third-party code, data and tools

| Kind | Item | Licence / terms |
|---|---|---|
| Data | GBIF occurrence records | Per-dataset licences (CC0 / CC BY / CC BY-NC); GBIF citation guidelines |
| Data | WorldClim 2.1 (Fick & Hijmans 2017) | Free for research and education |
| Data | WDPCA Philippines, UNEP-WCMC via HDX | Protected Planet / WDPA terms, non-commercial |
| Data | Natural Earth land | Public domain |
| Data | IUCN Red List API v4 (optional) | IUCN terms of use; categories never invented |
| Libraries | See `requirements.txt` / `pyproject.toml` (and `web/package.json` once added) | Each under its own licence |

## AI assistance

| Tool | Period | Use |
|---|---|---|
| Grok, Cursor agent | Sep – Oct 2026 | Drafted v1 code and docs, reviewed by the team |
| Claude Code (Anthropic) | Oct 2026 onward | v1 audit, v2 plan, and drafting v2 code, data pipeline and docs, reviewed by the team |

The team is responsible for the accuracy, licensing and appropriateness of everything submitted. Scientific claims and curated values carry citations, and curated values are human-verified before release.
