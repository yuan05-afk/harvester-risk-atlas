"""Export the v2 build as static JSON for the web app (web/public/data/).

  manifest.json          version, build time, git commit, weights, rules, sources
  species.json           one summary row per cohort species
  species/<slug>.json    profile detail: cells, record history, traits, cleaning
  validation.json        robustness and plausibility checks
  geo/cells.geojson      H3 res-5 cells with effort, PA cover and per-tier species counts
  geo/cells_r4.geojson   the same, aggregated to res-4 parents for the country view
  geo/land.geojson       Philippine land mask
  geo/pa.geojson         WDPCA Philippines, simplified

Only H3 resolution-5 cells (about 250 km²) are published. Record
coordinates never leave the pipeline (Chapman 2020, sensitive species).
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import unicodedata
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_PROCESSED, ROOT
from .index import COMPONENTS, DEFAULT_WEIGHTS, MIN_CELLS, TIER_HIGH, TIER_WATCH, normalize, ranks, score as index_score
from .pipeline import V2_DIR, load_cohort

INDEX_VERSION = "2.0.0"
WEB_DATA = ROOT / "web" / "public" / "data"
PA_SIMPLIFY_DEG = 0.008
CELL_SIMPLIFY_DEG = 0.006
COORD_DP = 3  # ~100 m; ample for 250 km² cells and country-scale outlines


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name.replace("×", "x")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _clean(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else round(o, 4)
    if isinstance(o, (np.floating,)):
        return _clean(float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def _write(path: Path, payload) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_clean(payload), ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _str(v) -> str:
    return "" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


def cell_bounds(cells: list[str]) -> list[float] | None:
    """[west, south, east, north] around a set of H3 cells, for framing a map."""
    import h3

    if not cells:
        return None
    pts = [p for c in cells for p in h3.cell_to_boundary(c)]
    lats, lngs = [p[0] for p in pts], [p[1] for p in pts]
    return [round(min(lngs), 3), round(min(lats), 3), round(max(lngs), 3), round(max(lats), 3)]


def record_history(raw: pd.DataFrame) -> list[dict]:
    """Records per decade split by basis of record (all fetched PH records, pre-cleaning)."""
    r = raw.dropna(subset=["year"]).copy()
    if r.empty:
        return []
    r["decade"] = (pd.to_numeric(r["year"], errors="coerce") // 10 * 10).astype("Int64")
    r = r.dropna(subset=["decade"])
    groups = {
        "HUMAN_OBSERVATION": "observation",
        "PRESERVED_SPECIMEN": "specimen",
        "MATERIAL_CITATION": "literature",
    }
    r["kind"] = r["basis_of_record"].map(groups).fillna("other")
    t = r.groupby(["decade", "kind"]).size().unstack(fill_value=0)
    return [{"decade": int(d), **{k: int(t.loc[d].get(k, 0)) for k in ("observation", "specimen", "literature", "other")}} for d in t.index]


def chosen_photos() -> dict[str, dict]:
    """slug -> photo credit, for the candidate marked ``chosen`` in photos.csv.

    The chosen image is copied (already resized) into web/public/photos/.
    """
    import shutil

    from .sources import photos

    if not photos.CANDIDATES_CSV.exists():
        return {}
    df = pd.read_csv(photos.CANDIDATES_CSV, keep_default_na=False)
    df = df[df["chosen"].astype(str).str.lower() == "true"]
    out = {}
    for r in df.itertuples(index=False):
        src = photos.raw_path(r.slug, int(r.candidate))
        if not src.exists():
            continue
        dest = photos.WEB_DIR / f"{r.slug}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        out[r.slug] = {
            "src": f"photos/{r.slug}.jpg",
            "creator": r.creator,
            "licence": r.licence,
            "page": r.page,
        }
    return out


def build_species(scores: pd.DataFrame) -> tuple[list[dict], dict[str, dict]]:
    import h3

    photos = chosen_photos()

    cohort = load_cohort().set_index("scientific_name")
    base = pd.read_csv(V2_DIR / "species_base.csv", encoding="utf-8").set_index("scientific_name")
    raw = pd.read_parquet(V2_DIR / "records_raw.parquet")
    clean = pd.read_parquet(V2_DIR / "records_clean.parquet")
    traits = pd.read_csv(ROOT / "data" / "curated" / "harvest_traits.csv", encoding="utf-8", keep_default_na=False)
    traits = traits.set_index("scientific_name")

    summaries, details = [], {}
    for s in scores.itertuples(index=False):
        name = s.scientific_name
        c = cohort.loc[name]
        b = base.loc[name]
        slug = slugify(name)
        gate = _str(s.gate)
        summary = {
            "slug": slug,
            "name": name,
            "vernacular": _str(c["vernacular_ph"]),
            "family": _str(c["family"]),
            "ph_status": s.ph_status,
            "endemic": bool(s.ph_endemic),
            "gate": gate,
            "tier": s.tier,
            "partial": bool(s.partial),
            "dao": _str(s.dao_category),
            "iucn": {"status": "not_queried", "category": None},
            "habitat": _str(s.habitat),
            "n_records": int(b["n_gbif_ph"]),
            "n_clean": int(b["n_clean"]),
            "n_cells": int(s.n_cells),
            "components": {k: _num(getattr(s, k)) for k in ("R", "H", "E", "C")},
            "sub": {
                k: _num(getattr(s, k))
                for k in ("r_local", "r_global", "h_part", "h_life_form", "h_sourcing", "e_pa_gap", "e_forest_loss")
            },
            "score": _num(s.score),
            "score_ci": [_num(s.score_p05), _num(s.score_p95)],
            "rank": _num(s.rank_median),
            "rank_ci": [_num(s.rank_p05), _num(s.rank_p95)],
            "p_top": _num(s.p_top_quartile),
            "driver": _str(s.main_driver),
            "climate": {
                "dT": _num(s.dT),
                "dT_range": [_num(s.dT_min), _num(s.dT_max)],
                "exceed": _num(s.C),
                "exceed_range": [_num(s.c_min), _num(s.c_max)],
            },
            "review": {"needed": bool(c["needs_review"]), "note": _str(c["review_note"])},
            "photo": photos.get(slug),
        }
        summaries.append(summary)

        t = traits.loc[name] if name in traits.index else None
        sp_raw = raw[raw["scientific_name"] == name]
        sp_clean = clean[clean["scientific_name"] == name]
        report_cols = [
            "n_fetched",
            "n_kept",
            "missing_coordinates",
            "zero_coordinates",
            "severe_issue",
            "not_wild_basis",
            "cultivated",
            "imprecise",
            "country_centroid",
            "off_land",
            "duplicate",
        ]
        provinces = sp_clean["gadm_level1"].dropna().value_counts()
        cells = json.loads(b["hex_cells"])
        details[slug] = {
            **summary,
            "use_context": _str(c["use_context"]),
            "cells": cells,
            "cells_r4": sorted({h3.cell_to_parent(c, 4) for c in cells}),
            "bounds": cell_bounds(cells),
            "aoo_km2": _num(b["aoo_km2"]),
            "eoo_km2": _num(b["eoo_km2"]),
            "reporting_rate": _num(s.reporting_rate),
            "n_cells_surveyed": int(s.n_cells_surveyed),
            "n_surveyed_ph": int(s.n_surveyed_ph),
            "native_regions": int(s.native_regions),
            "pa_share": _num(s.pa_share),
            "forest_loss_rate": _num(s.forest_loss_rate),
            "provinces": [{"name": p, "records": int(n)} for p, n in provinces.items()],
            "history": record_history(sp_raw),
            "basis": json.loads(b["gbif_basis_counts"]) if isinstance(b["gbif_basis_counts"], str) else {},
            "cleaning": {k: int(b[k]) if k in b and pd.notna(b[k]) else 0 for k in report_cols},
            "traits": None
            if t is None
            else {
                "parts_used": t["parts_used"],
                "part_classes": t["part_classes"].split(";") if t["part_classes"] else [],
                "life_form": t["life_form"],
                "sourcing": t["sourcing"],
                "habitat_note": t["habitat_note"],
                "source": t["source"],
                "source_url": t["source_url"],
                "accessed": t["accessed"],
                "verified": bool(t["verified_by"]),
            },
            "gbif": {
                "taxon_key": _num(b["gbif_taxon_key"]),
                "match_type": _str(b["gbif_match_type"]),
                "fetched_at": _str(b["gbif_fetched_at"]),
                "n_world": int(b["n_gbif_world"]),
            },
            "wcvp": {"key": _num(b["wcvp_key"]), "fetched_at": _str(b["wcvp_fetched_at"])},
        }
    return summaries, details


@lru_cache(maxsize=1)
def _land():
    """Philippine land, lightly buffered so coastal cells keep their shoreline."""
    from shapely.geometry import shape

    gj = json.loads((DATA_PROCESSED / "ph_land_mask.geojson").read_text(encoding="utf-8"))
    return shape(gj["features"][0]["geometry"]).buffer(0.004)


def _round(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], COORD_DP), round(coords[1], COORD_DP)]
    return [_round(c) for c in coords]


def _clipped_cell(cell: str) -> dict | None:
    """The H3 cell cut to the coastline, as GeoJSON; None for cells entirely at sea."""
    from shapely.geometry import mapping

    from .grid import cell_polygon

    geom = cell_polygon(cell).intersection(_land())
    if geom.is_empty or geom.area < 1e-6:
        return None
    # ~600 m tolerance: invisible at atlas scales, and it keeps the files small.
    geom = geom.simplify(CELL_SIMPLIFY_DEG, preserve_topology=True).buffer(0)
    if geom.is_empty:
        return None
    g = mapping(geom)
    if g["type"] == "GeometryCollection":
        polys = [p for p in geom.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        if not polys:
            return None
        from shapely.ops import unary_union

        g = mapping(unary_union(polys))
    return {"type": g["type"], "coordinates": _round(json.loads(json.dumps(g["coordinates"])))}


def build_cells(summaries: list[dict], details: dict[str, dict]) -> dict:
    import h3

    from .sources.effort import cell_effort, ph_land_cells

    pa = dict(pd.read_csv(V2_DIR / "hex_pa.csv").itertuples(index=False, name=None))
    occupied = sorted({c for d in details.values() for c in d["cells"]})
    cells = sorted(set(ph_land_cells()) | set(occupied))
    effort = cell_effort(cells, offline=True)
    by_cell: dict[str, list[dict]] = {c: [] for c in cells}
    for s in summaries:
        for c in details[s["slug"]]["cells"]:
            by_cell[c].append(s)

    features = []
    for c in cells:
        sp = by_cell[c]
        geometry = _clipped_cell(c)
        if geometry is None:
            continue
        features.append(
            {
                "type": "Feature",
                "id": c,
                "geometry": geometry,
                "properties": {
                    "h3": c,
                    "effort": int(effort.get(c, 0)),
                    "pa": round(float(pa[c]), 3) if c in pa else None,
                    "n_high": sum(1 for s in sp if s["tier"] == "High attention"),
                    "n_watch": sum(1 for s in sp if s["tier"] == "Watch"),
                    "n_lower": sum(1 for s in sp if s["tier"] == "Lower"),
                    "n_cohort": len(sp),
                    "species": [s["slug"] for s in sp],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_cells_coarse(cells: dict) -> dict:
    """Parent H3 resolution-4 cells (about 1,770 km²) for the country-scale view.

    Counts are of distinct species across the children, so a species recorded in
    three child cells counts once in their parent.
    """
    import h3

    parents: dict[str, dict] = {}
    for f in cells["features"]:
        p = f["properties"]
        parent = h3.cell_to_parent(p["h3"], 4)
        agg = parents.setdefault(parent, {"effort": 0, "species": set(), "pa": []})
        agg["effort"] += p["effort"]
        agg["species"].update(p["species"])
        if p["pa"] is not None:
            agg["pa"].append(p["pa"])
    return parents


def coarse_features(parents: dict, tier_of: dict[str, str]) -> dict:
    import h3

    features = []
    for c, agg in sorted(parents.items()):
        geometry = _clipped_cell(c)
        if geometry is None:
            continue
        sp = sorted(agg["species"])
        features.append(
            {
                "type": "Feature",
                "id": c,
                "geometry": geometry,
                "properties": {
                    "h3": c,
                    "effort": int(agg["effort"]),
                    "pa": round(float(np.mean(agg["pa"])), 3) if agg["pa"] else None,
                    "n_high": sum(1 for s in sp if tier_of.get(s) == "High attention"),
                    "n_watch": sum(1 for s in sp if tier_of.get(s) == "Watch"),
                    "n_lower": sum(1 for s in sp if tier_of.get(s) == "Lower"),
                    "n_cohort": len(sp),
                    "species": sp,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def hex_points(cells: dict) -> list[list[float]]:
    """[lon, lat, priority] for every res-4 cell with atlas plants: the preloader's bloom."""
    import h3

    out = []
    for f in cells["features"]:
        p = f["properties"]
        if p["n_cohort"] == 0:
            continue
        lat, lng = h3.cell_to_latlng(f["id"])
        out.append([round(lng, 2), round(lat, 2), int(p["n_high"] + p["n_watch"])])
    return out


