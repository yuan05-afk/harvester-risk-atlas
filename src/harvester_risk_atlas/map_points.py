"""Map coordinates at the true species mean.

GBIF sample averages often fall in the channels between islands (especially
the Visayas) or west of the Philippines. HPI uses those averages. The map
does too: a circle is drawn at the sample average already on the row.
Coordinates are never taken from a nearby land record.
"""
from __future__ import annotations

import json
import re
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
    return 12.0 + 6.0 * _unit_score(hpi)


# Same three risk inks as the bands. The ramp is continuous so a 0.40 and a
# 0.55 do not share one flat color. It is painted only on real centroids.
_RAMP_LOW = (0x40, 0x91, 0x6C)
_RAMP_MID = (0xB0, 0x89, 0x68)
_RAMP_HIGH = (0x9B, 0x22, 0x26)


def _unit_score(hpi: float) -> float:
    try:
        score = float(hpi)
    except (TypeError, ValueError):
        return 0.0
    if score != score:  # NaN
        return 0.0
    return min(1.0, max(0.0, score))


def _lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hpi_marker_color(hpi: float) -> str:
    """Calm HPI color for one centroid. Not a surface between points."""
    score = _unit_score(hpi)
    if score <= 0.5:
        rgb = _lerp_rgb(_RAMP_LOW, _RAMP_MID, score / 0.5)
    else:
        rgb = _lerp_rgb(_RAMP_MID, _RAMP_HIGH, (score - 0.5) / 0.5)
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# Clicks land on the marker coordinate. This only rejects a miss on open water.
CLICK_MATCH_DEG = 0.35


def species_at_click(
    plotted: pd.DataFrame,
    lat,
    lon,
    tooltip: str | None = None,
) -> str | None:
    """Species whose circle was clicked, or None if the click missed.

    Tooltip wins (``Name · score``). Otherwise the nearest plotted centroid
    within ``CLICK_MATCH_DEG``. Mentha × piperita never matches.
    """
    if plotted is None or plotted.empty or "scientific_name" not in plotted.columns:
        return None
    names = set(plotted["scientific_name"].astype(str)) - NEVER_FOCUS
    frame = plotted[plotted["scientific_name"].astype(str).isin(names)]
    if frame.empty:
        return None
    if tooltip:
        # Leaflet wraps the tip in a div. The name is the text before the score.
        text = re.sub(r"<[^>]+>", " ", str(tooltip))
        text = " ".join(text.split())
        head = text.split(" · ")[0].strip()
        if head in names:
            return head
    pair = _finite_pair(lat, lon)
    if pair is None:
        return None
    lat_f, lon_f = pair
    best_name = None
    best_d = CLICK_MATCH_DEG * CLICK_MATCH_DEG
    for rec in frame.itertuples(index=False):
        dlat = float(rec.plot_lat) - lat_f
        dlon = float(rec.plot_lon) - lon_f
        dist = dlat * dlat + dlon * dlon
        if dist <= best_d:
            best_d = dist
            best_name = str(rec.scientific_name)
    return best_name


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
