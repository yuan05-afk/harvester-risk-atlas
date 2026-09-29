# Methods — Harvest Pressure Index (HPI) v1.1

EthnoHACK 2026 Track 3 (Biodiversity & Sustainability). Transparent, reproducible research index — **not** IUCN status, **not** medical advice, **not** a permit.

## Formula

\[
\mathrm{HPI} = 0.30\,R + 0.25\,C + 0.25\,H + 0.20\,P
\]

Each of \(R,C,H,P \in [0,1]\). Higher HPI ⇒ higher *relative* harvest/climate pressure concern for monitoring.

| Component | Symbol | Construction (v1.1) |
|-----------|--------|---------------------|
| Rarity | \(R\) | 0.7 · min-max inverted log1p(GBIF n) + 0.3 · endemism cue from seed notes (SEA_forest > PH_SEA > cultivated…) |
| Climate stress | \(C\) | **WorldClim 2.1** (10′, SEA clip): 0.75 · cohort min-max of species `climate_stress_raw` + 0.25 · lat-range backup. Raw cue = 0.40·niche-squeeze(1/(1+bio1_std)) + 0.35·bio15/100 + 0.25·\|bio1−regional\|/8 |
| Harvest proxy | \(H\) | 0.4 · local occurrence density + 0.35 · inverted recent-occurrence fraction (year≥2015) + 0.25 · literature harvest-concern flag |
| PA gap | \(P\) | \(1 -\) fraction of GBIF points inside **WDPCA Philippines** polygons, plus a mild distance boost (≤0.15) when mean distance to nearest PA is large |

**IUCN Red List category is a separate dossier field. It is never invented and is not an HPI input.**

### Confidence

\[
\mathrm{confidence} = \mathrm{clip}_{[0.2,0.95]}(0.85 - 0.12 \cdot n_{\mathrm{imputed}})
\]

A component is *imputed* when live inputs (recent frac, PA frac, WorldClim sample) are missing for that species.

### Bands

| HPI | Band label |
|-----|------------|
| ≤ 0.33 | Lower relative pressure |
| ≤ 0.66 | Moderate |
| > 0.66 | Higher relative pressure |

## Data sources & licenses

| Resource | Use | Access / license notes |
|----------|-----|------------------------|
| [GBIF](https://www.gbif.org/) | Occurrence samples via public API / `pygbif` | Follow GBIF citation guidelines; respect rate limits |
| Seed CSV | Scientific + PH vernacular + ethnobotany brief | Project-curated; DOH herbal list used only as *cultural context*, not efficacy claims |
| [IUCN Red List API v4](https://api.iucnredlist.org/) | Official threat categories (dossier only) | **Free token**: [sign up](https://api.iucnredlist.org/users/sign_up). [Terms of use](https://www.iucnredlist.org/terms/terms-of-use). Without token → `not_queried`. **Never invent categories.** |
| [WorldClim 2.1](https://www.worldclim.org/) bio1, bio12, bio15 @ 10′ | Climate stress | Global zip ~50 MB; we ship **SEA bbox clip** (~300 KB) under `data/processed/worldclim_sea/`. Cite Fick & Hijmans (2017). Research / non-commercial terms. |
| [WDPCA Philippines (HDX)](https://data.humdata.org/dataset/unep_wdpca_phl) | Real PA polygons for overlap / distance | UNEP-WCMC Protected Planet / WDPA family. **Hackathon research & education**; cite Protected Planet. Not a DENR permitting product. Raw ~4 MB gpkg; processed `data/processed/pa_wdpca_phl.gpkg`. |
| OSM `boundary=protected_area` (optional cache) | QA / secondary | [ODbL](https://opendatacommons.org/licenses/odbl/). Not used as primary HPI geometry. |
| Natural Earth parks | *Not used for PH scoring* | Public domain / NE terms — layer is US NPS–centric; documented as non-fit for PH. |

### Size limits (hack week)

| Artifact | Approx size | Notes |
|----------|-------------|-------|
| WorldClim 10′ full bio zip | ~50 MB | Downloaded once by `scripts/fetch_climate.py` |
| SEA clipped bio1/12/15 | ~300 KB | Shipped for offline demo |
| WDPCA PH geopackage | ~4 MB | Downloaded by `scripts/fetch_protected_areas.py` |
| Processed PA gpkg | ~similar | EPSG:4326 polygons only |
| IUCN status CSV | <50 KB | Categories only when token set |

## Rebuild pipeline

```bash
source .venv/bin/activate
# optional: IUCN (needs token)
python scripts/fetch_iucn.py
# climate + PA (network once; then offline)
python scripts/fetch_climate.py
python scripts/fetch_protected_areas.py
python scripts/build_features.py
python scripts/compute_hpi.py
scripts/run_app.sh
```

## Risk archetypes (sklearn)

KMeans (`k≈4`) on standardized HPI components \(R,C,H,P\). Cluster labels are assigned by which component mean sits furthest *above* the atlas cohort mean (e.g. Harvest-pressured, Climate-stressed, PA-gap exposed, Sparse / rarity-driven). Computed at app load — not persisted in `hpi_scores.csv`. **Descriptive only; not IUCN status.**

## Occurrence timing

Decade histograms use GBIF sample `year` when present (demo extract has years; no `eventDate` column). If neither is available for a species, the chart is skipped gracefully.

## Exploratory suitability sketch

Optional RandomForest presence/background classifier on lat/lon + species-level WorldClim bio1/bio12/bio15 means (background = uniform random in SEA bbox). Shown in a dossier expander. **Not a species distribution model** — no spatial CV, bioclim broadcast from species means, unsuitable for permitting or publication as SDM.

## Ethics & claims policy

- No medical advice; no unvalidated efficacy claims.
- Ethnobotany text is cultural/documentary context only.
- Disclose AI assistance and OSS licenses in README / judging materials.
- Synthetic or proxy fields are always labeled; v1.1 climate/PA are real open layers with documented licenses.
- IUCN categories appear only from live API responses (or explicit `not_queried`).