def build_pa() -> dict:
    from .protected_areas import load_pa_polygons

    pa = load_pa_polygons()
    pa = pa[[c for c in ("name", "desig_eng", "iucn_cat", "status") if c in pa.columns] + ["geometry"]].copy()
    # Only the land part of each area is drawn: marine reserves and the sea
    # inside coastal parks add outlines with nothing on them to read.
    pa["geometry"] = pa.geometry.intersection(_land()).simplify(PA_SIMPLIFY_DEG, preserve_topology=True)
    pa = pa[~pa.geometry.is_empty]
    pa = pa[pa.geometry.to_crs(6933).area > 1e6]  # drop slivers under 1 km²
    pa = pa[pa.geom_type.isin(["Polygon", "MultiPolygon"])]
    gj = json.loads(pa.to_json(drop_id=True))
    for f in gj["features"]:
        f["geometry"]["coordinates"] = _round(f["geometry"]["coordinates"])
    return gj


def build_manifest(summaries: list[dict]) -> dict:
    taxa = pd.read_csv(V2_DIR / "taxa.csv", encoding="utf-8")
    tiers = pd.Series([s["tier"] for s in summaries]).value_counts().to_dict()
    return {
        "index": "Harvest Priority Index",
        "version": INDEX_VERSION,
        "built_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "git_sha": _git_sha(),
        "weights": DEFAULT_WEIGHTS,
        "rules": {
            "tier_high": TIER_HIGH,
            "tier_watch": TIER_WATCH,
            "min_cells": MIN_CELLS,
            "h3_resolution": 5,
            "well_surveyed_records": 100,
            "mc_draws": 2000,
        },
        "counts": {"species": len(summaries), "tiers": tiers},
        "sources": [
            {
                "id": "gbif",
                "name": "GBIF occurrence records",
                "use": "records, counts, survey effort",
                "licence": "Per dataset (CC0 / CC BY / CC BY-NC)",
                "url": "https://www.gbif.org/",
                "accessed": str(taxa["gbif_fetched_at"].dropna().min())[:10],
            },
            {
                "id": "wcvp",
                "name": "World Checklist of Vascular Plants (Govaerts et al. 2021)",
                "use": "native status, native regions",
                "licence": "CC BY 4.0",
                "url": "https://www.gbif.org/dataset/f382f0ce-323a-4091-bb9f-add557f3a9a2",
                "accessed": str(taxa["wcvp_fetched_at"].dropna().min())[:10],
            },
            {
                "id": "wdpca",
                "name": "WDPCA Philippines (UNEP-WCMC, via HDX)",
                "use": "protected-area cover",
                "licence": "Protected Planet terms, non-commercial",
                "url": "https://data.humdata.org/dataset/unep_wdpca_phl",
            },
            {
                "id": "gfw",
                "name": "Tree-cover loss 2001–2023 by province (Hansen et al. 2013; Global Forest Watch)",
                "use": "forest-loss exposure",
                "licence": "CC BY 4.0",
                "url": "https://www.globalforestwatch.org/dashboards/country/PHL/",
            },
            {
                "id": "worldclim",
                "name": "WorldClim 2.1 baseline and CMIP6 2041–2060 (Fick & Hijmans 2017)",
                "use": "climate exposure (reported, weight 0)",
                "licence": "Research and education use",
                "url": "https://www.worldclim.org/",
            },
            {
                "id": "dao",
                "name": "DENR DAO 2026-20, national list of threatened plants",
                "use": "validation only",
                "licence": "Public government document",
                "url": "https://apidb.denr.gov.ph/infores/uploads/DAO-2026-20.pdf",
            },
            {
                "id": "stuart",
                "name": "Stuart GU Jr., Philippine Medicinal Plants (StuartXchange)",
                "use": "curated harvest traits; cohort additions",
                "licence": "Cited per species; text not redistributed",
                "url": "https://www.stuartxchange.org/",
            },
        ],
    }


