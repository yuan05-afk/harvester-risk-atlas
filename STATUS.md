# STATUS — Harvester Risk Atlas

Last updated: 2026-09-29 ~20:20 (Asia/Manila)

## What works now

| Item | Status |
|------|--------|
| Repo scaffold (`src/`, `app/`, `scripts/`, `data/`, `docs/`, `notebooks/`) | Done |
| Seed list of **35** PH/SEA medicinal taxa + vernaculars | Done (`data/raw/seed_species.csv`) |
| Live GBIF fetch (`scripts/fetch_gbif.py`) | Done — demo extract shipped |
| Offline demo parquet/csv (`occurrences_sample`, `species_features`, `hpi_scores`) | Shipped under `data/processed/` |
| HPI v1.1 with transparent weights + confidence | Done — see `docs/METHODS.md` |
| **WorldClim 2.1** bio1/bio12/bio15 SEA clip → climate stress | Done |
| **WDPCA PH** real PA polygons → overlap + distance gap | Done |
| **IUCN API v4** client + batch script | Done — `not_queried` without token; never invents |
| Vernacular↔scientific search | Done |
| Streamlit dossier + HTML/PDF field brief | Done |
| EDA notebook | Done |
| venv + editable install | Done |

### Workflow / DS / viz upgrades (2026-09-29 evening)

| Item | Status |
|------|--------|
| Guided workflow step indicator (Map → Dossier → Field brief) + Continue | Done |
| HPI component bar + weighted waterfall; cohort HPI histogram (Map + Methods) | Done |
| Data gaps panel (imputed flags, sparse/missing GBIF, IUCN `not_queried`, climate/PA sources) | Done |
| Compare view (2 species, side-by-side components + metrics) | Done |
| Risk archetypes — sklearn KMeans on HPI components; map color option + dossier chip | Done (`src/.../archetypes.py`) |
| Occurrence decade histogram from GBIF `year` (skips if no dates) | Done |
| Folium MarkerCluster on centroids; Esri World Gray Canvas retained | Done |
| Demo mode toggle → *Arcangelisia flava* (abutra) + narrative captions | Done |
| Chart HTML download (PNG if kaleido installed) | Done |
| Exploratory suitability sketch (RF presence/background; not an SDM) | Done (dossier expander) |

**No feature rebuild required** — archetypes/charts run on existing `hpi_scores` columns. IUCN left `not_queried`.

### GBIF note
- `Mentha × piperita` (yerba buena stand-in) may have 0 PH/SEA points; imputed components + lower confidence. Consider `Mentha cordifolia` synonyms for hack week.

## Needs user tokens / optional downloads

| Resource | Needed? | Behavior without key / file |
|----------|---------|------------------------------|
| **IUCN Red List API v4** (`IUCN_API_TOKEN`) | Official categories on dossier | `iucn_status=not_queried`, category blank. Signup: https://api.iucnredlist.org/users/sign_up |
| **OpenAI** (`OPENAI_API_KEY` + `ENABLE_LLM_NAMES=1`) | Optional name helper | Table fuzzy match only |
| **kaleido** (optional pip) | PNG chart export for slides | HTML chart download still works |
| WorldClim full zip | Only if regenerating climate | SEA clips already shipped |
| WDPCA raw gpkg | Only if regenerating PA | Processed gpkg shipped |

## Design system
- Tokens & bans documented in `docs/DESIGN.md`
- UI: Inter/system + JetBrains/IBM Plex Mono for metrics; forest accent `#2d6a4f`; risk colors only on map/HPI
- Map basemap: **Esri World Gray Canvas** (free, no key)

## Changelog (2026-09-29)

### Demo polish + PDF brief (2026-09-29 ~20:20 Asia/Manila) — local only

| Item | Status |
|------|--------|
| Map-only "How to read this" strip (HPI color meaning) | Done |
| Methods expander — R/C/H/P weights + one-sentence why | Done |
| Demo mode 60-sec talk track (plain script) | Done |
| Field brief PDF download (reportlab; HTML retained) | Done |
| IUCN badge: category when `ok`; muted "IUCN not linked" when `not_queried` | Done — never invents |
| `requirements.txt` pinned for Streamlit Cloud + `DEPLOY.md` | Done |

Files: `app/streamlit_app.py`, `app/styles.css`, `src/harvester_risk_atlas/pdf_brief.py`, `requirements.txt`, `DEPLOY.md`, `STATUS.md`, `docs/DESIGN.md`.

