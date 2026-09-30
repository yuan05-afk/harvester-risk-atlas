"""Map coordinates at the true species mean.

GBIF sample averages often fall in the channels between islands (especially
the Visayas) or west of the Philippines. HPI uses those averages. The map
does too: a circle is drawn at the sample average already on the row.
Coordinates are never taken from a nearby land record.
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

from .config import DATA_PROCESSED

PH_LAND_MASK = DATA_PROCESSED / "ph_land_mask.geojson"
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
    """True when the point lies on the Philippines land mask.

    Used to describe a circle. Never used to move one.
    """
    point = _point(lat, lon)
    if point is None:
        return False
    _geom, prepared = _land_geometry()
    return bool(prepared.covers(point))


def _finite_pair(lat, lon) -> tuple[float, float] | None:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if lat_f != lat_f or lon_f != lon_f:
        return None
    return lat_f, lon_f


def choose_plot_point(lat_mean, lon_mean) -> tuple[float, float, str] | None:
    """Return ``(lat, lon, "centroid")`` for a real average, else None.

    The average is returned even when it falls in the sea or west of the
    Philippines. A nearby land record is not a substitute.
    """
    mean = _finite_pair(lat_mean, lon_mean)
    if mean is None:
        return None
    return mean[0], mean[1], "centroid"


def species_plot_points(hpi: pd.DataFrame, occurrences: pd.DataFrame | None = None) -> pd.DataFrame:
    """Species drawn at their true sample average.

    Columns: scientific_name, plot_lat, plot_lon, plot_source.
    ``plot_source`` is ``centroid``. ``occurrences`` is not a placement
    source — individual records must not pull the circle onto land.
    Rows with no lat/lon (Mentha × piperita in the demo extract) are omitted.
    """
    del occurrences
    columns = ["scientific_name", "plot_lat", "plot_lon", "plot_source"]
    if hpi is None or hpi.empty or "scientific_name" not in hpi.columns:
        return pd.DataFrame(columns=columns)

    has_lat = "lat_mean" in hpi.columns
    has_lon = "lon_mean" in hpi.columns
    rows: list[dict] = []
    for rec in hpi.itertuples(index=False):
        name = getattr(rec, "scientific_name", None)
        if name is None or (isinstance(name, float) and name != name):
            continue
        lat_mean = getattr(rec, "lat_mean", None) if has_lat else None
        lon_mean = getattr(rec, "lon_mean", None) if has_lon else None
        chosen = choose_plot_point(lat_mean, lon_mean)
        if chosen is None:
            continue
        lat, lon, source = chosen
        rows.append(
            {
                "scientific_name": str(name),
                "plot_lat": lat,
                "plot_lon": lon,
                "plot_source": source,
            }
        )
    return pd.DataFrame(rows, columns=columns)


# Demo extract has no centroid. An imputed score must not become the map focus.
NEVER_FOCUS = frozenset({"Mentha × piperita"})


def hotspot_name(
    plotted: pd.DataFrame,
    scores: pd.DataFrame,
    selected: str | None,
) -> str | None:
    """Selected species when it is plotted; otherwise the highest HPI that is.

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
