#!/usr/bin/env python3
"""Build species feature table from occurrences + seed metadata."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from harvester_risk_atlas.config import (
    DATA_PROCESSED,
    FEATURES_PARQUET,
    OCCURRENCES_PARQUET,
    SEED_SPECIES,
)
from harvester_risk_atlas.features import build_species_features


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    seed = pd.read_csv(SEED_SPECIES)
    if OCCURRENCES_PARQUET.exists():
        occ = pd.read_parquet(OCCURRENCES_PARQUET)
    else:
        raw = ROOT / "data" / "raw" / "gbif_occurrences_sample.csv"
        if raw.exists():
            occ = pd.read_csv(raw)
        else:
            print("No occurrences found — building features from seed only.")
            occ = pd.DataFrame()
    feats = build_species_features(occ, seed)
    feats.to_parquet(FEATURES_PARQUET, index=False)
    feats.to_csv(DATA_PROCESSED / "species_features.csv", index=False)
    print(f"Features: {len(feats)} species → {FEATURES_PARQUET}")


if __name__ == "__main__":
    main()
