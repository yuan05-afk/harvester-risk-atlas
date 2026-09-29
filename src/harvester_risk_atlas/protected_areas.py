"""Protected-area overlap / distance for occurrence points.

Primary source (hackathon research): UNEP-WCMC WDPCA Philippines subset via
HDX (Protected and Conserved Areas). License: UNEP-WCMC / Protected Planet
terms — non-commercial research & education; cite Protected Planet / WDPA.
Do NOT treat as a substitute for official DENR GIS for permitting.

Secondary (optional): OSM boundary=protected_area / leisure=nature_reserve
centers for PH bbox (ODbL). Natural Earth parks are US-focused and are NOT
used for PH gap scoring (kept only as a documented non-fit).

Pipeline writes a cleaned GeoPackage under data/processed/ for offline reuse.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import DATA_PROCESSED, DATA_RAW, PA_PROCESSED_GPKG

PA_SOURCE_LABEL = (
    "WDPCA Philippines polygons (UNEP-WCMC via HDX); "
    "license: Protected Planet / WDPA terms — research/education citation required"
)
PA_METHOD = (
    "Point-in-polygon overlap + geodesic-approx distance (degrees→km at lat) "
    "to nearest WDPCA polygon; species frac_in_protected & mean_dist_to_pa_km"
)


def default_raw_gpkg() -> Path:
    return DATA_RAW / "protected_areas" / "wdpca_phl.gpkg"


def load_pa_polygons(path: Path | None = None) -> "gpd.GeoDataFrame":
    import geopandas as gpd
    from shapely.validation import make_valid

    src = path or PA_PROCESSED_GPKG
    if not src.exists():
        src = default_raw_gpkg()
    if not src.exists():
        raise FileNotFoundError(
            f"No PA layer at {PA_PROCESSED_GPKG} or {default_raw_gpkg()}. "
            "Run scripts/fetch_protected_areas.py"
        )
    # Prefer processed single-layer gpkg; raw has points+polygons
    try:
        layers = None
        try:
            import pyogrio

            layers = [r[0] for r in pyogrio.list_layers(src)]
        except Exception:
            layers = None
        if layers and "polygons" in layers:
            gdf = gpd.read_file(src, layer="polygons")
        elif layers and "pa_polygons" in layers:
            gdf = gpd.read_file(src, layer="pa_polygons")
        else:
            gdf = gpd.read_file(src)
    except Exception:
        gdf = gpd.read_file(src)

    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    elif str(gdf.crs).upper() not in ("EPSG:4326", "WGS84"):
        gdf = gdf.to_crs(4326)

    gdf = gdf[~gdf.geometry.isna()].copy()
    gdf["geometry"] = gdf.geometry.apply(
        lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
    )
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    # Keep polygonal only
    gdf = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    return gdf.reset_index(drop=True)


def prepare_processed_pa(raw: Path | None = None, out: Path | None = None) -> Path:
    """Normalize WDPCA polygons → data/processed/pa_wdpca_phl.gpkg (EPSG:4326)."""
    import geopandas as gpd

    raw = raw or default_raw_gpkg()
    out = out or PA_PROCESSED_GPKG
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf = load_pa_polygons(raw)
    keep = [c for c in ("name", "name_eng", "desig_eng", "iucn_cat", "rep_area", "status", "iso3") if c in gdf.columns]
    slim = gdf[keep + ["geometry"]].copy() if keep else gdf.copy()
    slim.to_file(out, layer="pa_polygons", driver="GPKG")
    return out


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def annotate_occurrences(
    occurrences: pd.DataFrame,
    pa: "gpd.GeoDataFrame | None" = None,
) -> pd.DataFrame:
    """Add in_pa (bool) and dist_to_pa_km to occurrence rows."""
    import geopandas as gpd
    from shapely.ops import nearest_points

    occ = occurrences.copy()
    if occ.empty or "lat" not in occ.columns:
        occ["in_pa"] = False
        occ["dist_to_pa_km"] = np.nan
        return occ

    try:
        pa = pa if pa is not None else load_pa_polygons()
    except FileNotFoundError:
        occ["in_pa"] = False
        occ["dist_to_pa_km"] = np.nan
        return occ

    pts = gpd.GeoDataFrame(
        occ,
        geometry=gpd.points_from_xy(occ["lon"], occ["lat"]),
        crs=4326,
    )
    # Spatial index join for containment
    joined = gpd.sjoin(pts, pa[["geometry"]], how="left", predicate="within")
    # If a point hits multiple PAs, keep first
    in_pa_idx = joined.index.duplicated(keep="first")
    joined = joined.loc[~in_pa_idx]
    occ["in_pa"] = joined["index_right"].notna().reindex(occ.index).fillna(False).astype(bool)

    # Distance for points outside PA (and 0 inside)
    # Use unary union for nearest — OK for ~300 PH polygons
    try:
        union = pa.geometry.union_all()
    except AttributeError:
        union = pa.unary_union
    dists = []
    for i, row in pts.iterrows():
        if bool(occ.at[i, "in_pa"]):
            dists.append(0.0)
            continue
        geom = row.geometry
        if geom is None or union is None:
            dists.append(np.nan)
            continue
        nearest = nearest_points(geom, union)[1]
        dists.append(
            float(_haversine_km(geom.y, geom.x, nearest.y, nearest.x))
        )
    occ["dist_to_pa_km"] = dists
    return occ


def species_pa_metrics(
    occurrences: pd.DataFrame,
    seed_names: list[str] | None = None,
) -> pd.DataFrame:
    """Per-species protected-area overlap & gap metrics."""
    names = seed_names or sorted(occurrences["scientific_name"].dropna().unique())
    try:
        pa = load_pa_polygons()
        annotated = annotate_occurrences(occurrences, pa)
        source = PA_SOURCE_LABEL
        method = PA_METHOD
        available = True
    except FileNotFoundError:
        annotated = occurrences.copy()
        annotated["in_pa"] = False
        annotated["dist_to_pa_km"] = np.nan
        source = "not_available — run scripts/fetch_protected_areas.py"
        method = "none"
        available = False

    rows: list[dict[str, Any]] = []
    for n in names:
        g = annotated.loc[annotated["scientific_name"] == n] if not annotated.empty else pd.DataFrame()
        if g.empty or not available or "lat" not in g.columns or g["lat"].isna().all():
            rows.append(
                {
                    "scientific_name": n,
                    "frac_in_protected": np.nan,
                    "mean_dist_to_pa_km": np.nan,
                    "n_in_pa": 0,
                    "pa_source": source,
                    "pa_method": method,
                }
            )
            continue
        g_geo = g.dropna(subset=["lat", "lon"])
        frac = float(g_geo["in_pa"].mean()) if len(g_geo) else np.nan
        dist = float(g_geo["dist_to_pa_km"].mean()) if g_geo["dist_to_pa_km"].notna().any() else np.nan
        rows.append(
            {
                "scientific_name": n,
                "frac_in_protected": frac,
                "mean_dist_to_pa_km": dist,
                "n_in_pa": int(g_geo["in_pa"].sum()),
                "pa_source": source,
                "pa_method": method,
            }
        )
    return pd.DataFrame(rows)
