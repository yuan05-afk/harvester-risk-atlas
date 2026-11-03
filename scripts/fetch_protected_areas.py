#!/usr/bin/env python3
"""Fetch Philippines protected-area polygons (WDPCA via HDX) and normalize.

Primary: UNEP-WCMC Protected & Conserved Areas (WDPCA) Philippines geopackage
  https://data.humdata.org/dataset/unep_wdpca_phl
License: Protected Planet / WDPA terms — non-commercial research & education;
  cite Protected Planet / UNEP-WCMC. Not a DENR permitting layer.

Also caches OSM protected_area centers (ODbL) as optional secondary reference.
Natural Earth parks are US-centric and are NOT used for PH HPI scoring.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import requests

from harvester_risk_atlas.config import DATA_RAW, PA_PROCESSED_GPKG
from harvester_risk_atlas.protected_areas import prepare_processed_pa

HDX_GPKG = (
    "https://data.humdata.org/dataset/275821e7-e3ae-471b-8625-f3eb8811d7d2/"
    "resource/dc05b146-eded-4ad8-b726-0e9c9ca22637/download/"
    "protected_conserved_areas_wdpca.gpkg"
)
OVERPASS_URLS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
OVERPASS_QUERY = """[out:json][timeout:90];
(relation["boundary"="protected_area"](4.0,116.0,21.5,127.5);
 way["boundary"="protected_area"](4.0,116.0,21.5,127.5);
 relation["leisure"="nature_reserve"](4.0,116.0,21.5,127.5);
 way["leisure"="nature_reserve"](4.0,116.0,21.5,127.5););
out tags center;"""


def main() -> None:
    pa_dir = DATA_RAW / "protected_areas"
    pa_dir.mkdir(parents=True, exist_ok=True)
    raw_gpkg = pa_dir / "wdpca_phl.gpkg"

    if not raw_gpkg.exists() or raw_gpkg.stat().st_size < 1000:
        print(f"Downloading WDPCA PH geopackage…")
        with requests.get(HDX_GPKG, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(raw_gpkg, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
        print(f"  → {raw_gpkg} ({raw_gpkg.stat().st_size / 1e6:.1f} MB)")
    else:
        print(f"Using existing {raw_gpkg}")

    out = prepare_processed_pa(raw_gpkg, PA_PROCESSED_GPKG)
    print(f"Normalized PA polygons → {out}")

    # Optional OSM cache (centers only) for documentation / QA
    osm_path = pa_dir / "osm_ph_pa.json"
    if not osm_path.exists():
        for url in OVERPASS_URLS:
            try:
                print(f"Trying OSM Overpass {url} …")
                r = requests.get(url, params={"data": OVERPASS_QUERY}, timeout=120)
                r.raise_for_status()
                osm_path.write_bytes(r.content)
                print(f"  OSM PA centers → {osm_path} ({osm_path.stat().st_size / 1e3:.0f} KB)")
                break
            except Exception as e:
                print(f"  failed: {e}")
        else:
            print("OSM Overpass unavailable — WDPCA alone is sufficient for HPI.")

    print("Next: python scripts/build_features.py && python scripts/compute_hpi.py")


if __name__ == "__main__":
    main()
