"""HPI v2 components. Each is in [0, 1], higher = more priority, NaN = not measurable.

Every scale is anchored to fixed reference points, not to the cohort's own
min and max. Adding or removing a species therefore never changes another
species' component values (v1 used cohort min–max, which did).

R  Range restriction
   Mean of
   - local rarity: effort-corrected reporting rate. The share of well-surveyed
     Philippine H3 cells (≥ ``WELL_SURVEYED`` vascular-plant records in GBIF)
     where the species was recorded, on a log scale. 50% of cells → 0; 0.5% → 1.
   - global restriction: number of WCVP native regions (TDWG level 3).
     1 region → 1; 50 or more → 0, on a log scale.
H  Harvest sensitivity (curated; NaN when no cited traits)
   Mean of
   - part harvested: half the first-listed part, half the most destructive part
     (roots, rhizomes, bark and whole plants are destructive; Cunningham 2001)
   - life form: slow-regenerating woody plants score higher
   - sourcing: wild-only supply scores higher than wild + cultivated
E  Habitat exposure
   Mean of
   - protected-area gap: 1 − mean protected share of occupied cells
   - forest-loss exposure: tree-cover loss rate 2001–2023 in occupied provinces
     (0 → 0, 20% → 1), times forest affinity (forest 1, mixed 0.5, open 0).
     NaN when habitat is not curated.
C  Climate exposure (reported; default weight 0)
   Share of occupied cells where projected 2041–2060 mean annual temperature
   (SSP2-4.5, median of five GCMs) exceeds the warmest 5% of the species'
   current Philippine cells. Warming is about +1.5 °C for every species, so
   this barely separates species; it is shown, not weighted.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

WELL_SURVEYED = 100
RR_ANCHORS = (0.5, 0.005)
REGION_ANCHOR = 50
LOSS_ANCHOR = 0.20

PART_SCORE = {
    "whole_plant": 1.0,
    "underground": 1.0,
    "bark": 1.0,
    "stem": 0.75,
    "seed_fruit": 0.5,
    "exudate": 0.5,
    "leaf_flower": 0.25,
}
LIFE_FORM_SCORE = {
    "tree": 1.0,
    "palm": 0.9,
    "liana": 0.8,
    "shrub": 0.6,
    "fern": 0.5,
    "herbaceous_vine": 0.3,
    "herb": 0.3,
}
SOURCING_SCORE = {"wild_only": 1.0, "wild_and_cultivated": 0.5}
FOREST_AFFINITY = {"forest": 1.0, "mixed": 0.5, "open": 0.0}


def _log_anchor(value: float, high: float, low: float) -> float:
    """0 at ``high``, 1 at ``low``, linear in log10, clipped."""
    if value is None or not np.isfinite(value):
        return math.nan
    v = max(float(value), low / 10)
    s = (math.log10(high) - math.log10(v)) / (math.log10(high) - math.log10(low))
    return float(min(1.0, max(0.0, s)))


def _mean(values: list[float]) -> float:
    vals = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.mean(vals)) if vals else math.nan


def reporting_rate(cells: list[str], effort: dict[str, int], well: int = WELL_SURVEYED) -> float:
    surveyed = {c for c, n in effort.items() if n >= well}
    if not surveyed:
        return math.nan
    return len(set(cells) & surveyed) / len(surveyed)


def range_restriction(rr: float, n_native_regions: float) -> dict[str, float]:
    local = _log_anchor(rr, *RR_ANCHORS) if rr == rr and rr is not None else math.nan
    if rr == 0:
        local = math.nan  # never recorded in a well-surveyed cell: not measurable, not "rare"
    regions = float(n_native_regions) if n_native_regions else math.nan
    glob = (
        float(min(1.0, max(0.0, 1 - math.log(regions) / math.log(REGION_ANCHOR))))
        if regions == regions and regions >= 1
        else math.nan
    )
    return {"r_local": local, "r_global": glob, "R": _mean([local, glob])}


def harvest_sensitivity(part_classes: str, life_form: str, sourcing: str) -> dict[str, float]:
    parts = [p for p in str(part_classes or "").split(";") if p in PART_SCORE]
    if parts:
        part = 0.5 * PART_SCORE[parts[0]] + 0.5 * max(PART_SCORE[p] for p in parts)
    else:
        part = math.nan
    life = LIFE_FORM_SCORE.get(str(life_form or ""), math.nan)
    src = SOURCING_SCORE.get(str(sourcing or ""), math.nan)
    subs = [part, life, src]
    h = _mean(subs) if all(np.isfinite(s) for s in subs) else math.nan
    return {"h_part": part, "h_life_form": life, "h_sourcing": src, "H": h}


def habitat_exposure(pa_share: float, loss_rate: float, habitat: str) -> dict[str, float]:
    gap = 1.0 - float(pa_share) if pa_share is not None and np.isfinite(pa_share) else math.nan
    affinity = FOREST_AFFINITY.get(str(habitat or ""), math.nan)
    if loss_rate is not None and np.isfinite(loss_rate) and np.isfinite(affinity):
        forest = min(1.0, max(0.0, float(loss_rate) / LOSS_ANCHOR)) * affinity
    else:
        forest = math.nan
    return {"e_pa_gap": gap, "e_forest_loss": forest, "E": _mean([gap, forest])}


def thermal_exceedance(current: np.ndarray, futures: list[np.ndarray]) -> dict[str, float]:
    """Share of cells whose future bio1 exceeds the current 95th percentile, per GCM."""
    current = np.asarray(current, float)
    ok = np.isfinite(current)
    if ok.sum() < 3:
        return {"C": math.nan, "c_min": math.nan, "c_max": math.nan, "dT": math.nan, "dT_min": math.nan, "dT_max": math.nan}
    p95 = np.nanpercentile(current[ok], 95)
    shares, deltas = [], []
    for fut in futures:
        f = np.asarray(fut, float)
        m = ok & np.isfinite(f)
        shares.append(float(np.mean(f[m] > p95)))
        deltas.append(float(np.mean(f[m] - current[m])))
    return {
        "C": float(np.median(shares)),
        "c_min": min(shares),
        "c_max": max(shares),
        "dT": float(np.median(deltas)),
        "dT_min": min(deltas),
        "dT_max": max(deltas),
    }


def province_loss_for(cell_provinces: pd.Series, loss: pd.DataFrame) -> float:
    """Mean loss rate over occupied cells, each cell taking its modal province."""
    rates = loss.set_index("province")["loss_rate"]
    vals = cell_provinces.map(rates).dropna()
    return float(vals.mean()) if len(vals) else math.nan
