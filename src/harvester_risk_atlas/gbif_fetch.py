"""GBIF occurrence fetch helpers (pygbif or raw API). Modest volumes for demo."""
from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests

from .config import PH_BBOX

GBIF_OCC_URL = "https://api.gbif.org/v1/occurrence/search"


def search_species_key(scientific_name: str) -> int | None:
    """Resolve scientific name to GBIF usage key via species match API."""
    try:
        r = requests.get(
            "https://api.gbif.org/v1/species/match",
            params={"name": scientific_name, "strict": "false"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("matchType") in {"EXACT", "FUZZY", "HIGHERRANK"} and data.get("usageKey"):
            return int(data["usageKey"])
        return data.get("usageKey")
    except Exception:
        return None


def fetch_occurrences(
    scientific_name: str,
    *,
    species_key: int | None = None,
    limit: int = 200,
    country: str | None = "PH",
    use_bbox: bool = True,
) -> pd.DataFrame:
    """Fetch a small occurrence sample for one taxon.

    Prefers country=PH; if too few points, retries without country filter
    but keeps PH bbox when use_bbox=True for map focus.
    """
    key = species_key or search_species_key(scientific_name)
    rows: list[dict[str, Any]] = []

    def _page(params: dict[str, Any]) -> list[dict]:
        out: list[dict] = []
        offset = 0
        page_size = min(100, limit)
        while len(out) < limit:
            p = {**params, "limit": page_size, "offset": offset, "hasCoordinate": "true"}
            r = requests.get(GBIF_OCC_URL, params=p, timeout=60)
            r.raise_for_status()
            batch = r.json().get("results", [])
            if not batch:
                break
            out.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
            time.sleep(0.15)
        return out[:limit]

    params: dict[str, Any] = {}
    if key:
        params["taxonKey"] = key
    else:
        params["scientificName"] = scientific_name
    if country:
        params["country"] = country

    results = _page(params)
    if len(results) < 15 and country:
        # broaden: drop country, keep global but we still filter coords later
        params.pop("country", None)
        results = _page(params)

    for occ in results:
        lat = occ.get("decimalLatitude")
        lon = occ.get("decimalLongitude")
        if lat is None or lon is None:
            continue
        if use_bbox:
            if not (
                PH_BBOX["min_lat"] <= lat <= PH_BBOX["max_lat"]
                and PH_BBOX["min_lon"] <= lon <= PH_BBOX["max_lon"]
            ):
                # keep some SEA context if PH-empty
                if not ( -15 <= lat <= 30 and 90 <= lon <= 140):
                    continue
        rows.append(
            {
                "scientific_name": scientific_name,
                "gbif_taxon_key": key,
                "gbif_id": occ.get("key"),
                "lat": float(lat),
                "lon": float(lon),
                "year": occ.get("year"),
                "basis_of_record": occ.get("basisOfRecord"),
                "dataset_name": (occ.get("datasetName") or "")[:120],
                "country_code": occ.get("countryCode"),
            }
        )
    return pd.DataFrame(rows)


def fetch_seed_list(
    seed_df: pd.DataFrame,
    *,
    per_species: int = 80,
    sleep_s: float = 0.25,
) -> pd.DataFrame:
    """Fetch occurrences for each row in seed_species.csv."""
    frames = []
    for _, row in seed_df.iterrows():
        name = row["scientific_name"]
        try:
            df = fetch_occurrences(name, limit=per_species)
            df["vernacular_ph"] = row.get("vernacular_ph", "")
            frames.append(df)
            print(f"  GBIF {name}: {len(df)} pts")
        except Exception as e:
            print(f"  GBIF {name}: FAILED {e}")
            frames.append(
                pd.DataFrame(
                    columns=[
                        "scientific_name", "gbif_taxon_key", "gbif_id",
                        "lat", "lon", "year", "basis_of_record",
                        "dataset_name", "country_code", "vernacular_ph",
                    ]
                )
            )
        time.sleep(sleep_s)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