PARITY_WEIGHT_SETS = {
    "default": dict(DEFAULT_WEIGHTS),
    "with_climate": {"R": 1.0, "H": 1.0, "E": 1.0, "C": 1.0},
    "harm_heavy": {"R": 0.2, "H": 0.6, "E": 0.1, "C": 0.1},
}


def build_parity(summaries: list[dict]) -> dict:
    """Golden file: the pipeline's own ranks for several weight sets, computed
    from the same rounded component values the web app receives, so
    web/src/lib/score.ts can be tested against it exactly."""
    scored = [s for s in summaries if not s["gate"]]
    comps = pd.DataFrame(
        [{k: (np.nan if s["components"][k] is None else s["components"][k]) for k in COMPONENTS} for s in scored]
    )
    sets = []
    for name, raw in PARITY_WEIGHT_SETS.items():
        sc = index_score(comps, raw)
        rk = ranks(sc.to_numpy())
        sets.append(
            {
                "name": name,
                "weights": normalize(raw),
                "ranks": {s["slug"]: _num(r) for s, r in zip(scored, rk)},
            }
        )
    return {
        "note": "Golden ranks from harvester_risk_atlas.index; tested by web/src/lib/score.test.ts",
        "components": {s["slug"]: s["components"] for s in scored},
        "sets": sets,
    }


