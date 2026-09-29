"""Harvest Pressure Index (HPI) v1 — transparent formula.

HPI is a unitless [0, 1] score. Higher = greater relative harvest/climate
pressure concern for monitoring — NOT a clinical or legal determination.

Formula
-------
    HPI = w_r * R + w_c * C + w_h * H + w_p * P

where (each component scaled to [0, 1]):
    R  rarity_score      — high when few GBIF occurrences + endemism cue
    C  climate_stress    — high when thermal/precip niche is tight or shifting
    H  harvest_proxy     — high when points cluster near coasts/roads proxy
                           or show recent occurrence decline
    P  pa_gap            — high when few occurrences fall in protected areas

Default weights (documented, tunable):
    w_r=0.30, w_c=0.25, w_h=0.25, w_p=0.20

Confidence
----------
    confidence = max(0.2, CONFIDENCE_BASE - n_imputed * CONFIDENCE_PENALTY)

Components marked `*_imputed=True` were filled when WorldClim / WDPCA inputs
were unavailable for that species. IUCN category is NEVER an HPI input.
Never treat HPI as Red List status.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import CONFIDENCE_BASE, CONFIDENCE_PENALTY_MISSING, HPI_WEIGHTS


def _minmax(s: pd.Series, invert: bool = False) -> pd.Series:
    s = s.astype(float)
    lo, hi = s.min(), s.max()
    if hi == lo or np.isnan(hi) or np.isnan(lo):
        out = pd.Series(0.5, index=s.index)
    else:
        out = (s - lo) / (hi - lo)
    if invert:
        out = 1.0 - out
    return out.clip(0.0, 1.0)


def rarity_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Higher rarity when fewer occurrences; boost for forest/SEA endemism notes."""
    n = df["n_occurrences"].fillna(0).astype(float)
    # log-inverse richness
    base = _minmax(np.log1p(n), invert=True)
    endemism_map = {
        "widespread": 0.0,
        "widespread_tropics": 0.05,
        "widespread_weed": 0.0,
        "cultivated": 0.05,
        "cultivated_wild": 0.1,
        "cultivated_coastal": 0.05,
        "introduced_naturalized": 0.0,
        "SEA_cultivated": 0.1,
        "SEA": 0.25,
        "SEA_India": 0.2,
        "PH_SEA": 0.35,
        "SEA_forest": 0.55,
    }
    boost = df["endemism_proxy"].map(endemism_map).fillna(0.15).astype(float)
    score = (0.7 * base + 0.3 * boost).clip(0, 1)
    imputed = pd.Series(False, index=df.index)
    return score, imputed


def climate_stress_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Climate stress from WorldClim 2.1 bioclim (preferred) + lat-range backup.

    Preferred inputs (from features.climate_stress_raw / bio*):
      - climate_stress_raw: niche squeeze (bio1 std) + bio15 seasonality + thermal anomaly
    Backup when rasters missing:
      - narrow latitudinal range + |lat−12°| thermal cue (imputed=True)
    """
    lat_range = (df["lat_max"] - df["lat_min"]).fillna(5.0).astype(float)
    squeeze = _minmax(lat_range, invert=True)
    core_dist = (df["lat_mean"].fillna(12.0) - 12.0).abs()
    thermal = _minmax(core_dist)
    backup = (0.6 * squeeze + 0.4 * thermal).clip(0, 1)

    raw_col = None
    for c in ("climate_stress_raw", "climate_anomaly_proxy"):
        if c in df.columns and df[c].notna().any():
            raw_col = c
            break
    if raw_col is not None:
        raw = df[raw_col].astype(float)
        # Species-relative min-max so the bioclim cue spans the atlas cohort
        bioclim = _minmax(raw.fillna(raw.median() if raw.notna().any() else 0.5))
        # Blend: mostly WorldClim, light lat-range regularizer
        score = (0.75 * bioclim + 0.25 * backup).clip(0, 1)
        imputed = raw.isna()
        return score, imputed
    return backup, pd.Series(True, index=df.index)


def harvest_proxy_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Accessibility / demand / decline cues without inventing harvest volumes.

    - Coastal proximity proxy: mean |lon - 121| inverted towards coasts is weak;
      instead use fraction of points with low elevation proxy if present,
      else use high occurrence density in small geographic cell (pressure cue).
    - Temporal decline: if year_span and recent_frac available.
    """
    # Density cue: many points in small bbox → local pressure
    # Zero-occurrence / missing geo → neutral density (0.5 after minmax fallback)
    lat_span = (df["lat_max"] - df["lat_min"]).fillna(2.0).clip(lower=0.1)
    lon_span = (df["lon_max"] - df["lon_min"]).fillna(2.0).clip(lower=0.1)
    area = (lat_span * lon_span).astype(float).replace(0, 0.1)
    n = df["n_occurrences"].fillna(0).astype(float)
    density = n / area
    dens_score = _minmax(np.log1p(density))
    dens_score = dens_score.where(n > 0, 0.5)

    if "recent_occurrence_frac" in df.columns:
        # Low recent fraction → possible decline (higher concern)
        decline = _minmax(df["recent_occurrence_frac"].fillna(0.5), invert=True)
        imputed_decl = df["recent_occurrence_frac"].isna()
    else:
        decline = pd.Series(0.5, index=df.index)
        imputed_decl = pd.Series(True, index=df.index)

    # Literature harvest-concern flag from seed notes (binary cue, transparent)
    concern = df.get(
        "harvest_concern_flag", pd.Series(0, index=df.index)
    ).fillna(0).astype(float)
    score = (0.4 * dens_score + 0.35 * decline + 0.25 * concern).clip(0, 1)
    return score, imputed_decl


