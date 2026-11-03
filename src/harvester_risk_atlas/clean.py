"""Occurrence cleaning. Each dropped record gets exactly one reason (the first rule it fails).

The rules follow common practice for GBIF data (Zizka et al. 2019,
CoordinateCleaner) where they can be applied without extra reference layers.
Province-centroid and institution-coordinate tests are not run because no
reference layer for them is shipped. METHODS.md lists that as a limitation.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import pandas as pd
from shapely.geometry import shape
from shapely.prepared import prep

from .config import DATA_PROCESSED

PH_LAND_MASK = DATA_PROCESSED / "ph_land_mask.geojson"
# The land mask is simplified to about 0.01°. A 0.03° (~3 km) buffer keeps
# coastal, mangrove and beach records that sit just past the simplified line.
LAND_BUFFER_DEG = 0.03
MAX_UNCERTAINTY_M = 10_000
# Approximate geographic centre of the Philippines, where country-level
# georeferencing tends to drop records.
PH_CENTROID = (12.8797, 121.7740)
CENTROID_RADIUS_KM = 5.0

SEVERE_ISSUES = frozenset(
    {
        "ZERO_COORDINATE",
        "COORDINATE_OUT_OF_RANGE",
        "COORDINATE_INVALID",
        "COUNTRY_COORDINATE_MISMATCH",
        "PRESUMED_SWAPPED_COORDINATE",
        "PRESUMED_NEGATED_LATITUDE",
        "PRESUMED_NEGATED_LONGITUDE",
        "COORDINATE_REPROJECTION_FAILED",
    }
)
NOT_WILD_BASIS = frozenset({"LIVING_SPECIMEN", "FOSSIL_SPECIMEN"})
CULTIVATED_MEANS = frozenset({"MANAGED"})

REASONS = (
    "missing_coordinates",
    "zero_coordinates",
    "severe_issue",
    "not_wild_basis",
    "cultivated",
    "imprecise",
    "country_centroid",
    "off_land",
    "duplicate",
)


@lru_cache(maxsize=1)
def _land():
    data = json.loads(PH_LAND_MASK.read_text(encoding="utf-8"))
    geom = shape(data["features"][0]["geometry"]).buffer(LAND_BUFFER_DEG)
    return prep(geom)


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def _has_severe_issue(issues: object) -> bool:
    if not isinstance(issues, str) or not issues:
        return False
    return any(i in SEVERE_ISSUES for i in issues.split(";"))


def flag_records(df: pd.DataFrame) -> pd.Series:
    """Return the drop reason per row ("" keeps the row). The input is not modified."""
    reason = pd.Series("", index=df.index, dtype=object)

    def mark(mask: pd.Series, why: str) -> None:
        reason.loc[mask & (reason == "")] = why

    lat = pd.to_numeric(df["lat"], errors="coerce")
    lon = pd.to_numeric(df["lon"], errors="coerce")
    mark(lat.isna() | lon.isna(), "missing_coordinates")
    mark((lat == 0) | (lon == 0) | (lat == lon), "zero_coordinates")
    mark(df["issues"].map(_has_severe_issue), "severe_issue")
    mark(df["basis_of_record"].isin(NOT_WILD_BASIS), "not_wild_basis")
    mark(df["establishment_means"].isin(CULTIVATED_MEANS), "cultivated")

    unc = pd.to_numeric(df["coordinate_uncertainty_m"], errors="coerce")
    whole_degrees = (lat.round(0) == lat) & (lon.round(0) == lon)
    mark((unc > MAX_UNCERTAINTY_M) | whole_degrees, "imprecise")

    live = reason == ""
    dist = pd.Series(np.inf, index=df.index)
    dist.loc[live] = _haversine_km(lat[live], lon[live], *PH_CENTROID)
    mark(dist <= CENTROID_RADIUS_KM, "country_centroid")

    land = _land()
    live = reason == ""
    from shapely.geometry import Point

    on_land = pd.Series(True, index=df.index)
    on_land.loc[live] = [land.covers(Point(x, y)) for x, y in zip(lon[live], lat[live])]
    mark(~on_land, "off_land")

    live = reason == ""
    key = pd.DataFrame(
        {
            "sp": df["scientific_name"],
            "lat": lat.round(4),
            "lon": lon.round(4),
            "year": pd.to_numeric(df["year"], errors="coerce"),
        }
    )
    dup = key[live].duplicated(keep="first")
    mark(dup.reindex(df.index, fill_value=False), "duplicate")
    return reason


def clean_occurrences(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Kept records, plus a per-species table of counts by drop reason."""
    if df.empty:
        cols = ["scientific_name", "n_fetched", "n_kept", *REASONS]
        return df.copy(), pd.DataFrame(columns=cols)
    reason = flag_records(df)
    kept = df.loc[reason == ""].copy()
    kept["lat"] = pd.to_numeric(kept["lat"])
    kept["lon"] = pd.to_numeric(kept["lon"])
    tally = (
        pd.DataFrame({"scientific_name": df["scientific_name"], "reason": reason})
        .assign(n=1)
        .pivot_table(index="scientific_name", columns="reason", values="n", aggfunc="sum", fill_value=0)
    )
    report = pd.DataFrame(index=tally.index)
    report["n_fetched"] = tally.sum(axis=1)
    report["n_kept"] = tally[""] if "" in tally.columns else 0
    for why in REASONS:
        report[why] = tally[why] if why in tally.columns else 0
    return kept.reset_index(drop=True), report.reset_index().astype({c: int for c in report.columns})
