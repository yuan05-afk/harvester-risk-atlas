# STATUS — Harvester Risk Atlas

Last updated: 2026-09-30 (Home + first-visit preface)

## Home and preface (2026-09-30)

| Item | Status |
|------|--------|
| App opens on **Home** — problem, HPI v1.1, term table, map → dossier → brief, cohort line from loaded scores | Done |
| One action on Home: **Open the map**. No icon cards, no stat tiles, no chat, no name-model UI | Done |
| First-visit preface: four opacity beats + formula + 2px rule + Skip. Once per session | Done |
| `prefers-reduced-motion` removes the preface. `?demo=1` skips it and opens the map | Done |
| Species search stays off Home so the introduction is not the tool chrome | Done |

Files: `app/landing.py`, `app/streamlit_app.py`, `app/styles.css`, `tests/test_landing.py`, `docs/DESIGN.md`.

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
| Centroids drawn without MarkerCluster so HPI colors show at default zoom; Esri World Gray Canvas retained | Done |
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
- Motion: 120–180ms ease on signal controls only; no fade-up spam / bounce / aurora
- Map basemap: **Esri World Gray Canvas** (free, no key); floating hairline legend panel

## Changelog

- 2026-09-30: Cluster off on the risk atlas — centroids are CircleMarkers (HPI fill, white stroke); duplicate Folium in-map legend removed.

### HPI weight sensitivity on Methods (2026-09-30)

| Item | Status |
|------|--------|
| Methods expander: R/C/H/P sliders, clipped ≥ 0 and rescaled to sum to 1 | Done |
| Selected species rank before/after (rank 1 = highest HPI) | Done |
| Top rank-shift table + forest-accent bars (no risk colors) | Done |
| Restore control returns sliders to v1.1 (0.30 / 0.25 / 0.25 / 0.20) | Done |
| Caption: oral-defense sensitivity, not a new official index | Done |
| No new sidebar page; Map and Dossier unchanged | Confirmed |
| IUCN left `not_queried`; no IUCN fetch | Unchanged |
| Unit tests for normalize / ranks / chart colors | Done |

Files: `src/harvester_risk_atlas/hpi.py`, `src/harvester_risk_atlas/charts.py`, `app/streamlit_app.py`, `tests/test_hpi_sensitivity.py`, `docs/METHODS.md`, `docs/DESIGN.md`, `STATUS.md`.

### Changelog (2026-09-29)


### Cloud ImportError fix (2026-09-29 ~21:12 Asia/Manila) — local fix, needs push

| Item | Status |
|------|--------|
| Root cause | Streamlit kept stale `harvester_risk_atlas.*` in `sys.modules` after polish added `hpi_spark_svg` / earlier `render_field_brief_pdf` → in-app `ImportError: cannot import name …` |
| Fix | Bust package modules before import in `app/streamlit_app.py`; add `-e .` to `requirements.txt` for Cloud src install |
| Smoke | Stale-module repro fixed; AppTest Map + Dossier no exceptions; Cloud-style editable import OK |

Files: `app/streamlit_app.py`, `requirements.txt`, `DEPLOY.md`.

**Push recommendation:** yes — CloudAgent should push to `main`, then reboot the Streamlit Cloud app once.





### Demo visual polish — motion + denser UI (2026-09-29 ~20:55 Asia/Manila) — local only

| Item | Status |
|------|--------|
| Motion = signal only (150ms ease): step chips, cards, sidebar radio, button/input hover + focus | Done |
| Optional one-shot Folium focus pulse (CSS, `prefers-reduced-motion` respected) | Done |
| Denser dossier metrics + clearer section rhythm; hairline panels + rare hair shadow | Done |
| Focus rings (`--focus-ring`); floating hairline map legend panel | Done |
| Cohort HPI SVG spark under dossier metrics (selected tick + rank) | Done |
| Plotly soft bar cornerradius; legends stay below | Done |
| Microcopy tightened (header, howto, demo captions, talk track) | Done |
| How-to-read, weights, demo talk, PDF brief, IUCN not linked | Kept |
| IUCN never invented | Unchanged |
| `docs/DESIGN.md` motion + spark tokens | Updated |

Files: `app/styles.css`, `app/streamlit_app.py`, `src/harvester_risk_atlas/charts.py`, `docs/DESIGN.md`, `STATUS.md`.

**QA:** chart + spark imports OK; IUCN statuses `{not_queried}` only; PDF `%PDF-`; Streamlit boot HTTP 200 + `_stcore/health=ok`; AppTest Map page no exceptions.



### Judging packet docs (2026-09-29 ~20:35 Asia/Manila) — local only, no GitHub push

| Item | Status |
|------|--------|
| `docs/JUDGING.md` — Track 3 one-pager (problem, HPI, workflow, licenses, AI, demo URL, Demo mode path) | Done |
| `docs/VIDEO_SCRIPT.md` — 60–90s spoken script matching Demo mode | Done |
| `docs/SUBMISSION_CHECKLIST.md` — Devpost deliverables; **repo private flagged** | Done |
| README **For judges** section + layout links | Done |
| No browser / no git push | Observed |

**Flag for submit:** GitHub repo still private — publicize or share judge access before Devpost close.



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
6. Judging packet drafted (`docs/JUDGING.md`, `VIDEO_SCRIPT.md`, `SUBMISSION_CHECKLIST.md`) — still need public repo + record/upload video + ≤10 slides.
7. HPI weight sensitivity — on the Methods page (oral-defense explorer; v1.1 remains the official index).
8. Optional: `pip install kaleido` for PNG slide exports.

## Blockers
- None for offline `streamlit run` demo (climate + PA fidelity upgraded without tokens).
- Live IUCN categories blocked only on free API token registration.
