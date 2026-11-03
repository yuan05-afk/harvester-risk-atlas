#!/usr/bin/env python3
"""Fetch IUCN Red List categories for seed species (API v4).

Requires IUCN_API_TOKEN in env or .env.
  Free signup: https://api.iucnredlist.org/users/sign_up

Without a token, writes not_queried rows (never invents categories).
IUCN is a separate dossier field — not baked into HPI.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from harvester_risk_atlas.config import DATA_PROCESSED, IUCN_STATUS_CSV, SEED_SPECIES
from harvester_risk_atlas.iucn import SIGNUP_URL, get_token, lookup_many


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    seed = pd.read_csv(SEED_SPECIES)
    names = seed["scientific_name"].tolist()
    token = get_token()
    if not token:
        print(
            f"IUCN_API_TOKEN not set — writing not_queried for {len(names)} species.\n"
            f"Get a free research token: {SIGNUP_URL}\n"
            f"Then: export IUCN_API_TOKEN=... && python scripts/fetch_iucn.py"
        )
    else:
        print(f"Querying IUCN API v4 for {len(names)} species…")
    df = lookup_many(names, token=token or None)
    df.to_csv(IUCN_STATUS_CSV, index=False)
    ok = (df["iucn_status"] == "ok").sum() if "iucn_status" in df.columns else 0
    print(f"Wrote {IUCN_STATUS_CSV} (ok={ok}, total={len(df)})")
    print(df[["scientific_name", "iucn_category_code", "iucn_status"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
