# Harvester Risk Atlas

**Which wild medicinal plants of the Philippines need attention first, where they grow, why, and how sure we are.**

EthnoHACK 2026, Track 3: Biodiversity & Sustainability. Version 2 (Harvest Priority Index v2).

> For research and education. Not medical advice, not a harvest permit, and not a Red List assessment.
> IUCN and DENR categories are never invented: missing data stays missing.

| | |
|--|--|
| **Live app** | https://harvester-risk-atlas.vercel.app |
| **Method** | [`docs/METHODS.md`](docs/METHODS.md) |
| **Design system** | [`docs/DESIGN.md`](docs/DESIGN.md) |
| **What was built when** | [`docs/ORIGINALITY.md`](docs/ORIGINALITY.md) |

## A three-minute tour

1. **Overview** (`/`): the hotspot map and the five plants that need attention now. Hover the map, click an area.
2. **Atlas** (`/atlas`): pick a plant to see where it grows and why it ranks where it does, or click an area to see what grows there.
3. **A plant** (`/species/eurycoma-longifolia`): the three reasons in plain words, the evidence behind them, and how sure the rank is.
4. **Field brief** (`/species/eurycoma-longifolia/brief`): one A4 page to print.
5. **How it works** (`/how-it-works`): the method, a weight explorer (the sliders live in the URL), and the checks that test the ranking.

## What it does

The **Harvest Priority Index (HPI v2)** ranks 29 native plants (of a cohort of 51) from three equally weighted parts:
**rarity** (how seldom it is recorded where botanists have looked, and how small its native range is),
**harvest harm** (whether the roots, bark or whole plant are taken, and whether it is farmed) and
**habitat pressure** (how much of its range is unprotected and in provinces losing forest).
Climate exposure is shown but counts for nothing in the score.
2,000 Monte Carlo draws turn the score into a rank interval and a tier: *needs attention now*, *keep watch*, *lower concern*.
Plants appear only as H3 hexagons, never as points, so no exact location is revealed.
The first version ranked a plant with zero records first. How that was found and fixed is in the ledger and in the "How sure is the ranking?" section.

## Run it

The web app is static: data is pre-built into `web/public/data`.

```bash
cd web
npm ci
npm run dev        # http://localhost:5173
npm test           # unit tests, incl. parity with the Python index maths
npm run e2e        # Playwright + axe accessibility checks on every route
npm run build      # type check + production build into web/dist
```

Rebuild the data (Python 3.11+; Windows PowerShell or POSIX):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      POSIX: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python -m harvester_risk_atlas all --offline   # fetch -> base -> index -> validate -> export
```

`--offline` uses the committed raw snapshot; without it the pipeline fetches GBIF, WCVP and the other sources again
(a free IUCN token and a GBIF account are optional).

## Deploy

Vercel project with **Root Directory** `web`, framework Vite, build `npm run build`, output `dist`.
Every push to `main` redeploys. `web/vercel.json` provides the single-page-app fallback.

## Data and licences

| Source | Used for | Licence |
|---|---|---|
| GBIF occurrence records | records, counts, survey effort | per dataset (CC0 / CC BY / CC BY-NC) |
| World Checklist of Vascular Plants | native status | CC BY 4.0 |
| WDPCA Philippines (UNEP-WCMC, HDX) | protected-area cover | Protected Planet terms, non-commercial |
| Tree-cover loss (Hansen et al., Global Forest Watch) | forest loss by province | CC BY 4.0 |
| WorldClim 2.1 and CMIP6 | climate exposure (weight 0) | research and education use |
| DENR DAO 2026-20 | validation only | public government document |
| Stuart, *Philippine Medicinal Plants* | curated harvest traits | cited per plant; text not redistributed |
| iNaturalist observers | plant photos | credited on every photo |

Code: MIT (see `LICENSE`).

## Limits

- 22 of 51 plants are listed but not ranked (not native, or fewer than 5 occupied cells).
- GBIF records show where botanists looked as well as where plants grow; survey effort is shown and corrected for, not removed.
- Harvest traits are curated from published sources; rows awaiting expert review say so on the plant's page.
- There is no official count of how much of each plant is harvested, so the ranking is tested for robustness, not accuracy.

## AI disclosure

Code and documents were drafted with AI assistants (Grok and Cursor for version 1; Claude Code for the version 2 plan, pipeline, web app and docs)
and reviewed by the team, who are responsible for everything submitted. Scientific claims and curated values carry citations and are human-verified before release.

## Earlier version

The Streamlit prototype (v1.1, HPI v1) still lives in `app/` and `src/harvester_risk_atlas/` while the cut-over completes; see `DEPLOY.md`.
