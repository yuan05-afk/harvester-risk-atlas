"""Survey effort: GBIF vascular-plant records per H3 cell across the Philippines.

Raw record counts mix rarity with attention: a roadside weed collects more
iNaturalist records than a forest liana. The effort layer is the
target-group count (all Tracheophyta) per cell. It lets rarity be measured as
a reporting rate, the share of well-surveyed cells where a species was
recorded, rather than as a raw count.
"""
from __future__ import annotations

import json
import time

import h3

from ..config import DATA_RAW, DATA_PROCESSED
from ..grid import H3_RES
from .http import get_json, read_cache, utc_now, write_cache

API = "https://api.gbif.org/v1"
TRACHEOPHYTA_KEY = 7707728
CACHE = DATA_RAW / "effort" / f"tracheophyta_ph_h3r{H3_RES}.json.gz"
LAND_MASK = DATA_PROCESSED / "ph_land_mask.geojson"


def ph_land_cells(res: int = H3_RES) -> list[str]:
    """H3 cells whose centre lies on the Philippine land mask."""
    gj = json.loads(LAND_MASK.read_text(encoding="utf-8"))
    geom = gj["features"][0]["geometry"]
    return sorted(h3.geo_to_cells(geom, res))


def _wkt(cell: str) -> str:
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell)]
    # GBIF expects counter-clockwise exterior rings.
    area2 = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]))
    if area2 < 0:
        ring.reverse()
    ring.append(ring[0])
    return "POLYGON((" + ",".join(f"{x:.5f} {y:.5f}" for x, y in ring) + "))"


def cell_effort(cells: list[str], *, offline: bool = False) -> dict[str, int]:
    """Tracheophyta record count per cell. Cached; only missing cells are fetched."""
    cached = read_cache(CACHE) or {"counts": {}, "fetched_at": None}
    counts: dict[str, int] = cached["counts"]
    missing = [c for c in sorted(set(cells)) if c not in counts]
    if missing and offline:
        raise FileNotFoundError(f"{len(missing)} effort cells not cached")
    for i, cell in enumerate(missing):
        page = get_json(
            f"{API}/occurrence/search",
            {
                "taxonKey": TRACHEOPHYTA_KEY,
                "country": "PH",
                "hasCoordinate": "true",
                "hasGeospatialIssue": "false",
                "occurrenceStatus": "PRESENT",
                "geometry": _wkt(cell),
                "limit": 0,
            },
        )
        counts[cell] = int(page.get("count", 0))
        if (i + 1) % 100 == 0:
            write_cache(CACHE, {"counts": counts, "fetched_at": utc_now()})
        time.sleep(0.1)
    if missing:
        write_cache(CACHE, {"counts": counts, "fetched_at": utc_now()})
    return {c: counts[c] for c in cells}
