#!/usr/bin/env python3
"""Download WorldClim 2.1 10′ bioclim and clip bio1/bio12/bio15 to SEA bbox.

Source: https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip
(~50 MB). Clipped GeoTIFFs land in data/processed/worldclim_sea/ (~300 KB).

License: WorldClim 2.1 free for non-commercial / research — cite Fick & Hijmans 2017.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import requests

from harvester_risk_atlas.config import DATA_PROCESSED, DATA_RAW, SEA_BBOX, WORLDCLIM_SEA_DIR

WC_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip"
WANT = {1: "bio1", 12: "bio12", 15: "bio15"}


def main() -> None:
    import rasterio
    from rasterio.windows import from_bounds

    raw_dir = DATA_RAW / "worldclim"
    raw_dir.mkdir(parents=True, exist_ok=True)
    WORLDCLIM_SEA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = raw_dir / "wc2.1_10m_bio.zip"

    if not zip_path.exists():
        print(f"Downloading {WC_URL} …")
        with requests.get(WC_URL, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
        print(f"Saved {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")
    else:
        print(f"Using existing {zip_path}")

    minx, miny = SEA_BBOX["min_lon"], SEA_BBOX["min_lat"]
    maxx, maxy = SEA_BBOX["max_lon"], SEA_BBOX["max_lat"]

    with zipfile.ZipFile(zip_path) as z:
        for bio_num, label in WANT.items():
            member = f"wc2.1_10m_bio_{bio_num}.tif"
            tmp = raw_dir / member
            if not tmp.exists():
                z.extract(member, raw_dir)
            with rasterio.open(tmp) as src:
                window = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
                window = window.round_offsets().round_lengths()
                data = src.read(1, window=window)
                transform = src.window_transform(window)
                profile = src.profile.copy()
                profile.update(
                    height=data.shape[0],
                    width=data.shape[1],
                    transform=transform,
                    compress="lzw",
                )
                out = WORLDCLIM_SEA_DIR / f"wc2.1_10m_{label}_sea.tif"
                with rasterio.open(out, "w", **profile) as dst:
                    dst.write(data, 1)
                print(f"  {label} → {out} shape={data.shape}")
            tmp.unlink(missing_ok=True)

    total = sum(p.stat().st_size for p in WORLDCLIM_SEA_DIR.glob("*.tif"))
    print(f"Clipped SEA bioclim ready ({total / 1e3:.0f} KB) in {WORLDCLIM_SEA_DIR}")
    print("Next: python scripts/build_features.py && python scripts/compute_hpi.py")


if __name__ == "__main__":
    main()
