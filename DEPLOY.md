# Deploy — Harvester Risk Atlas (Streamlit Community Cloud)

Brief notes for a public demo. Offline demo data ships under `data/processed/`.

## Streamlit Community Cloud

1. Push this repo to GitHub (public or private with Cloud access).
2. [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Settings:
   - **Main file path:** `app/streamlit_app.py`
   - **Python version:** 3.11 or 3.12
   - **Requirements file:** `requirements.txt`
4. Deploy. First build installs pinned deps (~2–4 min).

No secrets are required for the offline demo. Optional secrets (Cloud → App settings → Secrets):

```toml
IUCN_API_TOKEN = "…"          # live Red List categories only
# OPENAI_API_KEY = "…"        # only if ENABLE_LLM_NAMES=1
```

Without `IUCN_API_TOKEN` the dossier shows **IUCN not linked** — categories are never invented.

## Local parity check

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
scripts/run_app.sh   # → http://localhost:8501
```

## PDF field brief

On the **Field brief** page: download HTML (always) and PDF (reportlab).

Smoke test without Streamlit:

```bash
python -c "
from harvester_risk_atlas.pdf_brief import render_field_brief_pdf
from harvester_risk_atlas.hpi import dossier_actions
import pandas as pd
row = pd.read_csv('data/processed/hpi_scores.csv').iloc[1].to_dict()
pdf = render_field_brief_pdf(row, dossier_actions(row))
open('/tmp/field_brief_smoke.pdf','wb').write(pdf)
print(len(pdf), 'bytes')
"
```

## Cloud notes

- `rasterio` / `geopandas` wheels are prebuilt on manylinux; Cloud usually fine. If a build fails on GDAL, pin older `rasterio`/`geopandas` or omit live rebuild scripts (demo uses shipped parquet/csv/gpkg).
- Large WorldClim zips are **not** needed at runtime — SEA clips are under `data/processed/worldclim_sea/`.
- Hide the Deploy/toolbar chrome via `app/styles.css` (already applied).
- Keep the disclaimer visible; disclose AI/OSS in README for judging.

- After a push that adds new package exports (e.g. `hpi_spark_svg`), **reboot** the Cloud app
  if you still see `ImportError: cannot import name …` — Streamlit can keep a stale module
  cache across soft reloads. `requirements.txt` includes `-e .` so the `src/` package installs.


## App entry

`scripts/run_app.sh` runs:

```bash
streamlit run app/streamlit_app.py --server.port 8501
```
