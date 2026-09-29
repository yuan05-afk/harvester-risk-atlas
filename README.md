# Harvester Risk Atlas

**EthnoHACK 2026 — Track 3: Biodiversity & Sustainability**

One workflow: **Explore map** → **Species dossier** (HPI components, data gaps, archetype, decade hist) → **Field brief**. Also: **Compare** two species, **Demo mode** for judging video, Methods with cohort HPI distribution + archetype table.

Vernacular→scientific search is a thin helper only — not a second product.

> **Not medical advice.** Not a harvest permit. IUCN categories are never invented.

## Design

Calm Apple-minimal research UI: map + data as hero. See [`docs/DESIGN.md`](docs/DESIGN.md).

## Harvest Pressure Index (HPI v1.1)

```
HPI = 0.30·Rarity + 0.25·Climate stress + 0.25·Harvest proxy + 0.20·PA gap
```

Each component ∈ [0,1]; confidence penalizes imputed inputs. Full methods: [`docs/METHODS.md`](docs/METHODS.md).

## Quick start

```bash
cd /workspace/harvester-risk-atlas   # or your clone path
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .

# Offline demo uses shipped processed data:
scripts/run_app.sh
# → http://localhost:8501
```

### Rebuild features (network once, then offline)

```bash
source .venv/bin/activate
python scripts/fetch_gbif.py              # modest GBIF samples
python scripts/fetch_climate.py           # WorldClim 2.1 → SEA clip (~50 MB zip → ~300 KB)
python scripts/fetch_protected_areas.py   # WDPCA PH polygons via HDX (~4 MB)
# Optional — needs free token from https://api.iucnredlist.org/users/sign_up
# export IUCN_API_TOKEN=... && python scripts/fetch_iucn.py
python scripts/build_features.py
python scripts/compute_hpi.py
scripts/run_app.sh
```

Copy `.env.example` → `.env` for optional `IUCN_API_TOKEN` / `OPENAI_API_KEY`.
Without IUCN token the dossier shows `not_queried` — categories are **never invented**.

## Repository layout

```
app/                 Streamlit UI + styles.css
src/harvester_risk_atlas/   HPI, GBIF, features, names, IUCN stub, PDF brief
scripts/             fetch_gbif, fetch_climate, fetch_protected_areas, fetch_iucn, build_features, compute_hpi, run_app.sh
data/raw/            seed_species.csv (+ GBIF / WorldClim zip / WDPCA)
data/processed/      occurrences, features, HPI, SEA bioclim clips, PA gpkg, iucn_status
notebooks/           EDA
docs/METHODS.md      formula & licenses
docs/DESIGN.md       UI tokens & bans
STATUS.md            what works / blockers / Nov hack plan
```

## Deploy

Streamlit Community Cloud should use branch `main` and main file **`app/streamlit_app.py`**. See [`DEPLOY.md`](DEPLOY.md).

## Stack

pandas, geopandas, rasterio, folium, streamlit, plotly, scikit-learn, pygbif/requests, pyarrow, reportlab.

Optional: langchain/openai behind `ENABLE_LLM_NAMES=1`.

## AI / OSS disclosure

- Code and docs drafted with AI assistance (Grok / Cursor agent); reviewed for factual honesty (no invented IUCN statuses).
- Open-source libraries as listed in `requirements.txt` under their respective licenses.
- GBIF data: cite contributing datasets when publishing results.

## License

MIT for project code. Upstream data retain their own terms (GBIF, IUCN, WorldClim/CHELSA, WDPA).