def pa_gap_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Protected-area gap from real WDPCA polygons (preferred).

    P = 1 - frac_in_protected, with a mild distance boost when frac is low:
    points far from any PA raise gap slightly (capped). Imputed only when
    PA layer / metrics are missing.
    """
    frac_col = None
    for c in ("frac_in_protected", "frac_in_protected_proxy"):
        if c in df.columns:
            frac_col = c
            break
    if frac_col is None:
        return pd.Series(0.55, index=df.index), pd.Series(True, index=df.index)

    frac = df[frac_col].astype(float)
    imputed = frac.isna()
    # Observed overlap → gap; missing overlap (no points) → neutral 0.55 imputed
    gap = (1.0 - frac).where(frac.notna(), 0.55)
    if "mean_dist_to_pa_km" in df.columns:
        dist = df["mean_dist_to_pa_km"].astype(float)
        boost = (dist.fillna(0).clip(0, 100) / 50.0).clip(0, 1) * 0.15
        # Distance boost only for observed points outside PAs
        gap = gap.where(imputed, (gap + boost * (1.0 - frac.fillna(0.0))).clip(0, 1))
    return gap.clip(0, 1), imputed


def compute_hpi(features: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Return features plus HPI components, score, band, and confidence."""
    w = weights or HPI_WEIGHTS
    df = features.copy()

    R, R_imp = rarity_score(df)
    C, C_imp = climate_stress_score(df)
    H, H_imp = harvest_proxy_score(df)
    P, P_imp = pa_gap_score(df)

    df["component_rarity"] = R
    df["component_climate"] = C
    df["component_harvest"] = H
    df["component_pa_gap"] = P
    df["rarity_imputed"] = R_imp
    df["climate_imputed"] = C_imp
    df["harvest_imputed"] = H_imp
    df["pa_gap_imputed"] = P_imp

    df["hpi"] = (
        w["rarity"] * R
        + w["climate_stress"] * C
        + w["harvest_proxy"] * H
        + w["pa_gap"] * P
    ).clip(0, 1)

    n_imp = (
        R_imp.astype(int)
        + C_imp.astype(int)
        + H_imp.astype(int)
        + P_imp.astype(int)
    )
    df["hpi_confidence"] = (
        CONFIDENCE_BASE - n_imp * CONFIDENCE_PENALTY_MISSING
    ).clip(lower=0.2, upper=0.95)

    df["hpi_band"] = pd.cut(
        df["hpi"],
        bins=[-0.01, 0.33, 0.66, 1.01],
        labels=["Lower relative pressure", "Moderate", "Higher relative pressure"],
    )
    df["hpi_weights_json"] = str(w)
    return df


def hpi_formula_markdown() -> str:
    return (
        "**HPI v1.1** = 0.30·Rarity + 0.25·Climate stress + 0.25·Harvest proxy "
        "+ 0.20·Protected-area gap. Each component ∈ [0,1]. "
        "Confidence falls when components are imputed. "
        "Not IUCN status; not medical advice."
    )


def weights_explainer_markdown() -> str:
    """Methods-page copy for the weights expander. Weights are the live config."""
    w = HPI_WEIGHTS
    total = float(sum(w.values()))
    return (
        "| Component | Weight | What it captures |\n"
        "|-----------|--------|------------------|\n"
        f"| Rarity | {w['rarity']:.2f} | Few GBIF records and an endemism cue |\n"
        f"| Climate stress | {w['climate_stress']:.2f} | Tight or shifted WorldClim niche in the SEA clip |\n"
        f"| Harvest proxy | {w['harvest_proxy']:.2f} | Accessibility and recent-record pattern. Not a volume |\n"
        f"| Protected-area gap | {w['pa_gap']:.2f} | Share of sample points outside WDPCA Philippines polygons |\n\n"
        f"**Sum {total:.2f}.** These weights are a documented choice. "
        "They are not an IUCN index and not a harvest quota. "
        "IUCN category is never an input."
    )


def dossier_actions(row: dict[str, Any]) -> list[str]:
    """Non-prescriptive stewardship suggestions for field briefs."""
    actions = [
        "Prefer cultivated / community-nursery material over wild collection when feasible.",
        "Record GPS, date, habitat, and harvest method; share with LGU / DENR partners if appropriate.",
        "Cross-check current IUCN Red List and national lists before any commercial volume claims.",
    ]
    if float(row.get("component_pa_gap", 0) or 0) >= 0.5:
        actions.append(
            "Many mapped points fall outside protected-area proxies — prioritize habitat stewardship dialogues."
        )
    if float(row.get("component_climate", 0) or 0) >= 0.5:
        actions.append(
            "Climate niche appears relatively tight/shifted in this proxy — monitor phenology and moisture stress."
        )
    if float(row.get("component_rarity", 0) or 0) >= 0.5:
        actions.append(
            "Sparse occurrence records and/or endemism cues — treat wild harvest as high-caution."
        )
    actions.append(
        "This atlas is for research & education only — not medical advice or harvest permits."
    )
    return actions
