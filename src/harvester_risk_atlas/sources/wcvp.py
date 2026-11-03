"""Native status in the Philippines from the World Checklist of Vascular Plants.

WCVP (Govaerts et al. 2021, CC BY 4.0) is read through its GBIF-hosted
checklist. Kew's POWO API sits behind a bot challenge, so it is not used.
The Philippines is TDWG level-3 region ``PHI``.

Statuses:
  native       PHI listed without an establishment flag
  introduced   PHI listed as INTRODUCED
  not_listed   PHI absent from the species' WCVP distribution
  not_found    the name did not resolve in WCVP
"""
from __future__ import annotations

from typing import Any

from ..config import DATA_RAW
from .http import get_json, read_cache, utc_now, write_cache

API = "https://api.gbif.org/v1"
WCVP_DATASET = "f382f0ce-323a-4091-bb9f-add557f3a9a2"
PH_TDWG = "TDWG:PHI"
CACHE_DIR = DATA_RAW / "wcvp"
CITATION = (
    "Govaerts R, Nic Lughadha E, Black N, Turner R, Paton A (2021). The World Checklist of "
    "Vascular Plants, a continuously updated resource for exploring global plant diversity. "
    "Scientific Data 8: 215. Accessed via GBIF checklist " + WCVP_DATASET + "."
)


def _wcvp_usage(name: str) -> dict[str, Any] | None:
    data = get_json(
        f"{API}/species/search",
        {"q": name, "datasetKey": WCVP_DATASET, "rank": "SPECIES", "limit": 20},
    )
    target = name.lower().replace("×", "x").split()
    rows = [
        r
        for r in data.get("results", [])
        if (r.get("canonicalName") or "").lower().replace("×", "x").split() == target
    ]
    if not rows:
        return None
    accepted = [r for r in rows if r.get("taxonomicStatus") == "ACCEPTED"]
    row = accepted[0] if accepted else rows[0]
    if row.get("taxonomicStatus") != "ACCEPTED" and row.get("acceptedKey"):
        row = get_json(f"{API}/species/{row['acceptedKey']}")
    return row


def _distributions(key: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = get_json(f"{API}/species/{key}/distributions", {"limit": 100, "offset": offset})
        out.extend(page.get("results", []))
        if page.get("endOfRecords") or not page.get("results"):
            return out
        offset += 100


def classify(distribution: list[dict[str, Any]]) -> dict[str, Any]:
    """PH status from a list of WCVP distribution rows. Pure, for tests."""
    native_regions = [d["locationId"] for d in distribution if not d.get("establishmentMeans")]
    ph = [d for d in distribution if d.get("locationId") == PH_TDWG]
    if not ph:
        status = "not_listed"
    elif ph[0].get("establishmentMeans") == "INTRODUCED":
        status = "introduced"
    else:
        status = "native"
    return {
        "ph_status": status,
        "ph_endemic": status == "native" and native_regions == [PH_TDWG],
        "n_native_regions": len(native_regions),
    }


def nativity(name: str, *, offline: bool = False) -> dict[str, Any]:
    path = CACHE_DIR / f"{name.replace(' ', '_').replace('×', 'x')}.json.gz"
    cached = read_cache(path)
    if cached is None:
        if offline:
            raise FileNotFoundError(f"No cached WCVP status for {name}")
        usage = _wcvp_usage(name)
        if usage is None:
            cached = {"wcvp_key": None, "wcvp_name": None, "distribution": [], "found": False}
        else:
            cached = {
                "wcvp_key": usage["key"],
                "wcvp_name": usage.get("canonicalName"),
                "distribution": [
                    {"locationId": d.get("locationId"), "establishmentMeans": d.get("establishmentMeans")}
                    for d in _distributions(int(usage["key"]))
                ],
                "found": True,
            }
        cached["fetched_at"] = utc_now()
        write_cache(path, cached)
    if not cached["found"]:
        result = {"ph_status": "not_found", "ph_endemic": False, "n_native_regions": 0}
    else:
        result = classify(cached["distribution"])
    return {
        "query_name": name,
        "wcvp_key": cached["wcvp_key"],
        "wcvp_name": cached["wcvp_name"],
        **result,
        "fetched_at": cached["fetched_at"],
    }
