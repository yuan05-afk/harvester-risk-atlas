"""v2 build stages. Each stage reads the previous stage's files under data/processed/v2/.

  fetch     GBIF records + exact counts, WCVP nativity (network; cached under data/raw/)
  base      cleaning, range metrics, hex cells, protected-area coverage
  index     components, gates, Monte Carlo ranks, priority tiers
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .clean import clean_occurrences
from .config import DATA_PROCESSED, ROOT
from .grid import species_range_table
from .protected_areas import hex_protected_fraction
from .sources import gbif, wcvp

V2_DIR = DATA_PROCESSED / "v2"
COHORT_CSV = ROOT / "data" / "curated" / "cohort.csv"


def load_cohort() -> pd.DataFrame:
    cohort = pd.read_csv(COHORT_CSV, encoding="utf-8", keep_default_na=False)
    cohort["needs_review"] = cohort["needs_review"].astype(str).str.lower() == "true"
    return cohort


def stage_fetch(offline: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Raw PH records for the cohort, plus one row of taxonomy and counts per species."""
    cohort = load_cohort()
    frames, rows = [], []
    for c in cohort.itertuples(index=False):
        payload = gbif.fetch_species(c.query_name, offline=offline)
        native = wcvp.nativity(c.query_name, offline=offline)
        counts = payload["counts"] or {}
        frames.append(gbif.records_frame(c.scientific_name, payload))
        bor = counts.get("basis_of_record", {})
        rows.append(
            {
                "scientific_name": c.scientific_name,
                **{k: v for k, v in payload["match"].items() if k != "fetched_at"},
                "n_gbif_ph": counts.get("n_country", 0),
                "n_gbif_ph_georef": counts.get("n_country_georeferenced", 0),
                "n_gbif_world": counts.get("n_world", 0),
                "gbif_basis_counts": json.dumps(bor, sort_keys=True),
                "gbif_year_counts": json.dumps(counts.get("year", {}), sort_keys=True),
                "gbif_capped": bool(payload["capped"]),
                "gbif_fetched_at": payload["fetched_at"],
                "wcvp_key": native["wcvp_key"],
                "wcvp_ph_status": native["ph_status"],
                "wcvp_ph_endemic": native["ph_endemic"],
                "wcvp_fetched_at": native["fetched_at"],
            }
        )
    records = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return records, pd.DataFrame(rows)


