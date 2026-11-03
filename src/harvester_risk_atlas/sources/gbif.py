"""GBIF backbone matching, exact occurrence counts, and full PH record pages.

v1 took the first 60 search results per species. Those were not a random
sample, and the cap made every count equal. v2 reads exact totals from
search facets and pages every Philippine record up to ``RECORD_CAP``. When
the cap is hit, the species is flagged; the counts stay exact either way.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import DATA_RAW
from .http import get_json, read_cache, utc_now, write_cache

API = "https://api.gbif.org/v1"
CACHE_DIR = DATA_RAW / "gbif"
RECORD_CAP = 5000
PAGE_SIZE = 300

# Columns kept from each occurrence. Everything else in the GBIF record is dropped.
RECORD_COLUMNS = [
    "gbif_id",
    "lat",
    "lon",
    "coordinate_uncertainty_m",
    "year",
    "basis_of_record",
    "establishment_means",
    "issues",
    "dataset_key",
    "license",
    "country_code",
    "gadm_level1",
    "gadm_level2",
]


def match_name(name: str) -> dict[str, Any]:
    """Resolve a name against the GBIF backbone. Synonyms resolve to the accepted key."""
    data = get_json(f"{API}/species/match", {"name": name, "kingdom": "Plantae"})
    status = data.get("status")
    usage = data.get("usageKey")
    accepted = data.get("acceptedUsageKey") or usage
    return {
        "query_name": name,
        "gbif_usage_key": usage,
        "gbif_taxon_key": accepted,
        "gbif_name": data.get("species") or data.get("canonicalName"),
        "gbif_status": status,
        "gbif_match_type": data.get("matchType"),
        "gbif_confidence": data.get("confidence"),
        "gbif_family": data.get("family"),
    }


def occurrence_counts(taxon_key: int, country: str = "PH") -> dict[str, Any]:
    """Exact totals from search facets. No records are downloaded."""
    base = {"taxonKey": taxon_key, "occurrenceStatus": "PRESENT", "limit": 0}
    in_country = get_json(
        f"{API}/occurrence/search",
        {
            **base,
            "country": country,
            "facet": ["basisOfRecord", "year"],
            "facetLimit": 400,
        },
    )
    georef = get_json(
        f"{API}/occurrence/search",
        {**base, "country": country, "hasCoordinate": "true", "hasGeospatialIssue": "false"},
    )
    world = get_json(f"{API}/occurrence/search", base)
    facets = {f["field"]: {c["name"]: c["count"] for c in f["counts"]} for f in in_country.get("facets", [])}
    return {
        "n_country": int(in_country.get("count", 0)),
        "n_country_georeferenced": int(georef.get("count", 0)),
        "n_world": int(world.get("count", 0)),
        "basis_of_record": facets.get("BASIS_OF_RECORD", {}),
        "year": facets.get("YEAR", {}),
    }


def _flatten(rec: dict[str, Any]) -> dict[str, Any]:
    gadm = rec.get("gadm") or {}
    return {
        "gbif_id": rec.get("key"),
        "lat": rec.get("decimalLatitude"),
        "lon": rec.get("decimalLongitude"),
        "coordinate_uncertainty_m": rec.get("coordinateUncertaintyInMeters"),
        "year": rec.get("year"),
        "basis_of_record": rec.get("basisOfRecord"),
        "establishment_means": rec.get("establishmentMeans"),
        "issues": ";".join(rec.get("issues") or []),
        "dataset_key": rec.get("datasetKey"),
        "license": rec.get("license"),
        "country_code": rec.get("countryCode"),
        "gadm_level1": (gadm.get("level1") or {}).get("name"),
        "gadm_level2": (gadm.get("level2") or {}).get("name"),
    }


def fetch_records(taxon_key: int, country: str = "PH", cap: int = RECORD_CAP) -> tuple[list[dict], bool]:
    """Every georeferenced, present record in ``country``, up to ``cap``.

    Returns the flattened records and whether the cap was reached.
    """
    out: list[dict] = []
    offset = 0
    while len(out) < cap:
        page = get_json(
            f"{API}/occurrence/search",
            {
                "taxonKey": taxon_key,
                "country": country,
                "hasCoordinate": "true",
                "occurrenceStatus": "PRESENT",
                "limit": min(PAGE_SIZE, cap - len(out)),
                "offset": offset,
            },
        )
        batch = page.get("results", [])
        out.extend(_flatten(r) for r in batch)
        if page.get("endOfRecords") or not batch:
            return out, False
        offset += len(batch)
        time.sleep(0.2)
    return out[:cap], True


def cache_path(taxon_key: int, country: str = "PH") -> Path:
    return CACHE_DIR / f"{taxon_key}_{country}.json.gz"


def fetch_species(name: str, *, country: str = "PH", offline: bool = False) -> dict[str, Any]:
    """Match, count, and page one species. Uses the on-disk cache when present.

    ``offline=True`` never touches the network and raises if the cache is missing.
    """
    match_file = CACHE_DIR / "matches" / f"{name.replace(' ', '_').replace('×', 'x')}.json.gz"
    match = read_cache(match_file)
    if match is None:
        if offline:
            raise FileNotFoundError(f"No cached GBIF match for {name}")
        match = {**match_name(name), "fetched_at": utc_now()}
        write_cache(match_file, match)
    key = match.get("gbif_taxon_key")
    if not key:
        return {"match": match, "counts": None, "records": [], "capped": False, "fetched_at": None}

    path = cache_path(int(key), country)
    cached = read_cache(path)
    if cached is None:
        if offline:
            raise FileNotFoundError(f"No cached GBIF records for {name} ({key})")
        counts = occurrence_counts(int(key), country)
        records, capped = fetch_records(int(key), country)
        cached = {
            "taxon_key": int(key),
            "country": country,
            "fetched_at": utc_now(),
            "counts": counts,
            "capped": capped,
            "records": records,
        }
        write_cache(path, cached)
    return {
        "match": match,
        "counts": cached["counts"],
        "records": cached["records"],
        "capped": cached["capped"],
        "fetched_at": cached["fetched_at"],
    }


def records_frame(name: str, payload: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(payload["records"], columns=RECORD_COLUMNS)
    df.insert(0, "scientific_name", name)
    return df
