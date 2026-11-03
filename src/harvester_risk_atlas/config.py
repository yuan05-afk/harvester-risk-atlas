"""Paths and HPI v1 weights."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
SEED_SPECIES = DATA_RAW / "seed_species.csv"
OCCURRENCES_PARQUET = DATA_PROCESSED / "occurrences_sample.parquet"
FEATURES_PARQUET = DATA_PROCESSED / "species_features.parquet"
HPI_CSV = DATA_PROCESSED / "hpi_scores.csv"
IUCN_STATUS_CSV = DATA_PROCESSED / "iucn_status.csv"

# Climate / PA artifacts
WORLDCLIM_SEA_DIR = DATA_PROCESSED / "worldclim_sea"
PA_PROCESSED_GPKG = DATA_PROCESSED / "pa_wdpca_phl.gpkg"

# Geographic focus
PH_BBOX = dict(min_lat=4.0, max_lat=21.5, min_lon=116.0, max_lon=127.5)
# SEA clip used for WorldClim subset (saves space vs global 10′)
SEA_BBOX = dict(min_lat=-11.0, max_lat=28.0, min_lon=95.0, max_lon=141.0)

# HPI v1 transparent weights (must sum to 1.0)
HPI_WEIGHTS = {
    "rarity": 0.30,           # inverse occurrence richness / endemism proxy
    "climate_stress": 0.25,   # WorldClim bioclim niche / seasonality / thermal
    "harvest_proxy": 0.25,    # accessibility / temporal decline / demand cue
    "pa_gap": 0.20,           # share of points outside real PA polygons
}

# Confidence penalties when a component is imputed
CONFIDENCE_BASE = 0.85
CONFIDENCE_PENALTY_MISSING = 0.12  # per missing real component
