#!/usr/bin/env python3
"""Fetch modest GBIF occurrence samples for seed species; write raw + parquet."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harvester_risk_atlas.config import DATA_PROCESSED, DATA_RAW, OCCURRENCES_PARQUET, SEED_SPECIES
from harvester_risk_atlas.gbif_fetch import fetch_seed_list
import pandas as pd


def main() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    seed = pd.read_csv(SEED_SPECIES)
    print(f"Fetching GBIF for {len(seed)} taxa (small samples)…")
    occ = fetch_seed_list(seed, per_species=60)
    raw_csv = DATA_RAW / "gbif_occurrences_sample.csv"
    occ.to_csv(raw_csv, index=False)
    occ.to_parquet(OCCURRENCES_PARQUET, index=False)
    print(f"Wrote {len(occ)} rows → {raw_csv}")
    print(f"Wrote {OCCURRENCES_PARQUET}")
    print(occ.groupby("scientific_name").size().describe())


if __name__ == "__main__":
    main()