**QA:** PDF smoke (`%PDF-`, ~3 KB for abutra); HTML shows "IUCN not linked"; package imports OK; no invented IUCN categories (`iucn_status` still `{not_queried}`).


### UI polish pass (2026-09-29 ~19:45 Asia/Manila) — local only, no GitHub push

| Item | Status |
|------|--------|
| Strict type hierarchy in `app/styles.css` + `docs/DESIGN.md` (title/section/body/caption/mono metrics) | Done |
| Streamlit chrome hide (header/toolbar/decoration/deploy) + block padding + column gaps | Done |
| Chart wells / Folium iframe hairlines; step-indicator spacing | Done |
| Plotly clean theme in `charts.py` — white paper, muted grid, taller figs, legends below | Done |
| Forest accent ramp on component charts; risk colors **only** on HPI histogram/bands/map | Done |
| Map markers: white stroke + fill; panel + on-map legend; taller map | Done |
| IUCN left `not_queried` | Unchanged |

**QA (local):** package + chart imports OK; 4 chart smoke builds (height ≥240, paper `#ffffff`); `streamlit_app.py` parses; `build_map` renders on-map legend; HPI CSV IUCN statuses = `{not_queried}`. No Streamlit runtime visual re-check of overlap (CSS/layout targeted). Optional: kaleido still absent → PNG download caption only.


### Compare-page QA fixes (2026-09-29 ~19:52 Asia/Manila) — local only

| Bug | Fix |
|-----|-----|
| Plotly grouped bar title overlapped species legend | `compare_components`: legend forced below (`orientation=h`, `y=-0.28`), taller fig + larger bottom/top margins so title never collides |
| Right compare card showed raw HTML (`<div class="hra-card">…`) | Indented multiline f-string → Markdown code fence; now zero-indent joined HTML + `st.html` (fallback `st.markdown`) |
| Left card scientific name awkward wrap (ARCANGELISI / A FLAVA) | `.hra-sci-name` / `.hra-compare-card`: italic sentence case, smaller letter-spacing, `overflow-wrap: break-word`, no mid-token uppercase crush |

Files: `src/harvester_risk_atlas/charts.py`, `app/streamlit_app.py`, `app/styles.css`, `STATUS.md`.


### Plotly legend-below pass (2026-09-29 ~20:00 Asia/Manila) — local only

| Item | Fix |
|------|-----|
| Title/legend collision on Compare (+ other charts) | Canonical `LEGEND_BELOW`: `orientation=h`, `yanchor=top`, `y=-0.22` (compare uses `y=-0.28`), `x=0`, `xanchor=left`; never `y>1` |
| Bottom clearance | Charts with legends use `margin.b>=110`; compare `b=120`, `l=96` so category labels fully visible |
| Streamlit theme overwrite | All `st.plotly_chart(..., theme=None)` so Streamlit theme cannot re-park legend |
| Title | `_title`: `y=0.98`, `pad.b=12`; taller figs (compare height=400) |

Files: `src/harvester_risk_atlas/charts.py`, `app/streamlit_app.py`, `STATUS.md`.


- Added `src/harvester_risk_atlas/archetypes.py`, `charts.py`, `suitability.py`
- Reworked `app/streamlit_app.py`: workflow steps, Compare page, Field brief page, demo mode, MarkerCluster, HPI viz, data gaps, decade hist
- Extended `app/styles.css` (steps, chips, gaps, demo captions)
- Documented archetypes + suitability caveats in `docs/METHODS.md`

## Next steps for Nov 2026 hack week (2–8 Nov)

1. Obtain IUCN token → `python scripts/fetch_iucn.py` → rebuild features/HPI; show live categories on dossier.
2. Optional: CHELSA future climate → suitability shift vs current WorldClim.
3. Optional: DENR open PA layers if license-cleared; keep WDPCA citation.
4. Tighten seed list with POWO synonyms; fix mint complex.
5. Deploy Streamlit Cloud (see `DEPLOY.md`); keep disclaimer + AI/OSS disclosure.
6. Judging packet: METHODS one-pager, demo video Map → Dossier → brief (use Demo mode).
7. HPI weight sensitivity in notebook for oral defense.
8. Optional: `pip install kaleido` for PNG slide exports.

## Blockers
- None for offline `streamlit run` demo (climate + PA fidelity upgraded without tokens).
- Live IUCN categories blocked only on free API token registration.
