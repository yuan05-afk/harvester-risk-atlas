"""HPI v2 — Harvest Priority Index: gates, aggregation and priority tiers.

The score orders attention within this cohort. It is not a Red List
category, not a harvest permit, and not medical advice.

Gates (a species is shown but not scored when either applies):
  not_native         WCVP does not list the species as native to the Philippines
                     (a cited override in cohort.csv can change this)
  insufficient_data  fewer than ``MIN_CELLS`` occupied H3 cells after cleaning

Aggregation: weighted arithmetic mean over the components a species has.
Missing components are dropped and the remaining weights rescaled; the
species is flagged ``partial``.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

COMPONENTS = ("R", "H", "E", "C")
DEFAULT_WEIGHTS = {"R": 1 / 3, "H": 1 / 3, "E": 1 / 3, "C": 0.0}
MIN_CELLS = 5
TIER_HIGH = 0.8
TIER_WATCH = 0.3
TIERS = ("High attention", "Watch", "Lower", "Not scored")


def gate(ph_status: str, n_cells: int) -> str:
    """'' when the species is scored, else the reason it is not."""
    if ph_status != "native":
        return "not_native"
    if int(n_cells or 0) < MIN_CELLS:
        return "insufficient_data"
    return ""


def normalize(weights: dict[str, float] | None) -> dict[str, float]:
    """Non-negative weights over COMPONENTS that sum to 1 (defaults if all zero)."""
    w = {k: max(0.0, float((weights or {}).get(k, 0.0) or 0.0)) for k in COMPONENTS}
    w = {k: (v if math.isfinite(v) else 0.0) for k, v in w.items()}
    total = sum(w.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in w.items()}


def aggregate(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Weighted mean over finite values along the last axis.

    ``values`` (..., k) may hold NaN; ``weights`` broadcasts against it.
    Rows with no weighted finite value return NaN.
    """
    v = np.asarray(values, float)
    w = np.broadcast_to(np.asarray(weights, float), v.shape)
    mask = np.isfinite(v) & (w > 0)
    num = np.where(mask, v * w, 0.0).sum(axis=-1)
    den = np.where(mask, w, 0.0).sum(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


def score(components: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.Series:
    w = normalize(weights or DEFAULT_WEIGHTS)
    vals = components[list(COMPONENTS)].to_numpy(float)
    return pd.Series(aggregate(vals, np.array([w[k] for k in COMPONENTS])), index=components.index)


def ranks(scores: np.ndarray) -> np.ndarray:
    """Rank 1 = highest score; ties share the best rank. NaN stays NaN."""
    s = pd.Series(scores)
    return s.rank(ascending=False, method="min").to_numpy()


def tier(p_top: float, gated: str) -> str:
    if gated:
        return "Not scored"
    if p_top >= TIER_HIGH:
        return "High attention"
    if p_top >= TIER_WATCH:
        return "Watch"
    return "Lower"
