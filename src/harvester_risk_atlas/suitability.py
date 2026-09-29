"""Exploratory climate-suitability sketch (nice-to-have, Track 3).

NOT a species distribution model. Uses sklearn on presence lat/lon + sampled
WorldClim bio1/bio12/bio15 vs random background in SEA bbox. Documented as
exploratory only — do not cite as SDM / MaxEnt equivalent.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from .config import SEA_BBOX


FEATURE_NAMES = ["lat", "lon", "bio1_mean", "bio12_mean", "bio15_mean"]


def suitability_sketch(
    occ: pd.DataFrame,
    species: str,
    species_features: pd.Series | dict[str, Any] | None = None,
    n_background: int = 80,
    random_state: int = 42,
) -> dict[str, Any]:
    """Fit a tiny RF presence/background classifier; return metrics + caveat.

    Returns dict with keys: ok, message, n_presence, cv_auc_approx, feature_importance
    """
    out: dict[str, Any] = {
        "ok": False,
        "message": "",
        "n_presence": 0,
        "cv_score": None,
        "feature_importance": {},
        "caveat": (
            "Exploratory sketch only — not a species distribution model. "
            "Background points are uniform random in SEA bbox; no spatial CV; "
            "bioclim values are species-level means broadcast to points when "
            "per-point rasters are unavailable."
        ),
    }
    sub = occ[occ["scientific_name"] == species].dropna(subset=["lat", "lon"])
    if len(sub) < 8:
        out["message"] = f"Need ≥8 georeferenced points (have {len(sub)}); skipped."
        out["n_presence"] = int(len(sub))
        return out

    rng = np.random.default_rng(random_state)
    n_pos = min(len(sub), 60)
    pos = sub.sample(n=n_pos, random_state=random_state)

    # Broadcast species-level bioclim if available
    bio1 = bio12 = bio15 = np.nan
    if species_features is not None:
        get = species_features.get if hasattr(species_features, "get") else (
            lambda k, d=None: species_features[k] if k in species_features.index else d
        )
        bio1 = float(get("bio1_mean") or np.nan)
        bio12 = float(get("bio12_mean") or np.nan)
        bio15 = float(get("bio15_mean") or np.nan)

    if np.isnan(bio1) or np.isnan(bio12) or np.isnan(bio15):
        out["message"] = "Missing WorldClim species means; suitability sketch skipped."
        out["n_presence"] = int(len(sub))
        return out

    X_pos = np.column_stack(
        [
            pos["lat"].astype(float).values,
            pos["lon"].astype(float).values,
            np.full(n_pos, bio1),
            np.full(n_pos, bio12),
            np.full(n_pos, bio15),
        ]
    )
    # Random background in SEA bbox with jittered bioclim around species mean
    bg_lat = rng.uniform(SEA_BBOX["min_lat"], SEA_BBOX["max_lat"], n_background)
    bg_lon = rng.uniform(SEA_BBOX["min_lon"], SEA_BBOX["max_lon"], n_background)
    X_bg = np.column_stack(
        [
            bg_lat,
            bg_lon,
            bio1 + rng.normal(0, abs(bio1) * 0.05 + 0.5, n_background),
            bio12 + rng.normal(0, abs(bio12) * 0.08 + 50, n_background),
            bio15 + rng.normal(0, abs(bio15) * 0.08 + 2, n_background),
        ]
    )
    X = np.vstack([X_pos, X_bg])
    y = np.array([1] * n_pos + [0] * n_background)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = RandomForestClassifier(
        n_estimators=40, max_depth=4, random_state=random_state, class_weight="balanced"
    )
    # 3-fold accuracy as a crude signal (not AUC to avoid roc_auc edge cases)
    try:
        scores = cross_val_score(clf, Xs, y, cv=3, scoring="accuracy")
        cv = float(np.mean(scores))
    except Exception as e:
        out["message"] = f"CV failed: {e}"
        out["n_presence"] = int(len(sub))
        return out

    clf.fit(Xs, y)
    imp = {FEATURE_NAMES[i]: float(clf.feature_importances_[i]) for i in range(len(FEATURE_NAMES))}
    out.update(
        {
            "ok": True,
            "message": "Fitted exploratory presence/background RF on lat/lon + bioclim means.",
            "n_presence": int(len(sub)),
            "cv_score": cv,
            "feature_importance": imp,
        }
    )
    return out
