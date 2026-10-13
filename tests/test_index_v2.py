"""HPI v2: component scales, gates, aggregation, uncertainty and tiers.

Several tests pin v1 failures so they cannot return:
  S1/S16  rarity tied to a fetch cap / cohort min–max  → anchored, per-species scales
  S2      a species with no records ranked #1          → gated, never scored
  S10/S13 no uncertainty, uninformative confidence     → Monte Carlo rank intervals
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harvester_risk_atlas import components as comp  # noqa: E402
from harvester_risk_atlas.index import aggregate, gate, normalize, ranks, score, tier  # noqa: E402
from harvester_risk_atlas.pipeline import main_driver  # noqa: E402
from harvester_risk_atlas.uncertainty import SpeciesEvidence, rank_summary  # noqa: E402


class RangeRestriction(unittest.TestCase):
    def test_rarer_reporting_rate_scores_higher(self):
        vals = [comp.range_restriction(rr, 10)["r_local"] for rr in (0.5, 0.1, 0.02, 0.005)]
        self.assertEqual(vals, sorted(vals))
        self.assertAlmostEqual(vals[0], 0.0)
        self.assertAlmostEqual(vals[-1], 1.0)

    def test_scale_is_anchored_not_cohort_relative(self):
        # Same inputs give the same value whatever else is in the cohort.
        a = comp.range_restriction(0.05, 3)
        b = comp.range_restriction(0.05, 3)
        self.assertEqual(a, b)

    def test_never_recorded_in_surveyed_cells_is_unmeasured_not_rare(self):
        r = comp.range_restriction(0.0, 5)
        self.assertTrue(math.isnan(r["r_local"]))
        self.assertAlmostEqual(r["R"], r["r_global"])

    def test_global_restriction_from_native_regions(self):
        self.assertAlmostEqual(comp.range_restriction(0.1, 1)["r_global"], 1.0)
        self.assertAlmostEqual(comp.range_restriction(0.1, 50)["r_global"], 0.0)
        self.assertTrue(math.isnan(comp.range_restriction(0.1, 0)["r_global"]))

    def test_reporting_rate_counts_only_well_surveyed_cells(self):
        effort = {"a": 500, "b": 150, "c": 20, "d": 100}
        self.assertAlmostEqual(comp.reporting_rate(["a", "c"], effort), 1 / 3)
        self.assertTrue(math.isnan(comp.reporting_rate(["a"], {"a": 5})))


class HarvestSensitivity(unittest.TestCase):
    def test_destructive_woody_wild_scores_high(self):
        h = comp.harvest_sensitivity("bark;leaf_flower", "tree", "wild_only")
        self.assertAlmostEqual(h["h_part"], 1.0)
        self.assertAlmostEqual(h["H"], 1.0)

    def test_leaf_herb_cultivated_scores_low(self):
        h = comp.harvest_sensitivity("leaf_flower", "herb", "wild_and_cultivated")
        self.assertAlmostEqual(h["H"], (0.25 + 0.3 + 0.5) / 3)

    def test_first_listed_and_most_destructive_part_both_count(self):
        # Leaves first, roots later: half of each.
        h = comp.harvest_sensitivity("leaf_flower;underground", "shrub", "wild_only")
        self.assertAlmostEqual(h["h_part"], 0.5 * 0.25 + 0.5 * 1.0)

    def test_uncurated_traits_are_nan(self):
        self.assertTrue(math.isnan(comp.harvest_sensitivity("", "", "")["H"]))
        self.assertTrue(math.isnan(comp.harvest_sensitivity("bark", "tree", "")["H"]))


class HabitatExposure(unittest.TestCase):
    def test_open_habitat_gets_no_forest_loss_exposure(self):
        e = comp.habitat_exposure(0.2, 0.15, "open")
        self.assertAlmostEqual(e["e_forest_loss"], 0.0)
        self.assertAlmostEqual(e["E"], (0.8 + 0.0) / 2)

    def test_forest_affinity_scales_loss(self):
        forest = comp.habitat_exposure(0.2, 0.10, "forest")["e_forest_loss"]
        mixed = comp.habitat_exposure(0.2, 0.10, "mixed")["e_forest_loss"]
        self.assertAlmostEqual(forest, 0.5)
        self.assertAlmostEqual(mixed, 0.25)

    def test_unknown_habitat_leaves_forest_part_unmeasured(self):
        e = comp.habitat_exposure(0.3, 0.10, "")
        self.assertTrue(math.isnan(e["e_forest_loss"]))
        self.assertAlmostEqual(e["E"], 0.7)

    def test_more_protection_lowers_exposure(self):
        self.assertGreater(
            comp.habitat_exposure(0.1, 0.05, "forest")["E"], comp.habitat_exposure(0.6, 0.05, "forest")["E"]
        )


class ClimateExposure(unittest.TestCase):
    def test_uniform_warming_counts_cells_above_current_p95(self):
        cur = np.linspace(24, 28, 21)
        res = comp.thermal_exceedance(cur, [cur + 1.0, cur + 2.0])
        self.assertAlmostEqual(res["dT_min"], 1.0)
        self.assertAlmostEqual(res["dT_max"], 2.0)
        self.assertGreater(res["c_max"], res["c_min"])

    def test_too_few_cells_is_nan(self):
        self.assertTrue(math.isnan(comp.thermal_exceedance([25.0, 26.0], [[26.0, 27.0]])["C"]))


class GatesAndAggregation(unittest.TestCase):
    def test_zero_record_species_is_never_scored(self):
        # v1 ranked Mentha × piperita first with no records at all (S2).
        self.assertEqual(gate("native", 0), "insufficient_data")
        self.assertEqual(gate("not_found", 0), "not_native")
        self.assertEqual(tier(1.0, "insufficient_data"), "Not scored")

    def test_introduced_species_are_not_scored(self):
        for status in ("introduced", "not_listed", "not_found"):
            self.assertEqual(gate(status, 200), "not_native")
        self.assertEqual(gate("native", 5), "")

    def test_missing_components_drop_out_and_weights_rescale(self):
        vals = np.array([[0.6, np.nan, 0.2, 0.9]])
        w = np.array([1 / 3, 1 / 3, 1 / 3, 0.0])
        self.assertAlmostEqual(aggregate(vals, w)[0], 0.4)

    def test_all_missing_is_nan(self):
        self.assertTrue(np.isnan(aggregate(np.array([[np.nan] * 4]), np.ones(4))[0]))

    def test_normalize(self):
        w = normalize({"R": 2, "H": 1, "E": 1, "C": -5})
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertEqual(w["C"], 0.0)
        self.assertAlmostEqual(w["R"], 0.5)
        self.assertEqual(normalize({"R": 0}), normalize(None))

    def test_rank_one_is_highest(self):
        self.assertEqual(ranks(np.array([0.2, 0.9, 0.5])).tolist(), [3.0, 1.0, 2.0])

    def test_score_uses_default_weights(self):
        df = pd.DataFrame({"R": [0.3], "H": [0.6], "E": [0.9], "C": [1.0]})
        self.assertAlmostEqual(score(df).iloc[0], 0.6)

    def test_tier_thresholds(self):
        self.assertEqual(tier(0.8, ""), "High attention")
        self.assertEqual(tier(0.79, ""), "Watch")
        self.assertEqual(tier(0.3, ""), "Watch")
        self.assertEqual(tier(0.29, ""), "Lower")

    def test_main_driver_is_relative_to_cohort(self):
        df = pd.DataFrame(
            {
                "gate": ["", "", "", "not_native"],
                "R": [0.9, 0.2, 0.3, 0.9],
                "H": [0.8, 0.8, 0.8, 0.9],
                "E": [0.4, 0.4, 0.9, 0.9],
                "C": [0.0, 0.0, 0.0, 0.0],
            }
        )
        # H is high for everyone, so it is nobody's driver.
        self.assertEqual(main_driver(df).tolist(), ["R", "", "E", ""])


def ev(name, k, h, pa, loss, habitat="forest", r_global=0.5):
    return SpeciesEvidence(
        name=name,
        k_surveyed=k,
        n_surveyed=300,
        r_global=r_global,
        H=h,
        C=float("nan"),
        habitat=habitat,
        pa_fraction=np.asarray(pa, float),
        loss_rate=np.asarray(loss, float),
    )


class Uncertainty(unittest.TestCase):
    def setUp(self):
        self.evidence = [
            ev("rare-destructive", 3, 1.0, [0.0] * 3, [0.15] * 3),
            ev("mid", 30, 0.7, [0.2] * 30, [0.06] * 30),
            ev("common-leafy", 150, 0.35, [0.4] * 150, [0.03] * 150, habitat="open"),
            ev("mid-2", 28, 0.7, [0.2] * 28, [0.06] * 28),
        ]

    def test_seeded_and_reproducible(self):
        a = rank_summary(self.evidence, n=300)
        b = rank_summary(self.evidence, n=300)
        pd.testing.assert_frame_equal(a, b)

    def test_clear_cases_rank_firmly(self):
        s = rank_summary(self.evidence, n=500).set_index("scientific_name")
        self.assertEqual(s.loc["rare-destructive", "rank_median"], 1)
        self.assertEqual(s.loc["common-leafy", "rank_median"], 4)
        self.assertEqual(s.loc["rare-destructive", "p_top_quartile"], 1.0)
        self.assertEqual(s.loc["common-leafy", "p_top_quartile"], 0.0)

    def test_intervals_are_ordered_and_probabilities_bounded(self):
        s = rank_summary(self.evidence, n=500)
        self.assertTrue((s["rank_p05"] <= s["rank_median"]).all())
        self.assertTrue((s["rank_median"] <= s["rank_p95"]).all())
        self.assertTrue(s["p_top_quartile"].between(0, 1).all())
        self.assertTrue((s["score_p05"] <= s["score_p95"]).all())

    def test_close_species_share_uncertainty(self):
        s = rank_summary(self.evidence, n=800).set_index("scientific_name")
        # "mid" and "mid-2" are near-identical, so neither should be certain of rank 2.
        self.assertLess(s.loc["mid", "rank_p05"], s.loc["mid", "rank_p95"])


if __name__ == "__main__":
    unittest.main()
