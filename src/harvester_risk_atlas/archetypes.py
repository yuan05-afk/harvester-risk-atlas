"""Risk archetypes via sklearn clustering on HPI components (Track 3 DS/ML).

Clusters are descriptive labels for the atlas cohort — not IUCN categories
and not a clinical/legal determination.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

COMPONENT_COLS = [
    "component_rarity",
    "component_climate",
    "component_harvest",
    "component_pa_gap",
]

# Human labels keyed by dominant mean component within a cluster
_LABEL_BY_DOMINANT = {
    "component_rarity": "Sparse / rarity-driven",
    "component_climate": "Climate-stressed",
    "component_harvest": "Harvest-pressured",
    "component_pa_gap": "PA-gap exposed",
}


def _label_cluster(centroid: dict[str, float], global_mean: dict[str, float]) -> str:
    """Name cluster by which component sits furthest above cohort mean."""
    deltas = {k: centroid[k] - global_mean[k] for k in COMPONENT_COLS}
    # If all near mean → balanced
    if max(abs(v) for v in deltas.values()) < 0.08:
        return "Balanced moderate"
    dominant = max(deltas, key=deltas.get)
    if deltas[dominant] < 0.05:
        # All below or flat — low-pressure profile
        return "Lower-pressure profile"
    return _LABEL_BY_DOMINANT[dominant]


def assign_archetypes(
    hpi: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42,
) -> pd.DataFrame:
    """Return a copy of hpi with archetype_id, archetype_label, archetype_note.

    Runs KMeans on the four HPI components (standardized). Small-n safe:
    clamps k to min(n_clusters, n_species - 1, 5).
    """
    df = hpi.copy()
    if df.empty or not all(c in df.columns for c in COMPONENT_COLS):
        df["archetype_id"] = -1
        df["archetype_label"] = "n/a"
        df["archetype_note"] = "Components missing"
        return df

    X = df[COMPONENT_COLS].astype(float).fillna(0.5).values
    n = len(df)
    k = max(2, min(n_clusters, n - 1, 5)) if n >= 3 else 1
    if k < 2:
        df["archetype_id"] = 0
        df["archetype_label"] = "Cohort (too few species)"
        df["archetype_note"] = "Need ≥3 species for clustering"
        return df

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    km = KMeans(n_clusters=k, n_init=10, random_state=random_state)
    labels = km.fit_predict(Xs)

    # Centroids in original [0,1] space (mean of members)
    global_mean = {c: float(df[c].astype(float).mean()) for c in COMPONENT_COLS}
    id_to_label: dict[int, str] = {}
    for cid in range(k):
        mask = labels == cid
        centroid = {c: float(df.loc[mask, c].astype(float).mean()) for c in COMPONENT_COLS}
        id_to_label[cid] = _label_cluster(centroid, global_mean)

    # Disambiguate duplicate names with short suffix
    seen: dict[str, int] = {}
    for cid, lab in list(id_to_label.items()):
        seen[lab] = seen.get(lab, 0) + 1
        if seen[lab] > 1:
            id_to_label[cid] = f"{lab} ({cid + 1})"

    df["archetype_id"] = labels.astype(int)
    df["archetype_label"] = [id_to_label[int(i)] for i in labels]
    df["archetype_note"] = (
        f"KMeans k={k} on standardized HPI components "
        f"(R,C,H,P); labels from dominant elevation vs cohort mean"
    )
    return df


def archetype_summary(hpi_with_arch: pd.DataFrame) -> pd.DataFrame:
    """Per-archetype counts and mean HPI / components for Methods / Map panels."""
    if "archetype_label" not in hpi_with_arch.columns:
        return pd.DataFrame()
    g = hpi_with_arch.groupby("archetype_label", dropna=False)
    rows: list[dict[str, Any]] = []
    for lab, sub in g:
        rows.append(
            {
                "archetype": lab,
                "n": len(sub),
                "mean_hpi": float(sub["hpi"].mean()),
                "mean_rarity": float(sub["component_rarity"].mean()),
                "mean_climate": float(sub["component_climate"].mean()),
                "mean_harvest": float(sub["component_harvest"].mean()),
                "mean_pa_gap": float(sub["component_pa_gap"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("mean_hpi", ascending=False)


def pick_demo_species(hpi: pd.DataFrame) -> str:
    """Strong judging-video example: harvest concern + real climate/PA + decent n."""
    preferred = [
        "Arcangelisia flava",
        "Lagerstroemia speciosa",
        "Vitex negundo",
        "Tinospora crispa",
    ]
    names = set(hpi["scientific_name"].astype(str))
    for p in preferred:
        if p in names:
            return p
    # Fallback: highest HPI with n_occurrences > 0
    scored = hpi[hpi["n_occurrences"].fillna(0) > 0]
    if scored.empty:
        return str(hpi.iloc[0]["scientific_name"])
    return str(scored.sort_values("hpi", ascending=False).iloc[0]["scientific_name"])
