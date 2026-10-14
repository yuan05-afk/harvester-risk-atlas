"""Checks on HPI v2. There is no ground truth for harvest priority, so these
test robustness and plausibility, not accuracy.

  aggregation     rank agreement between the weighted mean and two
                  alternatives (geometric mean, mean of component ranks)
  drop_component  rank agreement when each weighted component is left out
  effort          rank agreement when the well-surveyed threshold changes
  dao             where nationally listed threatened species (DAO 2026-20)
                  fall in the ranking, with a permutation p-value; a
                  directional check only, given how few are in the cohort
  v1_vs_v2        rank agreement with the archived v1.1 index
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from .index import COMPONENTS, DEFAULT_WEIGHTS, aggregate

ACTIVE = [k for k in COMPONENTS if DEFAULT_WEIGHTS[k] > 0]


def spearman(a, b) -> float:
    a, b = pd.Series(a, dtype=float), pd.Series(b, dtype=float)
    ok = a.notna() & b.notna()
    if ok.sum() < 3:
        return math.nan
    return float(a[ok].rank().corr(b[ok].rank()))


def _weighted(df: pd.DataFrame, comps: list[str]) -> pd.Series:
    w = np.array([DEFAULT_WEIGHTS[k] for k in comps])
    return pd.Series(aggregate(df[comps].to_numpy(float), w), index=df.index)


def aggregation(scored: pd.DataFrame) -> dict:
    base = _weighted(scored, ACTIVE)
    vals = scored[ACTIVE].clip(lower=1e-6)
    geo = np.exp(np.log(vals).mean(axis=1, skipna=True))
    rank_mean = scored[ACTIVE].rank(ascending=False).mean(axis=1) * -1
    return {
        "geometric_mean": spearman(base, geo),
        "mean_component_rank": spearman(base, rank_mean),
    }


def drop_component(scored: pd.DataFrame) -> dict:
    base = _weighted(scored, ACTIVE)
    return {f"without_{k}": spearman(base, _weighted(scored, [c for c in ACTIVE if c != k])) for k in ACTIVE}


def dao_check(scored: pd.DataFrame, n_perm: int = 10_000, seed: int = 7) -> dict:
    listed = scored["dao_category"].fillna("").astype(str).str.len() > 0
    r = scored["rank_median"].to_numpy(float)
    k = int(listed.sum())
    if k == 0:
        return {"n_listed": 0}
    observed = float(np.mean(r[listed.to_numpy()]))
    rng = np.random.default_rng(seed)
    perms = np.array([np.mean(rng.choice(r, size=k, replace=False)) for _ in range(n_perm)])
    return {
        "n_listed": k,
        "n_scored": int(len(scored)),
        "listed": scored.loc[listed, ["scientific_name", "dao_category", "rank_median", "tier"]].to_dict("records"),
        "mean_rank_listed": observed,
        "mean_rank_all": float(np.mean(r)),
        # One-sided: are listed species ranked higher (smaller rank) than chance?
        "p_value": float((np.sum(perms <= observed) + 1) / (n_perm + 1)),
    }


def v1_vs_v2(scored: pd.DataFrame, v1: pd.DataFrame) -> dict:
    m = scored.merge(v1[["scientific_name", "hpi"]], on="scientific_name", how="inner")
    return {"n_shared": int(len(m)), "spearman": spearman(m["score"], m["hpi"])}


def write(path, payload: dict) -> None:
    def clean(o):
        if isinstance(o, float) and not math.isfinite(o):
            return None
        if isinstance(o, (np.floating,)):
            return clean(float(o))
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return o

    path.write_text(json.dumps(clean(payload), indent=2, ensure_ascii=False), encoding="utf-8")
