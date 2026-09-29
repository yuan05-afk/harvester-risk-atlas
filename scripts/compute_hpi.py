#!/usr/bin/env python3
"""Compute Harvest Pressure Index v1 from species features."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from harvester_risk_atlas.config import FEATURES_PARQUET, HPI_CSV, DATA_PROCESSED
from harvester_risk_atlas.hpi import compute_hpi, hpi_formula_markdown


def main() -> None:
    if not FEATURES_PARQUET.exists():
        raise SystemExit(f"Missing {FEATURES_PARQUET} — run build_features.py first")
    feats = pd.read_parquet(FEATURES_PARQUET)
    scored = compute_hpi(feats)
    cols = [
        "scientific_name", "vernacular_ph", "family", "n_occurrences",
        "lat_mean", "lon_mean", "hpi", "hpi_band", "hpi_confidence",
        "component_rarity", "component_climate", "component_harvest", "component_pa_gap",
        "climate_imputed", "harvest_imputed", "pa_gap_imputed",
        "notes", "endemism_proxy", "demo_iucn_note", "data_source_note",
        "frac_in_protected", "frac_in_protected_proxy", "mean_dist_to_pa_km",
        "recent_occurrence_frac",
        "climate_stress_raw", "climate_anomaly_proxy",
        "bio1_mean", "bio1_std", "bio12_mean", "bio15_mean",
        "climate_method", "climate_source",
        "pa_source", "pa_method",
        "iucn_category", "iucn_category_code", "iucn_status", "iucn_note",
        "iucn_assessment_id", "iucn_year",
        "harvest_concern_flag",
    ]
    cols = [c for c in cols if c in scored.columns]
    out = scored[cols].sort_values("hpi", ascending=False)
    out.to_csv(HPI_CSV, index=False)
    scored.to_parquet(DATA_PROCESSED / "hpi_scores.parquet", index=False)
    print(hpi_formula_markdown())
    print(f"Wrote {HPI_CSV} ({len(out)} species)")
    show = [c for c in ["scientific_name", "hpi", "hpi_band", "hpi_confidence",
                        "iucn_status", "climate_source", "pa_source"] if c in out.columns]
    print(out[show].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