def stage_base(records: pd.DataFrame, taxa: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Cleaned records, a per-species base table, and per-hex PA coverage."""
    kept, report = clean_occurrences(records)
    ranges = species_range_table(kept)
    all_cells = sorted({c for cells in ranges["hex_cells"] for c in cells})
    coverage = hex_protected_fraction(all_cells)
    ranges["pa_cell_share"] = [
        float(np.mean([coverage[c] for c in cells])) if cells else np.nan for cells in ranges["hex_cells"]
    ]
    base = (
        taxa.merge(report, on="scientific_name", how="left")
        .merge(ranges, on="scientific_name", how="left")
    )
    for col in ("n_fetched", "n_kept", "n_clean", "n_hex"):
        base[col] = base[col].fillna(0).astype(int)
    base["aoo_km2"] = base["aoo_km2"].fillna(0.0)
    base["eoo_km2"] = base["eoo_km2"].fillna(0.0)
    base["hex_cells"] = base["hex_cells"].map(lambda v: v if isinstance(v, list) else [])
    hex_table = pd.DataFrame({"h3": list(coverage), "pa_fraction": list(coverage.values())})
    return kept, base, hex_table


def _cell_provinces(records: pd.DataFrame) -> pd.DataFrame:
    """Modal GADM province per (species, H3 cell)."""
    from .grid import h3_cells

    r = records.dropna(subset=["lat", "lon"]).copy()
    r["h3"] = h3_cells(r["lat"], r["lon"])
    r = r.dropna(subset=["gadm_level1"])
    modal = (
        r.groupby(["scientific_name", "h3"])["gadm_level1"]
        .agg(lambda s: s.value_counts().index[0])
        .rename("province")
        .reset_index()
    )
    return modal


def stage_index(offline: bool = True) -> pd.DataFrame:
    """Components, gates, Monte Carlo ranks and tiers for every cohort species."""
    import h3

    from . import components as comp
    from .index import COMPONENTS, DEFAULT_WEIGHTS, gate, score, tier
    from .sources import climate_future as cf
    from .sources.dao import lookup as dao_lookup
    from .sources.effort import cell_effort, ph_land_cells
    from .sources.forest import province_loss
    from .sources.http import read_cache
    from .sources.wcvp import CACHE_DIR as WCVP_CACHE
    from .uncertainty import SpeciesEvidence, rank_summary

    cohort = load_cohort().set_index("scientific_name")
    base = pd.read_csv(V2_DIR / "species_base.csv", encoding="utf-8")
    base["hex_cells"] = base["hex_cells"].map(json.loads)
    records = pd.read_parquet(V2_DIR / "records_clean.parquet")
    pa = dict(pd.read_csv(V2_DIR / "hex_pa.csv").itertuples(index=False, name=None))
    traits = pd.read_csv(ROOT / "data" / "curated" / "harvest_traits.csv", encoding="utf-8", keep_default_na=False)
    traits = traits.set_index("scientific_name")
    loss = province_loss(offline=offline)
    loss_rate = loss.set_index("province")["loss_rate"]
    provinces = _cell_provinces(records)

    occupied = sorted({c for cells in base["hex_cells"] for c in cells})
    effort = cell_effort(sorted(set(ph_land_cells()) | set(occupied)), offline=offline)
    surveyed = {c for c, n in effort.items() if n >= comp.WELL_SURVEYED}
    dao = dao_lookup(base["scientific_name"].tolist())

    rows, evidence = [], []
    for b in base.itertuples(index=False):
        name = b.scientific_name
        meta = cohort.loc[name] if name in cohort.index else None
        status = b.wcvp_ph_status
        override = str(meta.get("nativity_override", "") if meta is not None else "").strip()
        if override:
            status = override
        wc = read_cache(WCVP_CACHE / f"{b.query_name.replace(' ', '_').replace('×', 'x')}.json.gz") or {}
        native_regions = sum(1 for d in wc.get("distribution", []) if not d.get("establishmentMeans"))

        cells = list(b.hex_cells)
        rr = comp.reporting_rate(cells, effort)
        r = comp.range_restriction(rr, native_regions)

        t = traits.loc[name] if name in traits.index else None
        h = comp.harvest_sensitivity(
            t["part_classes"] if t is not None else "",
            t["life_form"] if t is not None else "",
            t["sourcing"] if t is not None else "",
        )
        habitat = str(t["habitat"]) if t is not None else ""

        sp_prov = provinces[provinces["scientific_name"] == name].set_index("h3")["province"]
        cell_loss = np.array([loss_rate.get(sp_prov.get(c), np.nan) for c in cells], dtype=float)
        cell_pa = np.array([pa.get(c, np.nan) for c in cells], dtype=float)
        pa_share = float(np.nanmean(cell_pa)) if len(cells) else np.nan
        mean_loss = float(np.nanmean(cell_loss)) if np.isfinite(cell_loss).any() else np.nan
        e = comp.habitat_exposure(pa_share, mean_loss, habitat)

        c = {"C": np.nan, "c_min": np.nan, "c_max": np.nan, "dT": np.nan, "dT_min": np.nan, "dT_max": np.nan}
        if len(cells) >= 3:
            ll = np.array([h3.cell_to_latlng(x) for x in cells])
            cur = cf.sample_current(ll[:, 0], ll[:, 1])["bio1"]
            fut = [cf.sample_future(ll[:, 0], ll[:, 1], g, "ssp245")["bio1"] for g in cf.GCMS]
            c = comp.thermal_exceedance(cur, fut)

        gated = gate(status, len(cells))
        rows.append(
            {
                "scientific_name": name,
                "ph_status": status,
                "ph_endemic": bool(b.wcvp_ph_endemic),
                "native_regions": native_regions,
                "gate": gated,
                "n_cells": len(cells),
                "n_cells_surveyed": len(set(cells) & surveyed),
                "n_surveyed_ph": len(surveyed),
                "reporting_rate": rr,
                "pa_share": pa_share,
                "forest_loss_rate": mean_loss,
                "habitat": habitat,
                "dao_category": dao.get(name, ""),
                **r,
                **h,
                **e,
                **c,
            }
        )
        if not gated:
            evidence.append(
                SpeciesEvidence(
                    name=name,
                    k_surveyed=len(set(cells) & surveyed),
                    n_surveyed=len(surveyed),
                    r_global=r["r_global"],
                    H=h["H"],
                    C=c["C"],
                    habitat=habitat,
                    pa_fraction=np.nan_to_num(cell_pa, nan=0.0),
                    loss_rate=cell_loss,
                )
            )

    out = pd.DataFrame(rows)
    # Partial: a weighted component, or one of its sub-parts, could not be measured.
    sub_missing = out[["r_local", "r_global", "e_pa_gap", "e_forest_loss"]].isna().any(axis=1)
    out["partial"] = out[["R", "H", "E"]].isna().any(axis=1) | sub_missing
    out["score"] = score(out).where(out["gate"] == "")
    mc = rank_summary(evidence)
    out = out.merge(mc, on="scientific_name", how="left")
    out["tier"] = [tier(p, g) for p, g in zip(out["p_top_quartile"].fillna(0), out["gate"])]
    out["main_driver"] = main_driver(out)
    return out


def main_driver(scores: pd.DataFrame) -> pd.Series:
    """The weighted component furthest above the scored-cohort median, or "" if none is above."""
    from .index import COMPONENTS, DEFAULT_WEIGHTS

    active = [k for k in COMPONENTS if DEFAULT_WEIGHTS[k] > 0]
    scored = scores["gate"] == ""
    medians = scores.loc[scored, active].median()
    lift = (scores[active] - medians).mul(pd.Series(DEFAULT_WEIGHTS)[active])
    best = lift.fillna(-np.inf).idxmax(axis=1)
    above = lift.max(axis=1) > 0
    return best.where(scored & above, "")


def stage_validate() -> dict:
    from . import components as comp
    from . import validation as val
    from .sources.effort import cell_effort, ph_land_cells

    scores = pd.read_csv(V2_DIR / "scores.csv", encoding="utf-8", keep_default_na=False, na_values=[""])
    scored = scores[scores["gate"].isna()].copy()
    base = pd.read_csv(V2_DIR / "species_base.csv", encoding="utf-8").set_index("scientific_name")
    cells = base["hex_cells"].map(json.loads)
    occupied = sorted({c for cs in cells for c in cs})
    effort = cell_effort(sorted(set(ph_land_cells()) | set(occupied)), offline=True)

    reference = scored.set_index("scientific_name")["score"]
    effort_check = {}
    for well in (50, 200):
        alt = scored.copy()
        for i, row in alt.iterrows():
            rr = comp.reporting_rate(cells[row["scientific_name"]], effort, well=well)
            alt.at[i, "R"] = comp.range_restriction(rr, row["native_regions"])["R"]
        alt_score = val._weighted(alt, val.ACTIVE)
        effort_check[f"well_surveyed_{well}"] = val.spearman(reference.to_numpy(), alt_score.to_numpy())

    v1 = pd.read_csv(ROOT / "data" / "archive" / "v1.1" / "hpi_scores.csv", encoding="utf-8")
    return {
        "n_scored": int(len(scored)),
        "aggregation": val.aggregation(scored),
        "drop_component": val.drop_component(scored),
        "effort_threshold": {"well_surveyed_100": 1.0, **effort_check},
        "dao": val.dao_check(scored),
        "v1_vs_v2": val.v1_vs_v2(scored, v1),
        "interval_width_median": float((scored["rank_p95"] - scored["rank_p05"]).median()),
    }


def run(stages: list[str], offline: bool = False) -> None:
    V2_DIR.mkdir(parents=True, exist_ok=True)
    if "fetch" in stages or "base" in stages:
        records, taxa = stage_fetch(offline=offline or "fetch" not in stages)
        records.to_parquet(V2_DIR / "records_raw.parquet", index=False)
        taxa.to_csv(V2_DIR / "taxa.csv", index=False, encoding="utf-8")
        print(f"fetch: {len(taxa)} taxa, {len(records)} PH records")
    if "base" in stages:
        records = pd.read_parquet(V2_DIR / "records_raw.parquet")
        taxa = pd.read_csv(V2_DIR / "taxa.csv", encoding="utf-8")
        kept, base, hexes = stage_base(records, taxa)
        kept.to_parquet(V2_DIR / "records_clean.parquet", index=False)
        out = base.copy()
        out["hex_cells"] = out["hex_cells"].map(json.dumps)
        out.to_csv(V2_DIR / "species_base.csv", index=False, encoding="utf-8")
        hexes.to_csv(V2_DIR / "hex_pa.csv", index=False)
        print(f"base: kept {len(kept)} of {len(records)} records; {len(hexes)} occupied hex cells")
    if "index" in stages:
        scores = stage_index(offline=offline)
        scores.to_csv(V2_DIR / "scores.csv", index=False, encoding="utf-8")
        counts = scores["tier"].value_counts().to_dict()
        print(f"index: {len(scores)} species; tiers {counts}")
    if "validate" in stages:
        from .validation import write

        report = stage_validate()
        write(V2_DIR / "validation.json", report)
        print(f"validate: {report['n_scored']} scored species checked")
    if "export" in stages:
        from .export import run_export

        sizes = run_export()
        big = {k: v for k, v in sizes.items() if not k.startswith("species/")}
        detail = sum(v for k, v in sizes.items() if k.startswith("species/"))
        print("export:", {k: f"{v / 1024:.0f} KB" for k, v in big.items()}, f"species/*: {detail / 1024:.0f} KB")
