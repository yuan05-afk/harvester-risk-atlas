"""WorldClim 2.1 CMIP6 projections (2041–2060), clipped to the Philippines.

Five GCMs span the CMIP6 range of climate sensitivity, from MIROC6 and
MPI-ESM1-2-HR (lower) to UKESM1-0-LL (high). Two scenarios: SSP2-4.5 is
the primary one; SSP5-8.5 is shown as a high-emissions check.

Only bio1 (mean annual temperature, °C) and bio12 (annual precipitation, mm)
are kept. The global 10′ files (~35 MB each) are cached under data/raw/cmip6/
and are not committed; the PH clips (~tens of KB) are.

Cite: Fick & Hijmans (2017); WorldClim 2.1 CMIP6 downscaled data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import DATA_PROCESSED, DATA_RAW, WORLDCLIM_SEA_DIR
from .http import session

GCMS = ("MIROC6", "MPI-ESM1-2-HR", "EC-Earth3-Veg", "IPSL-CM6A-LR", "UKESM1-0-LL")
SSPS = ("ssp245", "ssp585")
PERIOD = "2041-2060"
URL = "https://geodata.ucdavis.edu/cmip6/10m/{gcm}/{ssp}/wc2.1_10m_bioc_{gcm}_{ssp}_{period}.tif"
RAW_DIR = DATA_RAW / "cmip6"
PH_DIR = DATA_PROCESSED / "cmip6_ph"
# Philippines with a margin (lon 115.5–127.5, lat 3.5–21.5).
PH_WINDOW = (115.5, 3.5, 127.5, 21.5)
BANDS = {"bio1": 1, "bio12": 12}


def clip_path(gcm: str, ssp: str) -> Path:
    return PH_DIR / f"{gcm}_{ssp}_{PERIOD}_bio1_bio12.tif"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with session().get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    tmp.replace(dest)


def _clip(src_path: Path, dest: Path) -> None:
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(src_path) as src:
        win = from_bounds(*PH_WINDOW, transform=src.transform).round_offsets().round_lengths()
        data = src.read([BANDS["bio1"], BANDS["bio12"]], window=win)
        profile = src.profile.copy()
        profile.update(
            count=2,
            height=data.shape[1],
            width=data.shape[2],
            transform=src.window_transform(win),
            compress="deflate",
            predictor=3 if data.dtype.kind == "f" else 2,
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dest, "w", **profile) as out:
        out.write(data)
        out.set_band_description(1, "bio1")
        out.set_band_description(2, "bio12")


def ensure_clips(offline: bool = False) -> list[Path]:
    """Download (once) and clip every GCM × SSP. Returns the clip paths."""
    paths = []
    for gcm in GCMS:
        for ssp in SSPS:
            dest = clip_path(gcm, ssp)
            if not dest.exists():
                if offline:
                    raise FileNotFoundError(dest)
                raw = RAW_DIR / f"wc2.1_10m_bioc_{gcm}_{ssp}_{PERIOD}.tif"
                if not raw.exists():
                    _download(URL.format(gcm=gcm, ssp=ssp, period=PERIOD), raw)
                _clip(raw, dest)
            paths.append(dest)
    return paths


def _sample(path: Path, band: int, lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as src:
        vals = np.array([v[band - 1] for v in src.sample(zip(lons, lats))], dtype=float)
        nodata = src.nodata
    if nodata is not None:
        vals[np.isclose(vals, nodata)] = np.nan
    vals[np.abs(vals) > 1e20] = np.nan
    return vals


def sample_current(lats, lons) -> dict[str, np.ndarray]:
    """WorldClim 2.1 1970–2000 baseline at the same 10′ resolution."""
    lats, lons = np.asarray(lats, float), np.asarray(lons, float)
    return {
        "bio1": _sample(WORLDCLIM_SEA_DIR / "wc2.1_10m_bio1_sea.tif", 1, lons, lats),
        "bio12": _sample(WORLDCLIM_SEA_DIR / "wc2.1_10m_bio12_sea.tif", 1, lons, lats),
    }


def sample_future(lats, lons, gcm: str, ssp: str) -> dict[str, np.ndarray]:
    lats, lons = np.asarray(lats, float), np.asarray(lons, float)
    path = clip_path(gcm, ssp)
    return {"bio1": _sample(path, 1, lons, lats), "bio12": _sample(path, 2, lons, lats)}
