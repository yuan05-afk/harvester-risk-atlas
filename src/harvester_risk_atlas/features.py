"""Build per-species feature table from occurrences + seed metadata + climate/PA."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .climate import species_climate_from_occurrences
from .config import IUCN_STATUS_CSV
from .protected_areas import species_pa_metrics


def _harvest_concern(notes: str, endemism: str) -> int:
    text = f"{notes} {endemism}".lower()
    cues = ("overharvest", "harvest pressure", "forest", "sea_forest", "root")
    return int(any(c in text for c in cues))


def _load_iucn_table() -> pd.DataFrame:
    if IUCN_STATUS_CSV.exists():
        return pd.read_csv(IUCN_STATUS_CSV)
    return pd.DataFrame()


def _merge_iucn(feat: pd.DataFrame, iucn: pd.DataFrame, seed_names: list[str]) -> pd.DataFrame:
    if iucn.empty:
        iucn = pd.DataFrame(
            {
                "scientific_name": seed_names,
                "iucn_category": [None] * len(seed_names),
                "iucn_category_code": [None] * len(seed_names),
                "iucn_assessment_id": [None] * len(seed_names),
                "iucn_year": [None] * len(seed_names),
                "iucn_status": ["not_queried"] * len(seed_names),
                "iucn_note": [
                    "Set IUCN_API_TOKEN and run scripts/fetch_iucn.py. Never invent categories."
                ]
                * len(seed_names),
            }
        )
    cols = [
        c
        for c in (
            "scientific_name",
            "iucn_category",
            "iucn_category_code",
            "iucn_assessment_id",
            "iucn_year",
            "iucn_status",
            "iucn_note",
        )
        if c in iucn.columns
    ]
    out = feat.merge(iucn[cols], on="scientific_name", how="left")
    out["iucn_status"] = out.get("iucn_status", pd.Series(dtype=object)).fillna("not_queried")
    if "iucn_category" not in out.columns:
        out["iucn_category"] = None
    if "iucn_note" not in out.columns:
        out["iucn_note"] = "Set IUCN_API_TOKEN; never invent categories"
    return out


def _seed_stub_rows(seed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, meta in seed.iterrows():
        rows.append(
            {
                "scientific_name": meta["scientific_name"],
                "vernacular_ph": meta.get("vernacular_ph", ""),
                "family": meta.get("family", ""),
                "notes": meta.get("notes", ""),
                "endemism_proxy": meta.get("endemism_proxy", "widespread"),
                "demo_iucn_note": meta.get(
                    "demo_iucn_note",
                    "not queried — set IUCN_API_TOKEN to fetch; never invent status",
                ),
                "n_occurrences": 0,
                "lat_mean": np.nan,
                "lon_mean": np.nan,
                "lat_min": np.nan,
                "lat_max": np.nan,
                "lon_min": np.nan,
                "lon_max": np.nan,
                "year_min": np.nan,
                "year_max": np.nan,
                "recent_occurrence_frac": np.nan,
                "harvest_concern_flag": _harvest_concern(
                    str(meta.get("notes", "")), str(meta.get("endemism_proxy", ""))
                ),
                "data_source_note": "no_occurrences",
            }
        )
    return pd.DataFrame(rows)


def build_species_features(
    occurrences: pd.DataFrame,
    seed: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate occurrence points → species-level features for HPI + dossier."""
    seed_names = seed["scientific_name"].tolist()
    climate = species_climate_from_occurrences(occurrences, seed_names)
    pa = species_pa_metrics(occurrences, seed_names)
    iucn = _load_iucn_table()

    if occurrences.empty or occurrences.dropna(subset=["lat", "lon"]).empty:
        feat = _seed_stub_rows(seed)
    else:
        occ = occurrences.dropna(subset=["lat", "lon"]).copy()
        recent_cutoff = 2015
        rows = []
        for name, g in occ.groupby("scientific_name"):
            years = g["year"].dropna()
            recent_frac = float((years >= recent_cutoff).mean()) if len(years) else np.nan
            seed_row = seed.loc[seed["scientific_name"] == name]
            meta = seed_row.iloc[0].to_dict() if len(seed_row) else {}
            rows.append(
                {
                    "scientific_name": name,
                    "vernacular_ph": meta.get("vernacular_ph")
                    or (g["vernacular_ph"].iloc[0] if "vernacular_ph" in g else ""),
                    "family": meta.get("family", ""),
                    "notes": meta.get("notes", ""),
                    "endemism_proxy": meta.get("endemism_proxy", "widespread"),
                    "demo_iucn_note": meta.get(
                        "demo_iucn_note",
                        "not queried — set IUCN_API_TOKEN to fetch; never invent status",
                    ),
                    "n_occurrences": int(len(g)),
                    "lat_mean": float(g["lat"].mean()),
                    "lon_mean": float(g["lon"].mean()),
                    "lat_min": float(g["lat"].min()),
                    "lat_max": float(g["lat"].max()),
                    "lon_min": float(g["lon"].min()),
                    "lon_max": float(g["lon"].max()),
                    "year_min": float(years.min()) if len(years) else np.nan,
                    "year_max": float(years.max()) if len(years) else np.nan,
                    "recent_occurrence_frac": recent_frac,
                    "harvest_concern_flag": _harvest_concern(
                        str(meta.get("notes", "")), str(meta.get("endemism_proxy", ""))
                    ),
                    "data_source_note": "gbif_sample",
                }
            )
        feat = pd.DataFrame(rows)
        missing = seed[~seed["scientific_name"].isin(feat["scientific_name"])]
        if len(missing):
            feat = pd.concat([feat, _seed_stub_rows(missing)], ignore_index=True)

    feat = feat.merge(climate, on="scientific_name", how="left")
    feat = feat.merge(pa, on="scientific_name", how="left")
    feat = _merge_iucn(feat, iucn, seed_names)
    # Back-compat aliases (older column names still referenced in HPI/UI)
    feat["frac_in_protected_proxy"] = feat["frac_in_protected"]
    feat["climate_anomaly_proxy"] = feat["climate_stress_raw"]
    return feat.reset_index(drop=True)
