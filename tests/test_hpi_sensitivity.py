"""HPI weight sensitivity: normalize, ranks, and the Methods chart palette."""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from harvester_risk_atlas.charts import rank_shift_bars
from harvester_risk_atlas.config import HPI_CSV, HPI_WEIGHTS
from harvester_risk_atlas.hpi import (
    hpi_from_components,
    normalize_weights,
    top_rank_movers,
    weight_sensitivity,
)

ROOT = Path(__file__).resolve().parents[1]
RISK_COLORS = {"#9b2226", "#b08968", "#40916c"}


def _toy() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scientific_name": ["HighR", "HighC", "HighH", "HighP"],
            "vernacular_ph": ["a", "b", "c", "d"],
            "component_rarity": [1.0, 0.0, 0.0, 0.0],
            "component_climate": [0.0, 1.0, 0.0, 0.0],
            "component_harvest": [0.0, 0.0, 1.0, 0.0],
            "component_pa_gap": [0.0, 0.0, 0.0, 1.0],
            "iucn_status": ["not_queried"] * 4,
            "iucn_category": [None] * 4,
        }
    )


class NormalizeTests(unittest.TestCase):
    def test_defaults_match_v11_and_sum_to_one(self):
        applied = normalize_weights(HPI_WEIGHTS)
        self.assertEqual(set(applied), set(HPI_WEIGHTS))
        self.assertAlmostEqual(sum(applied.values()), 1.0, places=12)
        for key, value in HPI_WEIGHTS.items():
            self.assertAlmostEqual(applied[key], value, places=12)
        self.assertIsNot(normalize_weights(None), HPI_WEIGHTS)

    def test_negative_and_missing_are_clipped_then_scaled(self):
        applied = normalize_weights(
            {
                "rarity": -1,
                "climate_stress": float("nan"),
                "harvest_proxy": 2,
                "pa_gap": 2,
            }
        )
        self.assertEqual(applied["rarity"], 0.0)
        self.assertEqual(applied["climate_stress"], 0.0)
        self.assertAlmostEqual(applied["harvest_proxy"], 0.5)
        self.assertAlmostEqual(applied["pa_gap"], 0.5)
        self.assertAlmostEqual(sum(applied.values()), 1.0)

    def test_all_zero_falls_back_to_v11(self):
        applied = normalize_weights(
            {"rarity": 0, "climate_stress": 0, "harvest_proxy": 0, "pa_gap": 0}
        )
        for key, value in HPI_WEIGHTS.items():
            self.assertAlmostEqual(applied[key], value, places=12)

    def test_partial_keys_put_mass_on_the_given_component(self):
        applied = normalize_weights({"pa_gap": 3})
        self.assertAlmostEqual(applied["pa_gap"], 1.0)
        self.assertEqual(applied["rarity"], 0.0)


class RankTests(unittest.TestCase):
    def test_v11_scores_and_zero_delta(self):
        frame = _toy()
        sens = weight_sensitivity(frame, HPI_WEIGHTS)
        expected = pd.Series([0.30, 0.25, 0.25, 0.20])
        self.assertTrue(np.allclose(sens["hpi_v11"], expected))
        self.assertTrue((sens["rank_delta"] == 0).all())
        # Tied climate and harvest share rank 2; PA gap is last.
        by_name = sens.set_index("scientific_name")
        self.assertEqual(int(by_name.loc["HighR", "rank_v11"]), 1)
        self.assertEqual(int(by_name.loc["HighC", "rank_v11"]), 2)
        self.assertEqual(int(by_name.loc["HighH", "rank_v11"]), 2)
        self.assertEqual(int(by_name.loc["HighP", "rank_v11"]), 4)

    def test_pa_weight_lifts_the_pa_species(self):
        frame = _toy()
        before_cols = list(frame.columns)
        before_iucn = frame["iucn_status"].copy()
        sens = weight_sensitivity(
            frame,
            {"rarity": 0, "climate_stress": 0, "harvest_proxy": 0, "pa_gap": 1},
        )
        self.assertEqual(list(frame.columns), before_cols)
        pd.testing.assert_series_equal(frame["iucn_status"], before_iucn)
        by_name = sens.set_index("scientific_name")
        self.assertEqual(int(by_name.loc["HighP", "rank_sensitivity"]), 1)
        self.assertEqual(int(by_name.loc["HighP", "rank_delta"]), 3)
        self.assertLess(int(by_name.loc["HighR", "rank_delta"]), 0)
        movers = top_rank_movers(sens, n=2)
        self.assertEqual(movers.iloc[0]["scientific_name"], "HighP")
        self.assertEqual(len(movers), 2)

    def test_shipped_cohort_matches_v11_formula(self):
        df = pd.read_csv(HPI_CSV)
        self.assertEqual(set(df["iucn_status"].dropna().unique()), {"not_queried"})
        sens = weight_sensitivity(df, dict(HPI_WEIGHTS))
        expected = hpi_from_components(df, HPI_WEIGHTS)
        self.assertTrue(np.allclose(sens["hpi_v11"], expected, atol=1e-12))
        self.assertTrue(np.allclose(sens["hpi_v11"], df["hpi"], atol=1e-9))
        self.assertTrue((sens["rank_delta"] == 0).all())
        self.assertTrue(top_rank_movers(sens).empty)
        # Putting all mass on rarity ranks the rarest stored component first.
        rarity_only = weight_sensitivity(df, {"rarity": 1})
        leader = rarity_only.sort_values(
            ["rank_sensitivity", "scientific_name"]
        ).iloc[0]
        max_r = df["component_rarity"].max()
        leaders = set(df.loc[np.isclose(df["component_rarity"], max_r), "scientific_name"])
        self.assertEqual(int(leader["rank_sensitivity"]), 1)
        self.assertIn(leader["scientific_name"], leaders)
        self.assertEqual(set(df["iucn_status"].dropna().unique()), {"not_queried"})


class ChartAndPageTests(unittest.TestCase):
    def test_rank_bars_avoid_risk_colors_and_legend_collision(self):
        sens = weight_sensitivity(
            _toy(),
            {"rarity": 0, "climate_stress": 0, "harvest_proxy": 0, "pa_gap": 1},
        )
        figure = rank_shift_bars(top_rank_movers(sens))
        self.assertIn("Largest rank shifts", figure.layout.title.text)
        self.assertTrue(figure.layout.xaxis.title.text)
        self.assertFalse(figure.layout.showlegend)
        if figure.layout.showlegend:
            self.assertLess(figure.layout.legend.y, 0)
        colors = [str(c).lower() for c in figure.data[0].marker.color]
        self.assertTrue(colors)
        for color in colors:
            self.assertNotIn(color, RISK_COLORS)
        self.assertIn("#2d6a4f", colors)

    def test_methods_copy_stays_on_methods(self):
        app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        methods = (ROOT / "docs" / "METHODS.md").read_text(encoding="utf-8")
        self.assertIn("Weight sensitivity", app)
        self.assertIn("not a new official index", app)
        self.assertIn("Restore v1.1 weights", app)
        self.assertIn(
            '"Map",\n    "Species dossier",\n    "Field brief",\n    "Compare",\n    "Methods"',
            app,
        )
        self.assertNotIn('"Sensitivity"', app)
        idx = app.index("rank_shift_bars(")
        self.assertIn("theme=None", app[idx : idx + 400])
        self.assertIn("## Weight sensitivity", methods)
        self.assertIn("does not replace HPI v1.1", methods)


if __name__ == "__main__":
    unittest.main()