def run_export() -> dict[str, int]:
    scores = pd.read_csv(V2_DIR / "scores.csv", encoding="utf-8", keep_default_na=False, na_values=[""])
    summaries, details = build_species(scores)
    cells = build_cells(summaries, details)
    coarse = coarse_features(build_cells_coarse(cells), {s["slug"]: s["tier"] for s in summaries})
    sizes = {
        "manifest.json": _write(WEB_DATA / "manifest.json", build_manifest(summaries)),
        "species.json": _write(WEB_DATA / "species.json", summaries),
        "parity.json": _write(WEB_DATA / "parity.json", build_parity(summaries)),
        "validation.json": _write(WEB_DATA / "validation.json", json.loads((V2_DIR / "validation.json").read_text(encoding="utf-8"))),
        "geo/cells.geojson": _write(WEB_DATA / "geo" / "cells.geojson", cells),
        "geo/cells_r4.geojson": _write(
            WEB_DATA / "geo" / "cells_r4.geojson",
            coarse,
        ),
        "geo/hex_points.json": _write(WEB_DATA / "geo" / "hex_points.json", hex_points(coarse)),
        "geo/land.geojson": _write(
            WEB_DATA / "geo" / "land.geojson",
            json.loads((DATA_PROCESSED / "ph_land_mask.geojson").read_text(encoding="utf-8")),
        ),
        "geo/pa.geojson": _write(WEB_DATA / "geo" / "pa.geojson", build_pa()),
    }
    for slug, d in details.items():
        sizes[f"species/{slug}.json"] = _write(WEB_DATA / "species" / f"{slug}.json", d)
    return sizes
