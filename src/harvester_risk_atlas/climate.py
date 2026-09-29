"""WorldClim 2.1 bioclim extract for PH/SEA (climate stress inputs).

Downloads/clips are handled by scripts/fetch_climate.py. This module only
samples clipped GeoTIFFs (bio1, bio12, bio15) at occurrence points / centroids.
Open-Meteo is available as an optional online fallback for centroids when
rasters are missing.

License: WorldClim 2.1 — free for non-commercial / research use; cite Fick &
Hijmans 2017. Do not redistribute commercial derivatives without checking terms.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import DATA_PROCESSED, WORLDCLIM_SEA_DIR

BIO_FILES = {
    "bio1": "wc2.1_10m_bio1_sea.tif",   # mean annual temperature (°C)
    "bio12": "wc2.1_10m_bio12_sea.tif",  # annual precipitation (mm)
    "bio15": "wc2.1_10m_bio15_sea.tif",  # precip seasonality (CV)
}

CLIMATE_METHOD = (
    "WorldClim 2.1 10-arcmin bio1/bio12/bio15 clipped to SEA bbox "
    "(lon 95–141, lat −11–28); stress = niche squeeze + seasonality + thermal anomaly"
)


def worldclim_paths(base: Path | None = None) -> dict[str, Path]:
    root = base or WORLDCLIM_SEA_DIR
    return {k: root / v for k, v in BIO_FILES.items()}


def rasters_available(base: Path | None = None) -> bool:
    paths = worldclim_paths(base)
    return all(p.exists() for p in paths.values())


def _sample_raster(path: Path, lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    import rasterio

    out = np.full(len(lons), np.nan, dtype=float)
    with rasterio.open(path) as src:
        nodata = src.nodata
        coords = list(zip(lons.tolist(), lats.tolist()))
        for i, val in enumerate(src.sample(coords)):
            v = float(val[0])
            if nodata is not None and (v == nodata or np.isclose(v, nodata, atol=1e20)):
                continue
            # WorldClim float nodata sometimes appears as very large magnitude
            if abs(v) > 1e20 or np.isnan(v):
                continue
            out[i] = v
    return out


def extract_bioclim_at_points(
    lats: pd.Series | np.ndarray,
    lons: pd.Series | np.ndarray,
    base: Path | None = None,
) -> pd.DataFrame:
    """Sample bio1/bio12/bio15 at lon/lat arrays. Returns DataFrame aligned to input."""
    lat = np.asarray(lats, dtype=float)
    lon = np.asarray(lons, dtype=float)
    paths = worldclim_paths(base)
    if not all(p.exists() for p in paths.values()):
        return pd.DataFrame(
            {
                "bio1": np.full(len(lat), np.nan),
                "bio12": np.full(len(lat), np.nan),
                "bio15": np.full(len(lat), np.nan),
            }
        )
    return pd.DataFrame(
        {
            "bio1": _sample_raster(paths["bio1"], lon, lat),
            "bio12": _sample_raster(paths["bio12"], lon, lat),
            "bio15": _sample_raster(paths["bio15"], lon, lat),
        }
    )


def species_climate_from_occurrences(
    occurrences: pd.DataFrame,
    seed_names: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate WorldClim samples per scientific_name.

    Returns columns used by features/HPI:
      bio1_mean, bio1_std, bio12_mean, bio15_mean,
      climate_stress_raw (0–1 pre-normalized cue),
      climate_method, climate_source
    """
    names = seed_names or sorted(occurrences["scientific_name"].dropna().unique())
    rows: list[dict[str, Any]] = []

    if occurrences.empty or not rasters_available():
        for n in names:
            rows.append(
                {
                    "scientific_name": n,
                    "bio1_mean": np.nan,
                    "bio1_std": np.nan,
                    "bio12_mean": np.nan,
                    "bio15_mean": np.nan,
                    "climate_stress_raw": np.nan,
                    "climate_method": "not_available — run scripts/fetch_climate.py",
                    "climate_source": "none",
                }
            )
        return pd.DataFrame(rows)

    occ = occurrences.dropna(subset=["lat", "lon"]).copy()
    samples = extract_bioclim_at_points(occ["lat"], occ["lon"])
    occ = pd.concat([occ.reset_index(drop=True), samples], axis=1)

    # Regional reference (SEA land cells with valid bio1) ≈ tropical PH core
    # Use median of sampled points as empirical regional MAT reference
    regional_bio1 = float(occ["bio1"].median()) if occ["bio1"].notna().any() else 26.0

    for n in names:
        g = occ.loc[occ["scientific_name"] == n]
        if g.empty or g["bio1"].notna().sum() == 0:
            rows.append(
                {
                    "scientific_name": n,
                    "bio1_mean": np.nan,
                    "bio1_std": np.nan,
                    "bio12_mean": np.nan,
                    "bio15_mean": np.nan,
                    "climate_stress_raw": np.nan,
                    "climate_method": CLIMATE_METHOD,
                    "climate_source": "worldclim_2.1_10m_sea",
                }
            )
            continue
        bio1 = g["bio1"].dropna()
        bio12 = g["bio12"].dropna()
        bio15 = g["bio15"].dropna()
        bio1_mean = float(bio1.mean())
        bio1_std = float(bio1.std()) if len(bio1) > 1 else 0.0
        bio12_mean = float(bio12.mean()) if len(bio12) else np.nan
        bio15_mean = float(bio15.mean()) if len(bio15) else np.nan

        # Per-species raw cues (scaled later across species in HPI):
        # - niche squeeze: low bio1 std → higher stress
        # - seasonality: higher bio15 → higher stress
        # - thermal anomaly: |bio1 - regional| → higher stress
        squeeze = 1.0 / (1.0 + bio1_std)  # (0.2–1]
        season = 0.0 if np.isnan(bio15_mean) else float(np.clip(bio15_mean / 100.0, 0, 1.5))
        thermal = abs(bio1_mean - regional_bio1) / 8.0  # ~8°C span → 1.0
        raw = float(np.clip(0.40 * squeeze + 0.35 * min(season, 1.0) + 0.25 * min(thermal, 1.0), 0, 1))

        rows.append(
            {
                "scientific_name": n,
                "bio1_mean": bio1_mean,
                "bio1_std": bio1_std,
                "bio12_mean": bio12_mean,
                "bio15_mean": bio15_mean,
                "climate_stress_raw": raw,
                "climate_method": CLIMATE_METHOD,
                "climate_source": "worldclim_2.1_10m_sea",
            }
        )
    return pd.DataFrame(rows)


def open_meteo_centroid_summary(lat: float, lon: float) -> dict[str, Any]:
    """Optional online fallback: 1991–2020 climate normals via Open-Meteo.

    Not used in the default offline rebuild; available for interactive upgrades.
    """
    import requests

    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "1991-01-01",
        "end_date": "2020-12-31",
        "models": "EC_Earth3P_HR",
        "daily": "temperature_2m_mean,precipitation_sum",
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    daily = r.json().get("daily", {})
    t = np.asarray(daily.get("temperature_2m_mean") or [], dtype=float)
    p = np.asarray(daily.get("precipitation_sum") or [], dtype=float)
    return {
        "bio1_approx": float(np.nanmean(t)) if len(t) else np.nan,
        "bio12_approx": float(np.nansum(p) / max(len(p) / 365.25, 1)) if len(p) else np.nan,
        "source": "open-meteo_climate_api",
        "note": "Approximate annual means from daily model series; prefer WorldClim rasters",
    }
