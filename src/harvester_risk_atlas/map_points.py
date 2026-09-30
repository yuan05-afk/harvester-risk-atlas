"""Map coordinates that sit on Philippines land.

GBIF sample averages often fall in the channels between islands (especially
the Visayas). HPI still uses those averages. The map does not: a circle is
drawn at the average only when that point is on land inside the Philippines,
otherwise at the nearest sample point that is.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

from .config import DATA_PROCESSED, PH_BBOX

PH_LAND_MASK = DATA_PROCESSED / "ph_land_mask.geojson"
# Coastal GBIF points can sit just off a simplified coastline. Accept them
# as land records; do not treat a channel centroid the same way.
COAST_BUFFER_DEG = 0.02
# Smaller islets read as open water at a Philippines-wide zoom.
MAJOR_ISLAND_MIN_DEG2 = 0.15
# Country view: Philippines land, with a margin so islands are not clipped.
PH_FIT_BOUNDS = ((4.15, 116.45), (21.05, 127.2))
# Regional view around one hotspot. Wide enough to read the island, not a dot.
HOTSPOT_PAD_DEG = 1.35


def marker_radius(hpi: float) -> float:
    """Pixel radius. Readable at a Philippines-wide zoom, still quiet."""
    try:
        score = float(hpi)
    except (TypeError, ValueError):
        score = 0.0
    if score != score:  # NaN
        score = 0.0
    score = min(1.0, max(0.0, score))
    return 12.0 + 6.0 * score


@lru_cache(maxsize=1)
def _land_geometry():
    data = json.loads(PH_LAND_MASK.read_text(encoding="utf-8"))
    geom = shape(data["features"][0]["geometry"])
    return geom, prep(geom)


def _point(lat: float, lon: float) -> Point | None:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if lat_f != lat_f or lon_f != lon_f:
        return None
    return Point(lon_f, lat_f)


def on_ph_land(lat: float, lon: float) -> bool:
    """True when the point lies on the Philippines land mask."""
    point = _point(lat, lon)
    if point is None:
        return False
    _geom, prepared = _land_geometry()
    return bool(prepared.covers(point))


@lru_cache(maxsize=1)
def _major_land():
    geom, _prepared = _land_geometry()
    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    major = unary_union([g for g in parts if g.area >= MAJOR_ISLAND_MIN_DEG2])
    return major, prep(major)


def on_major_ph_land(lat: float, lon: float) -> bool:
    """True on a large Philippines island (Luzon, Visayas mains, Mindanao, Palawan)."""
    point = _point(lat, lon)
    if point is None:
        return False
    _major, prepared = _major_land()
    return bool(prepared.covers(point))


def _in_ph_bbox(lat: float, lon: float) -> bool:
    return (
        PH_BBOX["min_lat"] <= lat <= PH_BBOX["max_lat"]
        and PH_BBOX["min_lon"] <= lon <= PH_BBOX["max_lon"]
    )


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    mid = np.deg2rad((lat1 + lat2) / 2.0)
    return float(
        np.hypot((lat1 - lat2) * 111.32, (lon1 - lon2) * 111.32 * np.cos(mid))
    )


def _finite_pair(lat, lon) -> tuple[float, float] | None:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if lat_f != lat_f or lon_f != lon_f:
        return None
    return lat_f, lon_f


def _nearest(origin: tuple[float, float], points: list[tuple[float, float]]) -> tuple[float, float]:
    lat0, lon0 = origin
    return min(points, key=lambda p: (_km(lat0, lon0, p[0], p[1]), p[0], p[1]))


def choose_plot_point(
    lat_mean,
    lon_mean,
    occurrences: list[tuple[float, float]],
    *,
    on_land,
    near_land,
) -> tuple[float, float, str] | None:
    """Return (lat, lon, source) or None when nothing plottable is in the Philippines.

    source is ``centroid`` or ``land_record``.
    ``on_land`` / ``near_land`` take (lat, lon). ``near_land`` includes a short coast buffer.
    """
    strict: list[tuple[float, float]] = []
    coastal: list[tuple[float, float]] = []
    for lat, lon in occurrences:
        pair = _finite_pair(lat, lon)
        if pair is None or not _in_ph_bbox(*pair):
            continue
        if on_land(*pair):
            strict.append(pair)
        elif near_land(*pair):
            coastal.append(pair)
    pool = strict or coastal

    mean = _finite_pair(lat_mean, lon_mean)
    if mean is not None and _in_ph_bbox(*mean) and on_land(*mean):
        return mean[0], mean[1], "centroid"
    if not pool:
        return None
    origin = mean if mean is not None else (
        float(np.median([p[0] for p in pool])),
        float(np.median([p[1] for p in pool])),
    )
    lat, lon = _nearest(origin, pool)
    return lat, lon, "land_record"


def species_plot_points(hpi: pd.DataFrame, occ: pd.DataFrame) -> pd.DataFrame:
    """Species that can be drawn on Philippines land.

    Columns: scientific_name, plot_lat, plot_lon, plot_source.
    """
    geom, prepared = _land_geometry()
    _major, major_prep = _major_land()

    def on_land(lat: float, lon: float) -> bool:
        # Prefer a large island so the circle is not a speck in a channel.
        return bool(major_prep.covers(Point(lon, lat)))

    def near_land(lat: float, lon: float) -> bool:
        point = Point(lon, lat)
        if prepared.covers(point):
            return True
        return geom.distance(point) <= COAST_BUFFER_DEG

    by_name: dict[str, list[tuple[float, float]]] = {}
    if occ is not None and not occ.empty and {"scientific_name", "lat", "lon"} <= set(occ.columns):
        use = occ.dropna(subset=["lat", "lon"])
        for name, lat, lon in zip(use["scientific_name"], use["lat"], use["lon"]):
            pair = _finite_pair(lat, lon)
            if pair is None:
                continue
            by_name.setdefault(str(name), []).append(pair)

    rows: list[dict] = []
    if hpi is None or hpi.empty or "scientific_name" not in hpi.columns:
        return pd.DataFrame(columns=["scientific_name", "plot_lat", "plot_lon", "plot_source"])

    has_lat = "lat_mean" in hpi.columns
    has_lon = "lon_mean" in hpi.columns
    for rec in hpi.itertuples(index=False):
        name = getattr(rec, "scientific_name", None)
        if name is None or (isinstance(name, float) and name != name):
            continue
        name = str(name)
        lat_mean = getattr(rec, "lat_mean", None) if has_lat else None
        lon_mean = getattr(rec, "lon_mean", None) if has_lon else None
        chosen = choose_plot_point(
            lat_mean,
            lon_mean,
            by_name.get(name, []),
            on_land=on_land,
            near_land=near_land,
        )
        if chosen is None:
            continue
        lat, lon, source = chosen
        rows.append(
            {
                "scientific_name": name,
                "plot_lat": lat,
                "plot_lon": lon,
                "plot_source": source,
            }
        )
    return pd.DataFrame(rows, columns=["scientific_name", "plot_lat", "plot_lon", "plot_source"])


# Demo extract has no centroid. An imputed score must not become the map focus.
NEVER_FOCUS = frozenset({"Mentha × piperita"})


def hotspot_name(
    plotted: pd.DataFrame,
    scores: pd.DataFrame,
    selected: str | None,
) -> str | None:
    """Selected species when it has a land point; otherwise the highest HPI that does.

    Mentha × piperita never wins, even if a coordinate is passed in.
    """
    if plotted is None or plotted.empty:
        return None
    names = set(plotted["scientific_name"].astype(str)) - NEVER_FOCUS
    if selected and str(selected) in names:
        return str(selected)
    if scores is None or scores.empty or "hpi" not in scores.columns:
        return None
    scored = scores[scores["scientific_name"].astype(str).isin(names)].dropna(subset=["hpi"])
    if scored.empty:
        return None
    return str(scored.loc[scored["hpi"].idxmax(), "scientific_name"])
