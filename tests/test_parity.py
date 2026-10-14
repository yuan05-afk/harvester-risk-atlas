"""parity.json is the golden file web/src/lib/score.test.ts checks score.ts against."""
import numpy as np
import pandas as pd

from harvester_risk_atlas.export import PARITY_WEIGHT_SETS, build_parity
from harvester_risk_atlas.index import COMPONENTS, ranks, score


def _summary(slug, r, h, e, c, gate=""):
    return {"slug": slug, "gate": gate, "components": {"R": r, "H": h, "E": e, "C": c}}


def test_parity_ranks_match_index_and_skip_gated():
    rows = [
        _summary("a", 0.9, 0.8, 0.7, 0.5),
        _summary("b", 0.1, None, 0.2, 0.5),
        _summary("c", 0.5, 0.5, 0.5, 0.5),
        _summary("g", 0.9, 0.9, 0.9, 0.9, gate="not_native"),
    ]
    p = build_parity(rows)
    assert set(p["components"]) == {"a", "b", "c"}
    assert [s["name"] for s in p["sets"]] == list(PARITY_WEIGHT_SETS)
    comps = pd.DataFrame([{k: np.nan if r["components"][k] is None else r["components"][k] for k in COMPONENTS} for r in rows[:3]])
    for s in p["sets"]:
        expect = ranks(score(comps, PARITY_WEIGHT_SETS[s["name"]]).to_numpy())
        assert [s["ranks"][k] for k in "abc"] == list(expect)
        assert abs(sum(s["weights"].values()) - 1) < 1e-3
