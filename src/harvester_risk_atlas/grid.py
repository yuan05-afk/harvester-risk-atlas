"""Range metrics and the hexagon grid.

AOO and EOO follow the IUCN Red List guidelines (v16, 2024, §4.9–4.10):
  AOO  number of occupied 2 × 2 km cells × 4 km²
  EOO  area of the minimum convex polygon of the records, never below AOO
Both are computed in an equal-area projection (EPSG:6933). They are
*indicative* range metrics from GBIF records, not a Red List assessment.

Hexagons are H3 resolution 5 (mean area about 250 km², edge about 9 km).
They are the unit for cell-based protected-area coverage, the hotspot map,
and the generalised maps of sensitive species.
"""
from __future__ import annotations

import h3
import numpy as np
import pandas as pd
from pyproj import Geod, Transformer
from shapely.geometry import MultiPoint, Polygon

AOO_CELL_KM = 2.0
H3_RES = 5
_TO_EA = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
_FROM_EA = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)
_GEOD = Geod(ellps="WGS84")


def _project(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = _TO_EA.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.asarray(x), np.asarray(y)


def aoo_km2(lat, lon, cell_km: float = AOO_CELL_KM) -> float:
    """Occupied ``cell_km`` cells × cell area. 0 for no records."""
    lat = np.asarray(lat, float)
    if lat.size == 0:
        return 0.0
    x, y = _project(lat, lon)
    size = cell_km * 1000.0
    cells = set(zip(np.floor(x / size).astype(np.int64), np.floor(y / size).astype(np.int64)))
    return len(cells) * cell_km * cell_km


def eoo_km2(lat, lon, aoo: float | None = None) -> float:
    """Convex-hull area in km², raised to AOO when smaller (IUCN guideline).

    Hull vertices are chosen in the equal-area projection. The area is then
    measured geodesically on WGS84, because straight projected edges drift
    from geodesics over hundreds of km and thin hulls magnify that error.
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    floor = 0.0 if aoo is None else float(aoo)
    if lat.size < 3:
        return floor
    x, y = _project(lat, lon)
    hull = MultiPoint(list(zip(x, y))).convex_hull
    if not isinstance(hull, Polygon):
        return floor
    hx, hy = hull.exterior.coords.xy
    vlon, vlat = _FROM_EA.transform(np.asarray(hx), np.asarray(hy))
    area, _ = _GEOD.polygon_area_perimeter(vlon, vlat)
    return max(abs(area) / 1e6, floor)


def h3_cells(lat, lon, res: int = H3_RES) -> list[str]:
    return [h3.latlng_to_cell(float(a), float(b), res) for a, b in zip(lat, lon)]


def cell_polygon(cell: str) -> Polygon:
    """Cell boundary as a lon/lat polygon."""
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(cell)])


def species_range_table(occ: pd.DataFrame) -> pd.DataFrame:
    """Per-species n records, unique sites, AOO, EOO and occupied hex cells."""
    rows = []
    for name, g in occ.groupby("scientific_name", sort=True):
        lat, lon = g["lat"].to_numpy(float), g["lon"].to_numpy(float)
        aoo = aoo_km2(lat, lon)
        cells = sorted(set(h3_cells(lat, lon)))
        rows.append(
            {
                "scientific_name": name,
                "n_clean": int(len(g)),
                "aoo_km2": aoo,
                "eoo_km2": eoo_km2(lat, lon, aoo),
                "n_hex": len(cells),
                "hex_cells": cells,
            }
        )
    return pd.DataFrame(
        rows, columns=["scientific_name", "n_clean", "aoo_km2", "eoo_km2", "n_hex", "hex_cells"]
    )
