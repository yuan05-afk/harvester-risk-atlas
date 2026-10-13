"""Rank uncertainty for HPI v2 by Monte Carlo.

Each draw perturbs two things at once:
  weights  Dirichlet centred on the default weights (concentration ``ALPHA``)
           over the components with non-zero default weight
  evidence - local rarity: reporting rate drawn from Beta(k + ½, N − k + ½),
             the Jeffreys posterior for k occupied of N well-surveyed cells
           - protected-area gap and forest loss: occupied cells resampled
             with replacement (one resample shared by both)
Curated harvest traits and WCVP region counts are held fixed.

Outputs per scored species: median rank, 90% rank interval (5th–95th
percentile) and P(top quartile). Rank 1 is the highest priority.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .components import FOREST_AFFINITY, LOSS_ANCHOR, RR_ANCHORS, _log_anchor
from .index import COMPONENTS, DEFAULT_WEIGHTS, aggregate

N_DRAWS = 2000
ALPHA = 10.0
SEED = 20261102


@dataclass
class SpeciesEvidence:
    name: str
    k_surveyed: int  # occupied cells that are well surveyed
    n_surveyed: int  # all well-surveyed cells in the Philippines
    r_global: float
    H: float
    C: float
    habitat: str
    pa_fraction: np.ndarray = field(default_factory=lambda: np.zeros(0))
    loss_rate: np.ndarray = field(default_factory=lambda: np.zeros(0))


def _r_local_draws(ev: SpeciesEvidence, rng: np.random.Generator, n: int) -> np.ndarray:
    if ev.n_surveyed <= 0 or ev.k_surveyed <= 0:
        return np.full(n, np.nan)
    rr = rng.beta(ev.k_surveyed + 0.5, ev.n_surveyed - ev.k_surveyed + 0.5, size=n)
    return np.array([_log_anchor(x, *RR_ANCHORS) for x in rr])


def _e_draws(ev: SpeciesEvidence, rng: np.random.Generator, n: int) -> np.ndarray:
    m = len(ev.pa_fraction)
    if m == 0:
        return np.full(n, np.nan)
    idx = rng.integers(0, m, size=(n, m))
    gap = 1.0 - ev.pa_fraction[idx].mean(axis=1)
    affinity = FOREST_AFFINITY.get(ev.habitat, math.nan)
    loss = ev.loss_rate[idx]
    finite = np.isfinite(loss)
    n_finite = finite.sum(axis=1)
    loss_mean = np.where(n_finite > 0, np.where(finite, loss, 0.0).sum(axis=1) / np.maximum(n_finite, 1), np.nan)
    forest = np.clip(loss_mean / LOSS_ANCHOR, 0, 1) * affinity if math.isfinite(affinity) else np.full(n, np.nan)
    stacked = np.stack([gap, forest], axis=1)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(stacked).any(axis=1), np.nanmean(stacked, axis=1), np.nan)


def component_draws(evidence: list[SpeciesEvidence], n: int = N_DRAWS, seed: int = SEED) -> np.ndarray:
    """Array (n_draws, n_species, 4) of R, H, E, C draws."""
    rng = np.random.default_rng(seed)
    out = np.full((n, len(evidence), len(COMPONENTS)), np.nan)
    for j, ev in enumerate(evidence):
        r_loc = _r_local_draws(ev, rng, n)
        r_glob = np.full(n, ev.r_global)
        stacked = np.stack([r_loc, r_glob], axis=1)
        with np.errstate(invalid="ignore"):
            out[:, j, 0] = np.where(np.isfinite(stacked).any(axis=1), np.nanmean(stacked, axis=1), np.nan)
        out[:, j, 1] = ev.H
        out[:, j, 2] = _e_draws(ev, rng, n)
        out[:, j, 3] = ev.C
    return out


def weight_draws(n: int = N_DRAWS, seed: int = SEED + 1, base: dict[str, float] | None = None) -> np.ndarray:
    """Array (n_draws, 4). Components with zero base weight stay at zero."""
    base = base or DEFAULT_WEIGHTS
    rng = np.random.default_rng(seed)
    active = [i for i, k in enumerate(COMPONENTS) if base[k] > 0]
    alpha = np.array([ALPHA * base[COMPONENTS[i]] * len(active) for i in active])
    w = np.zeros((n, len(COMPONENTS)))
    w[:, active] = rng.dirichlet(alpha, size=n)
    return w


def rank_summary(evidence: list[SpeciesEvidence], n: int = N_DRAWS, seed: int = SEED) -> pd.DataFrame:
    comps = component_draws(evidence, n, seed)
    weights = weight_draws(n, seed + 1)
    scores = aggregate(comps, weights[:, None, :])  # (n, species)
    ranks = np.full_like(scores, np.nan)
    for i in range(n):
        ranks[i] = pd.Series(scores[i]).rank(ascending=False, method="min").to_numpy()
    n_species = len(evidence)
    top_q = math.ceil(n_species / 4)
    return pd.DataFrame(
        {
            "scientific_name": [e.name for e in evidence],
            "score_median": np.nanmedian(scores, axis=0),
            "score_p05": np.nanpercentile(scores, 5, axis=0),
            "score_p95": np.nanpercentile(scores, 95, axis=0),
            "rank_median": np.nanmedian(ranks, axis=0),
            "rank_p05": np.nanpercentile(ranks, 5, axis=0),
            "rank_p95": np.nanpercentile(ranks, 95, axis=0),
            "p_top_quartile": np.mean(ranks <= top_q, axis=0),
            "top_quartile_size": top_q,
        }
    )
